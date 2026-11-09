"""H5 小游戏的服务端：静态页 + 三个 JSON 接口。纯标准库，零依赖。"""

from __future__ import annotations

import argparse
import json
import os
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from game.core import GameError, draw, odds, rank

WEB_DIR = Path(__file__).resolve().parent.parent / "web"
DRAW_LOG: list[dict[str, Any]] = []  # 抽奖流水，供排行榜聚合
_LOCK = threading.Lock()

CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".png": "image/png",
    ".svg": "image/svg+xml",
}


def reset() -> None:
    with _LOCK:
        DRAW_LOG.clear()


def record(player: str, prize: dict[str, Any]) -> None:
    with _LOCK:
        DRAW_LOG.append({"player": player, "score": prize["points"], "at": time.time()})


def leaderboard(limit: int) -> list[dict[str, Any]]:
    with _LOCK:
        snapshot = list(DRAW_LOG)
    return [{"player": e.player, "score": e.score, "at": e.at} for e in rank(snapshot, limit)]


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "AIGame/1.0"

    def log_message(self, fmt: str, *args: Any) -> None:
        if os.getenv("GAME_DEBUG"):
            super().log_message(fmt, *args)

    # -- 基础工具 ---------------------------------------------------------
    def _json(self, status: int, payload: Any) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _body(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b""
        if not raw:
            return {}
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise GameError("INVALID_JSON", "请求体不是合法 JSON") from exc
        if not isinstance(payload, dict):
            raise GameError("INVALID_JSON", "请求体必须是 JSON 对象")
        return payload

    def _static(self, name: str) -> None:
        target = (WEB_DIR / name).resolve()
        if WEB_DIR not in target.parents or not target.is_file():
            self._json(404, {"code": "NOT_FOUND", "message": f"找不到 {name}"})
            return
        data = target.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", CONTENT_TYPES.get(target.suffix, "application/octet-stream"))
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    # -- 路由 -------------------------------------------------------------
    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path, query = parsed.path, parse_qs(parsed.query)
        try:
            if path == "/health":
                self._json(200, {"status": "ok", "service": "ai-qa-game"})
            elif path == "/api/odds":
                self._json(200, {"items": odds()})
            elif path == "/api/leaderboard":
                limit = int(query.get("limit", ["5"])[0])
                self._json(200, {"items": leaderboard(limit)})
            elif path in ("/", "/index.html"):
                self._static("index.html")
            elif path.startswith("/"):
                self._static(path.lstrip("/"))
            else:
                self._json(404, {"code": "NOT_FOUND", "message": path})
        except GameError as err:
            self._json(400, {"code": err.code, "message": err.message})
        except ValueError as err:
            self._json(400, {"code": "INVALID_QUERY", "message": str(err)})

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        try:
            if path == "/api/draw":
                payload = self._body()
                player = payload.get("player", "guest")
                if not isinstance(player, str) or not player.strip():
                    raise GameError("INVALID_PLAYER", "玩家名不能为空")
                prize = draw(seed=payload.get("seed", 0), index=payload.get("index", 0))
                record(player, prize)
                self._json(200, {"prize": prize, "player": player})
            elif path == "/api/reset":
                reset()
                self._json(200, {"ok": True})
            else:
                self._json(404, {"code": "NOT_FOUND", "message": path})
        except GameError as err:
            self._json(400, {"code": err.code, "message": err.message})


def create_server(port: int = 0) -> ThreadingHTTPServer:
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    server.daemon_threads = True
    return server


def main() -> None:
    parser = argparse.ArgumentParser(description="AI QA Playground · 抽奖小游戏服务")
    parser.add_argument("--port", type=int, default=8100)
    args = parser.parse_args()

    server = create_server(args.port)
    host, port = server.server_address[:2]
    print(f"[game] http://{host}:{port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
