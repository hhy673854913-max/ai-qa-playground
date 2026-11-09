"""排行榜排序的参数化单测。

排序规则看着简单，实际是 bug 高发区：同分怎么排？同一玩家抽多次算哪次？
limit 越界怎么办？这些都要写死在用例里，否则每次改动都得靠人肉回忆。
"""

from __future__ import annotations

import pytest

from game.core import Entry, GameError, rank

pytestmark = pytest.mark.unit


def names(entries: list[Entry]) -> list[str]:
    return [entry.player for entry in entries]


# ------------------------------------------------------------------ 基本排序
def test_sorted_by_score_desc() -> None:
    entries = [
        {"player": "alice", "score": 50, "at": 3.0},
        {"player": "bob", "score": 300, "at": 1.0},
        {"player": "carol", "score": 10, "at": 2.0},
    ]
    assert names(rank(entries)) == ["bob", "alice", "carol"]


def test_tie_goes_to_earlier_player() -> None:
    """同分时先达成的排前面 —— 这是产品的规则，不是实现细节。"""
    entries = [
        {"player": "late", "score": 300, "at": 20.0},
        {"player": "early", "score": 300, "at": 10.0},
    ]
    assert names(rank(entries)) == ["early", "late"]


def test_full_tie_is_stable_by_name() -> None:
    """分数、时间都相同，按名字升序兜底，保证结果可复现（避免数据库返回顺序影响断言）。"""
    entries = [
        {"player": "zed", "score": 10, "at": 1.0},
        {"player": "amy", "score": 10, "at": 1.0},
    ]
    assert names(rank(entries)) == ["amy", "zed"]


# ------------------------------------------------------------------ 聚合：一人一条
def test_same_player_keeps_best_score() -> None:
    entries = [
        {"player": "alice", "score": 50, "at": 1.0},
        {"player": "alice", "score": 300, "at": 5.0},
        {"player": "bob", "score": 100, "at": 2.0},
    ]
    result = rank(entries)
    assert names(result) == ["alice", "bob"]
    assert result[0].score == 300


def test_same_player_keeps_earliest_time_for_equal_score() -> None:
    entries = [
        {"player": "alice", "score": 300, "at": 9.0},
        {"player": "alice", "score": 300, "at": 3.0},
    ]
    assert rank(entries)[0].at == 3.0


# ------------------------------------------------------------------ 边界
@pytest.mark.parametrize(
    ("entries", "limit", "expected"),
    [
        pytest.param([], 5, [], id="空榜单"),
        pytest.param([{"player": "a", "score": 1, "at": 1.0}], 5, ["a"], id="少于-limit"),
        pytest.param([{"player": "a", "score": 1, "at": 1.0}, {"player": "b", "score": 2, "at": 2.0}], 1, ["b"], id="limit-截断"),
        pytest.param([{"player": "a", "score": 0, "at": 1.0}], 3, ["a"], id="分数为-0"),
    ],
)
def test_limit_and_boundaries(entries, limit: int, expected: list[str]) -> None:
    assert names(rank(entries, limit)) == expected


def test_accepts_entry_objects() -> None:
    """既接受 dict（来自接口），也接受 Entry（来自内部调用），减少调用方转换成本。"""
    entries = [Entry("alice", 10, 1.0), Entry("bob", 20, 2.0)]
    assert names(rank(entries)) == ["bob", "alice"]


# ------------------------------------------------------------------ 非法输入
@pytest.mark.parametrize(
    ("entries", "code"),
    [
        pytest.param([{"player": "", "score": 1, "at": 1.0}], "INVALID_PLAYER", id="玩家名为空"),
        pytest.param([{"player": "   ", "score": 1, "at": 1.0}], "INVALID_PLAYER", id="玩家名全空格"),
        pytest.param([{"player": "a", "score": -1, "at": 1.0}], "INVALID_SCORE", id="分数为负"),
        pytest.param([{"player": "a", "score": 1.5, "at": 1.0}], "INVALID_SCORE", id="分数是小数"),
        pytest.param([{"player": "a", "score": True, "at": 1.0}], "INVALID_SCORE", id="分数是布尔"),
        pytest.param([{"player": "a", "score": 1, "at": "yesterday"}], "INVALID_TIMESTAMP", id="时间戳是字符串"),
        pytest.param(["not-a-record"], "INVALID_ENTRY", id="记录类型错误"),
    ],
)
def test_invalid_entries_are_rejected(entries, code: str) -> None:
    with pytest.raises(GameError) as err:
        rank(entries)
    assert err.value.code == code


@pytest.mark.parametrize("limit", [0, -1, 1.5, True])
def test_invalid_limit_is_rejected(limit) -> None:
    with pytest.raises(GameError) as err:
        rank([], limit)
    assert err.value.code == "INVALID_LIMIT"
