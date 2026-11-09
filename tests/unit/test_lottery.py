"""抽奖逻辑的参数化单测。

练的就是「case 设计手感」：把一条规则拆成
  * 不变式（换成任何 seed 都成立）
  * 边界（0 / 1 / 最大值 / 非法类型）
  * 统计（权重是否真的生效，用固定 seed 跑大样本，结果确定、不会 flaky）
"""

from __future__ import annotations

import pytest

from game.core import PRIZES, GameError, draw, odds, total_weight

pytestmark = pytest.mark.unit


# ------------------------------------------------------------------ 不变式
def test_same_seed_and_index_is_reproducible() -> None:
    """同一个 (seed, index) 必须永远得到同一个奖品 —— 这是 E2E 能断言具体奖品的前提。"""
    first = draw(seed=7, index=0)
    second = draw(seed=7, index=0)
    assert first == second


def test_index_advances_the_sequence() -> None:
    """连续抽奖不能总是同一个奖品：前 20 抽里至少出现 2 种。"""
    prizes = {draw(seed=7, index=i)["id"] for i in range(20)}
    assert len(prizes) >= 2


def test_draw_returns_prize_from_pool() -> None:
    for index in range(50):
        prize = draw(seed=1234, index=index)
        assert prize["id"] in {p["id"] for p in PRIZES}
        assert isinstance(prize["points"], int)
        assert 0 <= prize["roll"] < total_weight()


# ------------------------------------------------------------------ 统计：权重是否真的生效
def test_weight_distribution_matches_config() -> None:
    """固定 seed 跑 20000 次，各奖品占比应贴合配置权重（误差 < 0.5 个百分点）。

    因为随机源由 sha256(seed:index) 决定，样本是「确定的」，
    所以这条统计用例不会因为运气不好而偶发失败。
    """
    runs = 20_000
    counts = {prize["id"]: 0 for prize in PRIZES}
    for index in range(runs):
        counts[draw(seed=42, index=index)["id"]] += 1

    for prize in PRIZES:
        expected = prize["weight"] / total_weight() * 100
        actual = counts[prize["id"]] / runs * 100
        assert abs(actual - expected) < 0.5, f"{prize['id']} 期望 {expected:.2f}%，实际 {actual:.2f}%"


def test_odds_sum_to_100() -> None:
    assert pytest.approx(sum(item["probability"] for item in odds()), abs=0.01) == 100.0


# ------------------------------------------------------------------ 自定义奖池
def test_single_prize_pool_always_wins() -> None:
    pool = [{"id": "only", "name": "唯一奖", "weight": 1, "points": 5}]
    for index in range(10):
        assert draw(seed=1, index=index, pool=pool)["id"] == "only"


def test_zero_weight_prize_is_impossible() -> None:
    """权重 0 的奖品永远不该出现 —— 但当前实现把它当非法配置直接拒绝，这里锁住这个约定。"""
    pool = [
        {"id": "real", "name": "真奖", "weight": 10, "points": 1},
        {"id": "ghost", "name": "幽灵奖", "weight": 0, "points": 0},
    ]
    with pytest.raises(GameError) as err:
        draw(seed=1, index=0, pool=pool)
    assert err.value.code == "INVALID_WEIGHT"


# ------------------------------------------------------------------ 非法输入
@pytest.mark.parametrize(
    ("pool", "code"),
    [
        pytest.param([], "EMPTY_POOL", id="空奖池"),
        pytest.param([{"id": "a", "name": "A", "weight": -1, "points": 1}], "INVALID_WEIGHT", id="权重为负"),
        pytest.param([{"id": "a", "name": "A", "weight": 1.5, "points": 1}], "INVALID_WEIGHT", id="权重是小数"),
        pytest.param([{"id": "a", "name": "A", "weight": True, "points": 1}], "INVALID_WEIGHT", id="权重是布尔"),
        pytest.param([{"id": "a", "name": "A", "weight": 1, "points": -1}], "INVALID_POINTS", id="积分为负"),
        pytest.param([{"id": "a", "name": "", "weight": 1, "points": 1}], "INVALID_POOL", id="奖品名为空"),
        pytest.param(
            [{"id": "a", "name": "A", "weight": 1, "points": 1}, {"id": "a", "name": "A2", "weight": 1, "points": 2}],
            "DUPLICATE_PRIZE",
            id="奖品 id 重复",
        ),
    ],
)
def test_invalid_pool_is_rejected(pool, code: str) -> None:
    with pytest.raises(GameError) as err:
        draw(seed=0, index=0, pool=pool)
    assert err.value.code == code


@pytest.mark.parametrize(
    ("kwargs", "code"),
    [
        pytest.param({"seed": 1.5, "index": 0}, "INVALID_SEED", id="seed 是小数"),
        pytest.param({"seed": True, "index": 0}, "INVALID_SEED", id="seed 是布尔"),
        pytest.param({"seed": 1, "index": -1}, "INVALID_INDEX", id="index 为负"),
        pytest.param({"seed": 1, "index": "3"}, "INVALID_INDEX", id="index 是字符串"),
    ],
)
def test_invalid_seed_or_index_is_rejected(kwargs, code: str) -> None:
    with pytest.raises(GameError) as err:
        draw(**kwargs)
    assert err.value.code == code


def test_negative_seed_is_allowed_and_stable() -> None:
    """负 seed 只是哈希输入，不是非法值；关键仍是「可复现」。"""
    assert draw(seed=-1, index=0) == draw(seed=-1, index=0)
