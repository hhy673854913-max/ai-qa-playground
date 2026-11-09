# Day 03 · 抽奖算法：为什么是 `sha256(seed:index)`

> 60 分钟 = 读 25 · 练 30 · 记 5
> 今天唯一的目标：**你能亲手证明"确定性"是设计出来的，不是碰巧。**

## 今天结束时要能做到

1. 解释 `draw()` 为什么不用 `random`；
2. 预测"同一个 seed 换 index 会得到什么"；
3. 把实现改坏，看到某条用例变红，再修回去。

## 1. 读（25 min）

打开 [`game/core.py`](../../game/core.py)，只读三段：

- **15-21 行**：奖池配置（weight 合计 100，points 是排行榜分数）
- **65-93 行**：`draw()` —— 今天的主角
- **95-104 行**：`odds()` —— 概率是怎么算出来的

带着三个问题读：

1. `roll = int.from_bytes(sha256(f"{seed}:{index}")[:8]) % total` 里，为什么要取模 `total`（而不是 100）？
   （答：奖池权重可以不是 100，取模保证落在累计权重区间内。）
2. 为什么把 `index` 拼进哈希，而不是用时间？
   （答：时间不可复现，E2E 就没法断言"第 3 抽一定是机械键盘"。）
3. `draw` 里有副作用吗？
   （答：没有。它不写流水、不加锁 —— 副作用在 `server.record()`。）

## 2. 练（30 min）

### 2.1 观察序列（10 min）

```powershell
python -c "from game.core import draw; print([draw(seed=7, index=i)['id'] for i in range(10)])"
```

期望（顺序固定，每次一样）：

```
['common', 'rare', 'common', 'common', 'common', 'rare', 'rare', 'common', 'rare', 'epic']
```

再跑一次，确认输出**逐字相同**。

### 2.2 手算一次（10 min）

```powershell
python -c "import hashlib; h=hashlib.sha256('7:0'.encode()).digest(); print(int.from_bytes(h[:8],'big') % 100)"
```

期望 `39`。这就是第 0 抽的 `roll`；39 落在"再来一次（权重 80）"的区间里，
所以第一抽是 `common` —— 和 2.1 一致。**能对上，说明你真的读懂了。**

### 2.3 改坏它（10 min）

把 `draw()` 里的两行改写为：

```python
import random
roll = random.randint(0, total - 1)
```

然后跑：

```powershell
python -m pytest -q
```

期望看到 `test_same_seed_and_index_is_reproducible` 变红，报错大意是
`assert first == second` 不成立（`roll` 每次不同）。

修回去：

```powershell
git checkout -- game/core.py
python -m pytest -q     # 回到 40 passed
```

> 这一步是全套手册里最重要的动作：**先让测试红一次**，你才会信任它。

## 3. 记（5 min）

progress.md 写：`Day 03 | ✅ | 手算 roll=39 对上序列；把 draw 改成 random 后 1 条用例变红 | 确定性是为了让断言能具体`

## 验收清单

- [ ] 两次运行序列完全一致
- [ ] 手算出的 `roll` 和实际序列对得上
- [ ] 亲眼看到 `test_same_seed_and_index_is_reproducible` 变红
- [ ] 用 `git checkout` 修回去，重新 40 passed
- [ ] 能说出"副作用在哪一层"

## 面试口径

> 抽奖我用 `sha256(seed:index)` 代替随机数。不是为了炫技，是因为**测试需要可复现**：
> 只有同 seed 必得同一串奖品，E2E 才能断言"第 3 抽是机械键盘"，而不是"中了一个"这种永远为真的废话。
> 副作用（写排行榜）被放在服务层的 `record()` 里，所以 `draw()` 是纯函数，单测不用起服务。

## 卡住了怎么办

| 现象 | 原因 | 处理 |
| --- | --- | --- |
| 序列和手册不一样 | 改了 `PRIZES` 权重 | `git checkout -- game/core.py` |
| `git checkout` 后仍有改动 | 只改了文件没存盘？ | `git status` 看 `game/core.py`，再 `git diff` |
| 手算和实际不一致 | 用了 `str(seed)` 的别的格式 | 严格按 `f"{seed}:{index}"`，中间是英文冒号 |
