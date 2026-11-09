# Day 05 · 用例设计：不变式、边界、统计，以及"找覆盖缺口"

> 60 分钟 = 读 15 · 找缺口 15 · 写 3 条 25 · 记 5
> 今天开始"写"而不是"读"。判断标准只有一个：**新用例能不能失败**。

## 今天结束时要能做到

1. 把一条业务规则翻译成 1~3 条可执行断言；
2. 分清"参数化表"和"整体不变式"两种写法；
3. 自己找出一处没有测试覆盖的地方，并补上。

## 1. 读（15 min）

通读 [`tests/unit/test_lottery.py`](../../tests/unit/test_lottery.py)，把每条用例归类：

| 类型 | 例子 | 特点 |
| --- | --- | --- |
| 不变式 | `test_odds_sum_to_100` | 换任何输入都成立，一条断言覆盖全表 |
| 可复现 | `test_same_seed_and_index_is_reproducible` | 守住"确定性"这个设计承诺 |
| 统计 | `test_weight_distribution_matches_config` | 用大样本验权重，固定 seed 所以不 flaky |
| 边界 | `test_single_prize_pool_always_wins` | 池子最小、最大、刚好不满足 |
| 非法 | `test_invalid_pool_is_rejected` | 输入类型/取值错误 → 明确错误码 |

记住这个分类，**评审用例时先问"它属于哪一类"** —— 缺哪类就补哪类，比盲目加数量有效。

## 2. 找缺口（15 min）

对着 [`game/core.py`](../../game/core.py) 的公开函数列表，逐个问"它被直接测过吗"：

| 函数 | 状态 |
| --- | --- |
| `draw` | ✅ 被大量覆盖 |
| `odds` | ⚠️ 只测了默认池 |
| `total_weight` | ❌ **没有任何直接测试** |
| `rank` | ✅ 覆盖较好，但 `limit` 默认值（10）没测过 |

**结论：至少有两处缺口。** 今天的任务就是把它们补上。

## 3. 写 3 条（25 min）

新建 `tests/unit/test_gaps.py`（自己写，不要抄）：

```python
"""Day 05 练习：补覆盖缺口。"""
from __future__ import annotations

import pytest

from game.core import PRIZES, draw, odds, rank, total_weight

pytestmark = pytest.mark.unit


def test_total_weight_matches_prize_config() -> None:
    # 1) 默认奖池：权重合计应该等于 PRIZES 里各 weight 之和
    ...


def test_total_weight_of_custom_pool() -> None:
    # 2) 自定义奖池：两个权重 7 + 13，合计应该是 20
    ...


@pytest.mark.parametrize(
    ("entries", "expected_len"),
    [
        pytest.param([{"player": f"p{i}", "score": i, "at": float(i)} for i in range(11)], 10, id="默认-limit-截断到-10"),
        pytest.param([{"player": f"p{i}", "score": i, "at": float(i)} for i in range(3)], 3, id="不足-limit-时全返回"),
    ],
)
def test_rank_default_limit(entries, expected_len: int) -> None:
    # 3) rank 的默认 limit 是 10，这条以前没人测
    ...
```

要求：

- 三条都要能在**不改业务代码**的前提下通过；
- 每条断言失败时，报错信息里能看出"期望 vs 实际"（用 `assert x == y, "说明"`）；
- 跑 `python -m pytest -q`，总数从 41 变成 44。

### 加练（写完后做，5 min）

挑其中一条，**故意让业务代码出错**（例如把 `total_weight` 的 `sum` 改成 `max`），
确认只有你写的那条变红。然后 `git checkout -- game/core.py` 修回。

## 4. 记（5 min）

progress.md：`Day 05 | ✅ | 补了 total_weight 与 limit 默认值 3 条用例；故意改 sum→max 验证能红`

## 验收清单

- [ ] `test_gaps.py` 三条用例全部通过
- [ ] 总数 44（41 + 3）
- [ ] 至少一条被你"改坏业务 → 变红 → 修回"
- [ ] 能说出你的用例属于上文哪一类

## 面试口径

> 我补用例不按"数量"，按"类型"：不变式、可复现、统计、边界、非法输入。
> 评审时先看缺哪类。比如这个仓库里 `total_weight` 和 `rank` 的默认 limit 就没被测过——
> 这类"公共函数没人测"的缺口，比多写十条正常路径有价值。

## 卡住了怎么办

| 现象 | 处理 |
| --- | --- |
| import 报错 | 从仓库根目录跑；`pytest.ini` 里 `pythonpath = .` 已配好 |
| 改坏后不止一条红 | 你删的是被复用的逻辑，换个更局部的改动（如 `limit=10` → `limit=1`） |
| 忘记改回来 | `git status` 看 `game/core.py`，`git checkout -- game/core.py` |
