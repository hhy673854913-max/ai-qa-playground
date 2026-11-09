"""抽奖与排行榜的纯逻辑。

刻意做到「三不沾」：不碰 HTTP、不碰 DOM、不碰数据库。
好处是 pytest 可以直接 import 进来跑参数化单测，不用起服务、不用开浏览器，
几百条边界用例跑完不到一秒 —— 这是测试金字塔的塔基。
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any, Iterable

# 奖池：weight 是相对权重（总和 100），points 是排行榜分数
PRIZES: tuple[dict[str, Any], ...] = (
    {"id": "legendary", "name": "限量手办", "weight": 1, "points": 1000},
    {"id": "epic", "name": "机械键盘", "weight": 4, "points": 300},
    {"id": "rare", "name": "定制鼠标垫", "weight": 15, "points": 50},
    {"id": "common", "name": "再来一次", "weight": 80, "points": 10},
)


class GameError(ValueError):
    """业务校验失败。server 层把它翻译成 400 + 错误码。"""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


def _validate_pool(pool: Iterable[dict[str, Any]]) -> tuple[dict[str, Any], ...]:
    pool = tuple(pool)
    if not pool:
        raise GameError("EMPTY_POOL", "奖池不能为空")

    seen: set[str] = set()
    for prize in pool:
        for key in ("id", "name"):
            if not isinstance(prize.get(key), str) or not prize[key].strip():
                raise GameError("INVALID_POOL", f"奖品缺少合法的 {key}")
        if prize["id"] in seen:
            raise GameError("DUPLICATE_PRIZE", f"奖品 id 重复: {prize['id']}")
        seen.add(prize["id"])

        weight = prize.get("weight")
        if not isinstance(weight, int) or isinstance(weight, bool) or weight <= 0:
            raise GameError("INVALID_WEIGHT", f"{prize['id']} 的权重必须是正整数")

        points = prize.get("points")
        if not isinstance(points, int) or isinstance(points, bool) or points < 0:
            raise GameError("INVALID_POINTS", f"{prize['id']} 的积分必须是非负整数")
    return pool


def _resolve_pool(pool: Iterable[dict[str, Any]] | None) -> tuple[dict[str, Any], ...]:
    """注意用 is None 而不是 `pool or PRIZES`：空奖池必须报错，不能悄悄回退成默认奖池。"""
    return _validate_pool(PRIZES if pool is None else pool)


def total_weight(pool: Iterable[dict[str, Any]] | None = None) -> int:
    return sum(prize["weight"] for prize in _resolve_pool(pool))


def draw(seed: int = 0, index: int = 0, pool: Iterable[dict[str, Any]] | None = None) -> dict[str, Any]:
    """按权重抽一次奖。

    为什么用 sha256(seed:index) 而不是 random 模块？
      1. 可复现：同样的 seed+index 永远得到同样的奖品，E2E 才能在 UI 上断言具体奖品，
         而不是只断言「中了某一个」这种空话。
      2. 无状态：服务重启、并发请求都不会改变结果，测试不用关心随机源被谁消费过。
      3. 与 Python 版本解耦：不依赖 random 模块内部实现的稳定性。

    seed 允许为负（字符串拼进哈希即可），只要求是整数；index 必须非负。
    """
    if not isinstance(seed, int) or isinstance(seed, bool):
        raise GameError("INVALID_SEED", "seed 必须是整数")
    if not isinstance(index, int) or isinstance(index, bool) or index < 0:
        raise GameError("INVALID_INDEX", "index 必须是非负整数")

    pool = _resolve_pool(pool)
    total = sum(prize["weight"] for prize in pool)

    digest = hashlib.sha256(f"{seed}:{index}".encode("utf-8")).digest()
    roll = int.from_bytes(digest[:8], "big") % total  # 落在 [0, total) 的均匀整数

    cursor = 0
    for prize in pool:
        cursor += prize["weight"]
        if roll < cursor:
            return {**prize, "roll": roll}
    raise AssertionError("unreachable")  # 权重累加一定覆盖 [0, total)


def odds(pool: Iterable[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    """返回每个奖品的中奖概率（百分比，保留 4 位小数），用于接口和测试。"""
    pool = _resolve_pool(pool)
    total = sum(prize["weight"] for prize in pool)
    return [
        {"id": prize["id"], "name": prize["name"], "weight": prize["weight"], "probability": round(prize["weight"] / total * 100, 4)}
        for prize in pool
    ]


# ---------------------------------------------------------------- 排行榜


@dataclass(frozen=True)
class Entry:
    player: str
    score: int
    at: float  #  Unix 时间戳（秒），同分时越早越靠前


def _coerce(raw: Any) -> Entry:
    if isinstance(raw, Entry):
        entry = raw
    elif isinstance(raw, dict):
        entry = Entry(player=raw.get("player"), score=raw.get("score"), at=raw.get("at"))
    else:
        raise GameError("INVALID_ENTRY", "排行榜记录必须是 Entry 或 dict")

    if not isinstance(entry.player, str) or not entry.player.strip():
        raise GameError("INVALID_PLAYER", "玩家名不能为空")
    if not isinstance(entry.score, int) or isinstance(entry.score, bool) or entry.score < 0:
        raise GameError("INVALID_SCORE", "分数必须是非负整数")
    if not isinstance(entry.at, (int, float)) or isinstance(entry.at, bool):
        raise GameError("INVALID_TIMESTAMP", "时间戳必须是数字")
    return Entry(entry.player.strip(), entry.score, float(entry.at))


def rank(entries: Iterable[Any], limit: int = 10) -> list[Entry]:
    """排序规则：分数降序 → 同分按时间升序（先到先得）→ 再按名字升序（保证结果稳定）。

    另外做了「同一玩家只保留最好成绩」的聚合，避免一个人刷满榜单。
    """
    if not isinstance(limit, int) or isinstance(limit, bool) or limit < 1:
        raise GameError("INVALID_LIMIT", "limit 必须是正整数")

    best: dict[str, Entry] = {}
    for raw in entries:
        entry = _coerce(raw)
        current = best.get(entry.player)
        # 分数更高，或同分但更早达成 → 替换
        if current is None or (entry.score, -entry.at) > (current.score, -current.at):
            best[entry.player] = entry

    ordered = sorted(best.values(), key=lambda e: (-e.score, e.at, e.player))
    return ordered[:limit]
