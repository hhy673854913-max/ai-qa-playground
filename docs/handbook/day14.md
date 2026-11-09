# Day 14 · ReAct 循环：自己给智能体加一个工具

> 60 分钟 = 读 25 · 加工具 25 · 跑 10
> 面试问"你用过 Function Calling 吗"，最有力的回答是：**我实现过循环，还给它加过工具**。

## 今天结束时要能做到

1. 画出 `Think → Act → Observe → … → Final` 的循环；
2. 说出三个必须有的工程约束（最大轮数、工具异常兜底、工具要真做事）；
3. 给这个 demo 加第四个工具，并让它出现在 trace 里。

## 1. 读（25 min）

打开 [`ai/react_loop.py`](../../ai/react_loop.py)，按四段读：

### 1.1 工具（44-104 行）

每个工具 = **一个普通函数 + 一份 JSON Schema**。注意 `check_service_health`：

```python
server = create_server(port=0)          # 真的起一个实例
thread = threading.Thread(target=server.serve_forever, daemon=True)
...
with urllib.request.urlopen(f"http://{host}:{port}/health", timeout=3) as resp:
```

**工具必须做实事。** 如果它 `return {"status": "ok"}` 写死，那这个 demo 就只是表演。

### 1.2 执行层（118-126 行）

```python
try:
    return spec["fn"](**args)
except Exception as exc:
    return {"error": f"{type(exc).__name__}: {exc}"}
```

工具抛异常**不能让循环崩**——要变成 Observation 回填给模型，模型才有机会换个方式重试。

### 1.3 离线"模型"（130-182 行）

`ScriptedModel.next()` 用关键词决定下一步。它证明了一件事：
**循环的骨架和模型无关**。换成真模型，只是把"返回什么"改成"解析 `tool_calls`"。

### 1.4 循环本体（215-264 行）

```python
for turn in range(1, MAX_STEPS + 1):
    decision = model.next(question, transcript)
    if decision["type"] == "final":
        print(f"[Turn {turn}] Final Answer: {decision['content']}")
        return
```

`MAX_STEPS = 6` 是硬性终止条件：**没有它，模型会一直调工具**（真实项目里这叫"死循环烧钱"）。

## 2. 加一个工具（25 min）

新工具：算"单次抽奖的期望得分"（纯计算，不依赖服务）。

### 2.1 实现（8 min）

在 `check_service_health` 后面加：

```python
def expected_points() -> dict[str, Any]:
    """按当前奖池算期望得分：Σ(权重/总权重 × 分数)。"""
    from game.core import PRIZES

    total = sum(prize["weight"] for prize in PRIZES)
    ev = sum(prize["weight"] / total * prize["points"] for prize in PRIZES)
    return {"expected_points": round(ev, 2), "total_weight": total}
```

> 为什么不用 `odds()`：它只返回 `id/name/weight/probability`，没有 `points`
> （Day 02 读过它的返回结构）。工具要用的字段得自己去 `PRIZES` 拿——
> 这类"字段对不上"的错，正是 `except` 兜底把 `KeyError` 变成 Observation 之后才会被你看出来的。

### 2.2 注册（7 min）

在 `TOOLS` 字典里加一项（schema 就是模型唯一的"行动空间"）：

```python
"expected_points": {
    "fn": expected_points,
    "description": "计算单次抽奖的期望得分（按当前奖池的概率与分数加权）",
    "parameters": {"type": "object", "properties": {}, "required": []},
},
```

再在 `SYSTEM_PROMPT` 的工具列表里补上名字。

### 2.3 让离线模型会用它（10 min）

在 `ScriptedModel.next()` 的 `return {"type": "final", ...}` **之前**插一段：

```python
if ("期望" in question or "平均" in question) and "expected_points" not in self.called:
    return {
        "type": "tool",
        "name": "expected_points",
        "args": {},
        "thought": "用户在问平均收益。先按奖池算期望，不靠心算。",
    }
```

并在 `summarize()` 里补一个分支：

```python
elif name == "expected_points":
    parts.append(f"单次抽奖期望得分 {obs['expected_points']}")
```

## 3. 跑（10 min）

```powershell
python ai/react_loop.py "抽一次的期望得分是多少？"
```

期望 trace 变成 2 轮（`expected_points` 一次 + Final），最后一句包含期望值。
手算校验：`(1000×1 + 300×4 + 50×15 + 10×80) / 100 = (1000 + 1200 + 750 + 800) / 100 = 37.5`。

**对得上，说明工具真的在算，不是在编。**

## 4. 记

progress.md：`Day 14 | ✅ | 加了 expected_points 工具，trace 2 轮到 Final，手算 37.5 对得上`

## 验收清单

- [ ] 能画出循环图（4 个箭头）
- [ ] 新工具出现在 trace 的 Action 里
- [ ] 输出里的期望值和手算一致
- [ ] 能说出 `MAX_STEPS` 不设会怎样

## 面试口径

> 我写过一个最小 ReAct 循环：工具是普通函数 + JSON Schema，模型每轮输出"调工具"或"给答案"，
> 执行结果回填成 Observation，`MAX_STEPS=6` 兜住死循环。
> 有两个工程细节我踩过：工具异常必须转成 Observation 而不是让进程崩；
> 工具必须做实事——所以我那个健康检查工具是真的起了一个服务实例去请求 `/health`。
> 后来我给它加了个"期望收益"工具，手算 37.5 和输出对上了，才敢说它没在编。

## 卡住了怎么办

| 现象 | 原因 | 处理 |
| --- | --- | --- |
| trace 只有 1 轮 Final | 关键词没匹配 | 问题里带"期望"，或改 `next()` 的条件 |
| `KeyError: 'expected_points'` | `summarize` 分支没加 | 补 `elif name == "expected_points"` |
| 期望值算错 | `odds()` 没有 `points` 字段 | 直接遍历 `PRIZES`，用 `weight / total` |
| 导入报错 | 不在仓库根目录跑 | `cd ai-qa-playground` 后再执行 |

