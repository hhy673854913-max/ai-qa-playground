# Day 06 · 排行榜：排序里的魔鬼细节

> 60 分钟 = 读 20 · 改坏 20 · 修 10 · 记 10
> 排序是"看起来简单、实际全是坑"的典型：同分怎么排？一人多条算哪条？limit 越界？

## 今天结束时要能做到

1. 说出这套排序规则的三个层级：**分数降序 → 时间升序 → 名字升序**；
2. 解释"同一玩家只保留最好成绩"的实现位置；
3. 改坏排序，让恰好 1 条用例变红。

## 1. 读（20 min）

打开 [`game/core.py`](../../game/core.py) 132-149 行的 `rank()`：

```python
best: dict[str, Entry] = {}
for raw in entries:
    entry = _coerce(raw)
    current = best.get(entry.player)
    if current is None or (entry.score, -entry.at) > (current.score, -current.at):
        best[entry.player] = entry

ordered = sorted(best.values(), key=lambda e: (-e.score, e.at, e.player))
```

两个技巧值得记住：

1. **用元组比较表达"多关键字排序"**：`(score, -at) > (...)` 一次比较完成"分数优先、同分取更早"。
2. **排序 key 里带名字兜底**：`(-score, at, player)` 让"分数和时间都一样"时结果稳定，
   否则不同版本的 Python / 不同数据库返回顺序会让断言飘。

再看 [`tests/unit/test_leaderboard.py`](../../tests/unit/test_leaderboard.py) 的 30-47 行：
同分先到先得、全同按名字升序 —— **规则都写死在用例里，不靠人记**。

## 2. 改坏（20 min）

### 2.1 改同分规则（10 min）

把排序 key 从

```python
key=lambda e: (-e.score, e.at, e.player)
```

改成

```python
key=lambda e: (-e.score, -e.at, e.player)
```

跑：

```powershell
python -m pytest -q -k "tie"
```

期望 `test_tie_goes_to_earlier_player` 变红：先到的那位跑到了后面。

### 2.2 改聚合规则（5 min）

把 `>` 改成 `<`，再跑 `-k "player"`。
期望 `test_same_player_keeps_best_score` 变红（现在保留的是最差成绩）。

### 2.3 修回去（5 min）

```powershell
git checkout -- game/core.py
python -m pytest -q        # 回到 44 passed（Day 05 加过 3 条）
```

## 3. 记（10 min）

progress.md：`Day 06 | ✅ | 改 key 让同分用例变红；理解"名字兜底"是为了可复现`

## 验收清单

- [ ] 能背出三级排序规则
- [ ] 亲手让 `test_tie_goes_to_earlier_player` 红过
- [ ] 解释了为什么排序 key 要带 `player`
- [ ] 代码已修回，全部用例通过

## 面试口径

> 排行榜我特意把规则写死在用例里：分数降序、同分先到先得、再同分按名字。
> 最后那个"名字兜底"不是为了美观，是为了**结果可复现**——
> 不兜底的话，两次查询顺序不同就能让你怀疑人生。
> 聚合规则（一人只留最好成绩）也在测试里，改坏了立刻红。

## 卡住了怎么办

| 现象 | 处理 |
| --- | --- |
| 改了 key 但测试没红 | 你可能改的是 `best` 比较那行；确认改的是 `sorted(...)` 的 key |
| 红了一大片 | `-e.at` 同时影响聚合与排序；只改排序 key 才精准 |
| 修不回去 | `git checkout -- game/core.py`，或用 `git diff` 对照手改 |
