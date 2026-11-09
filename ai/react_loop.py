#!/usr/bin/env python3
"""最小 ReAct / Function Calling 循环（去掉注释约 60 行）。

面试里被问「你用过 Function Calling 吗」，最有说服力的回答不是名词解释，而是：
**「模型输出结构化指令 → 运行时执行 → 结果回填，然后继续循环」**，再补一句「我自己写过这个循环」。

这个 demo 就是这个循环本体：
  1. 定义两个（三个）工具，普通 Python 函数 + 一份 JSON Schema；
  2. 让"模型"每轮产出一个决定：要么调工具（名称 + 参数），要么给最终答案；
  3. 运行时执行工具，把 Observation 回填进上下文；
  4. 循环直到 final 或达到最大轮数（终止条件必须有，否则模型会无限调工具）。

两种跑法：
  python ai/react_loop.py                      # 离线：用脚本化"模型"演示循环机制
  python ai/react_loop.py --real "问题"        # 真实：OpenAI 兼容接口 + tools 参数

为什么默认离线？因为想验证的是"循环"本身，而不是网络。没有 API Key 也能看到每一轮的
Thought / Action / Observation —— 这才是"有手感"的证据。
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import threading
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

MAX_STEPS = 6  # 硬性终止条件：没有它，模型可能一直调工具

SYSTEM_PROMPT = (
    "你是一个测试助手。可用工具：get_lottery_odds、check_service_health、read_smoke_report。"
    "需要事实时先调工具，不要凭记忆回答。拿到足够信息后用中文给出最终答案。"
)


# ---------------------------------------------------------------- 1. 工具实现
def get_lottery_odds() -> dict[str, Any]:
    """读取奖池配置与中奖概率（真实项目里可能查 DB / 配置中心）。"""
    from game.core import odds

    return {"items": odds()}


def check_service_health() -> dict[str, Any]:
    """真的起一个服务实例并请求 /health —— 工具应该做实事，而不是返回写死的 ok。"""
    from game.server import create_server

    server = create_server(port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address[:2]
    try:
        with urllib.request.urlopen(f"http://{host}:{port}/health", timeout=3) as resp:
            return {"status": "ok", "http_status": resp.status, "body": json.loads(resp.read())}
    except OSError as exc:
        return {"status": "down", "error": str(exc)}
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)


def read_smoke_report(junit_path: str = "reports/junit.xml") -> dict[str, Any]:
    """读取最近一次 pytest 的 junit 结果（CI 里由 pytest --junitxml 产出）。"""
    import xml.etree.ElementTree as ET

    path = ROOT / junit_path
    if not path.exists():
        return {"status": "missing", "path": str(path), "summary": "还没有测试报告，先跑一次 pytest --junitxml=reports/junit.xml"}
    root = ET.parse(path).getroot()
    suites = [root] if root.tag == "testsuite" else list(root)
    total = sum(int(s.get("tests") or 0) for s in suites)
    failures = sum(int(s.get("failures") or 0) + int(s.get("errors") or 0) for s in suites)
    return {"status": "ok", "total": total, "failed": failures, "summary": f"{total} 条用例，{failures} 条失败"}


TOOLS: dict[str, dict[str, Any]] = {
    "get_lottery_odds": {
        "fn": get_lottery_odds,
        "description": "查询抽奖奖池里每个奖品的中奖概率，返回 id/name/weight/probability",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
    "check_service_health": {
        "fn": check_service_health,
        "description": "检查抽奖服务是否可访问（起本地实例并请求 /health）",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
    "read_smoke_report": {
        "fn": read_smoke_report,
        "description": "读取最近一次 pytest junit 报告的用例总数与失败数",
        "parameters": {
            "type": "object",
            "properties": {"junit_path": {"type": "string", "description": "junit.xml 的相对路径"}},
            "required": [],
        },
    },
}


def tool_schemas() -> list[dict[str, Any]]:
    """转成 OpenAI tools 格式。名字和参数就是模型唯一的"行动空间"。"""
    return [
        {
            "type": "function",
            "function": {"name": name, "description": spec["description"], "parameters": spec["parameters"]},
        }
        for name, spec in TOOLS.items()
    ]


def execute(name: str, args: dict[str, Any]) -> dict[str, Any]:
    """执行工具。异常必须变成 Observation 返回给模型，而不是让循环崩掉。"""
    spec = TOOLS.get(name)
    if spec is None:
        return {"error": f"未知工具: {name}"}
    try:
        return spec["fn"](**args)
    except Exception as exc:  # noqa: BLE001 - 这里就是要兜住一切，让模型看到错误
        return {"error": f"{type(exc).__name__}: {exc}"}


# ---------------------------------------------------------------- 2. 离线"模型"
class ScriptedModel:
    """离线替身：按关键词决定下一步，用来演示 while 循环本身。

    它证明了一件事：**循环的骨架和模型无关**。
    换成真模型，只需要把「这里返回什么」改成「解析 API 返回的 tool_calls」。
    """

    def __init__(self) -> None:
        self.called: set[str] = set()

    def next(self, question: str, transcript: list[dict[str, Any]]) -> dict[str, Any]:
        if "概率" in question and "get_lottery_odds" not in self.called:
            return {
                "type": "tool",
                "name": "get_lottery_odds",
                "args": {},
                "thought": "用户在问中奖概率。这是事实型问题，先查奖池配置，不靠记忆编。",
            }
        if ("健康" in question or "服务" in question) and "check_service_health" not in self.called:
            return {
                "type": "tool",
                "name": "check_service_health",
                "args": {},
                "thought": "用户关心服务可用性，调健康检查工具拿真实状态。",
            }
        if ("报告" in question or "用例" in question) and "read_smoke_report" not in self.called:
            return {
                "type": "tool",
                "name": "read_smoke_report",
                "args": {"junit_path": "reports/junit.xml"},
                "thought": "用户想看测试结果，先读 junit 报告。",
            }
        return {"type": "final", "content": self.summarize(transcript)}

    @staticmethod
    def summarize(transcript: list[dict[str, Any]]) -> str:
        if not transcript:
            return "没有需要查询的信息，直接回答：这是 ai-qa-playground 的抽奖小游戏。"

        parts: list[str] = []
        for step in transcript:
            obs = step["observation"]
            name = step["name"]
            if name == "get_lottery_odds" and "items" in obs:
                odds_text = "，".join(f"{item['name']} {item['probability']}%" for item in obs["items"])
                parts.append(f"奖池概率为：{odds_text}（合计 100%）")
            elif name == "check_service_health":
                parts.append(f"服务健康检查结果：{obs.get('status')}")
            elif name == "read_smoke_report":
                parts.append(f"最近测试报告：{obs.get('summary')}")
            elif "error" in obs:
                parts.append(f"工具 {name} 报错：{obs['error']}")
        return "；".join(parts) + "。"


# ---------------------------------------------------------------- 3. 真实模型（可选）
class OpenAIModel:
    """OpenAI 兼容接口的最小客户端：只依赖标准库。改 base_url 就能接 DeepSeek / Qwen / 本地 vLLM。"""

    def __init__(self) -> None:
        self.api_key = os.environ.get("OPENAI_API_KEY", "")
        if not self.api_key:
            raise SystemExit("--real 模式需要环境变量 OPENAI_API_KEY（可用 OPENAI_BASE_URL 指向兼容网关）")
        self.base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
        self.model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

    def chat(self, messages: list[dict[str, Any]]) -> dict[str, Any]:
        payload = {
            "model": self.model,
            "messages": messages,
            "tools": tool_schemas(),
            "tool_choice": "auto",
            "temperature": 0,
        }
        request = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))


# ---------------------------------------------------------------- 4. 循环本体
def run(question: str, real: bool = False) -> None:
    print(f"用户：{question}\n")

    if not real:
        model = ScriptedModel()
        transcript: list[dict[str, Any]] = []
        for turn in range(1, MAX_STEPS + 1):
            decision = model.next(question, transcript)
            if decision["type"] == "final":
                print(f"[Turn {turn}] Final Answer: {decision['content']}")
                return
            name, args = decision["name"], decision["args"]
            model.called.add(name)
            print(f"[Turn {turn}] Thought: {decision['thought']}")
            print(f"          Action: {name}({json.dumps(args, ensure_ascii=False)})")
            observation = execute(name, args)
            print(f"          Observation: {json.dumps(observation, ensure_ascii=False)[:300]}\n")
            transcript.append({"name": name, "args": args, "observation": observation})
        print(f"[warn] 达到最大轮数 {MAX_STEPS}，强制结束（生产里应记录告警）")
        return

    # 真实模型：消息历史里要保留 assistant 的 tool_calls 和每条 tool 结果
    client = OpenAIModel()
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]
    for turn in range(1, MAX_STEPS + 1):
        data = client.chat(messages)
        message = data["choices"][0]["message"]
        calls = message.get("tool_calls") or []
        thought = (message.get("content") or "").strip()
        if thought:
            print(f"[Turn {turn}] Thought: {thought}")
        if not calls:
            print(f"[Turn {turn}] Final Answer: {message.get('content')}")
            return

        messages.append({"role": "assistant", "content": message.get("content") or "", "tool_calls": calls})
        for call in calls:
            name = call["function"]["name"]
            try:
                args = json.loads(call["function"].get("arguments") or "{}")
            except json.JSONDecodeError:
                args = {}
            print(f"          Action: {name}({json.dumps(args, ensure_ascii=False)})")
            observation = execute(name, args)
            print(f"          Observation: {json.dumps(observation, ensure_ascii=False)[:300]}\n")
            messages.append({"role": "tool", "tool_call_id": call["id"], "content": json.dumps(observation, ensure_ascii=False)})
    print(f"[warn] 达到最大轮数 {MAX_STEPS}，强制结束")


def main() -> None:
    parser = argparse.ArgumentParser(description="最小 ReAct / Function Calling 循环")
    parser.add_argument("question", nargs="?", default="抽奖概率是多少？服务现在健康吗？")
    parser.add_argument("--real", action="store_true", help="使用真实模型（需要 OPENAI_API_KEY）")
    args = parser.parse_args()
    run(args.question, real=args.real)


if __name__ == "__main__":
    main()
