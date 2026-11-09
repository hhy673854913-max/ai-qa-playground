# Day 04 · pytest：参数化表、标记、选择器

> 60 分钟 = 读 20 · 练 30 · 记 10
> 今天不追求"写很多用例"，而是学会用**最少的代码组织最多的场景**。

## 今天结束时要能做到

1. 读懂 `@pytest.mark.parametrize` 的三段结构（参数名 / 数据表 / 用例体）；
2. 用 `-k`、`--lf`、`--collect-only` 精确控制跑哪些用例；
3. 自己往表里加一行，并让它先红后绿。

## 1. 读（20 min）

打开 [`tests/unit/test_lottery.py`](../../tests/unit/test_lottery.py)，重点看 81-100 行：

```python
@pytest.mark.parametrize(
    ("pool", "code"),
    [
        pytest.param([], "EMPTY_POOL", id="空奖池"),
        pytest.param([{"id": "a", "name": "A", "weight": -1, "points": 1}], "INVALID_WEIGHT", id="权重为负"),
        ...
    ],
)
def test_invalid_pool_is_rejected(pool, code: str) -> None:
```

注意三件事：

1. **`id=` 是给人看的**。`pytest -v` 时显示 `test_invalid_pool_is_rejected[空奖池]`，
   比 `[case3]` 有用一百倍；CI 里失败时也靠它定位。
2. **一个函数 = 一张表**。10 个输入组合只写 1 个断言体，加场景就加一行。
3. **断言体只做一件事**：`pytest.raises` + 检查 `code`。不要在这里写业务判断。

再看 55-60 行的统计测试：它没有参数化，因为它是**一条断言跑全表**（概率合计 100）。
参数化不是万能，选"表"还是"循环"看场景：**要独立报告失败 → 用参数化；只是校验整体不变式 → 用循环**。

## 2. 练（30 min）

### 2.1 三个开关（10 min）

```powershell
python -m pytest --collect-only -q        # 只列用例，不执行（末尾会显示 40 tests collected）
python -m pytest -k "invalid_pool" -v     # 只跑名字匹配的
python -m pytest -q --lf                  # 只跑上次失败的（第一次会退化成全量）
```

观察：`--collect-only` 输出的 `[...]` 部分就是你的 `id`。

### 2.2 加一行（15 min）

在 `test_invalid_pool_is_rejected` 的表里加一行"积分是字符串"：

```python
pytest.param([{"id": "a", "name": "A", "weight": 1, "points": "1"}], "INVALID_POINTS", id="积分是字符串"),
```

跑：

```powershell
python -m pytest -q -k "invalid_pool"
```

期望 `passed`，总数变成 41。

### 2.3 让它红一次（5 min）

把刚加的期望值改成 `"INVALID_POOL"`，再跑。期望变红，报错形如：

```
AssertionError: assert 'INVALID_POINTS' == 'INVALID_POOL'
```

改回去。**这就是"用例在守规则"的体感**：实现没动，只改期望，测试立刻翻脸。

## 3. 记（10 min）

progress.md 写：`Day 04 | ✅ | 加了一行参数化用例并通过（41 条）；学会 -k/--lf/--collect-only`

## 验收清单

- [ ] 能用 `--collect-only` 说出当前用例数
- [ ] 能只跑 `invalid_pool` 这一组
- [ ] 自己加的行先红后绿
- [ ] 能解释"为什么 id 要写中文"

## 面试口径

> 我的用例是"一条用例 = 一行数据"：参数化表里每一行就是一个场景，失败时报告直接告诉你是哪一行。
> 组织上我会把"要独立报告失败的"写成参数化，"只校验整体不变式的"写成一条循环断言——
> 前者用来定位，后者用来防回归。

## 卡住了怎么办

| 现象 | 原因 | 处理 |
| --- | --- | --- |
| `-k` 匹配不到 | 名字或中文编码问题 | 用 `-k "invalid"` 更宽松，或直接 `-k "test_invalid_pool"` |
| 加了行但总数没变 | 缩进错位，表没接上 | 看 `--collect-only -q` 里有没有新 id |
| 报 `IndentationError` | 复制时带了行号 | 重新手打那一行 |
