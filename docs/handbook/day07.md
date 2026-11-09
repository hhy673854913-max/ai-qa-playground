# Day 07 · 第一周复盘 + 自测 10 题

> 60 分钟 = 复盘 20 · 自测 20 · 提交产出 15 · 计划下周 5
> 今天不学新东西。**把前六天变成能说出口的东西**，顺便让 GitHub 上留下记录。

## 1. 复盘（20 min）

打开 [progress.md](progress.md)，回看 Day 01-06 的记录，回答三个问题（写在复盘区）：

1. 哪一天我"以为懂了，其实没懂"？现在能讲清了吗？
2. 我改坏过哪几处代码？每次是哪条用例先红？
3. 如果只用 3 句话向别人介绍这个仓库，我说哪三句？

## 2. 自测（20 min）

先自己写答案，再看折叠的参考答案。**写不出来 = 没学会**，回头补那一天。

**Q1.** `draw()` 为什么用 `sha256(seed:index)` 而不是 `random`？说出三点。

<details><summary>参考答案</summary>

1. 可复现：同 seed+index 必得同一奖品，E2E 才能断言"具体中了什么"；
2. 无状态：服务重启、并发请求都不改变结果，测试不用关心随机源被谁消费；
3. 与 Python 版本解耦：不依赖 `random` 内部实现的稳定性。
</details>

**Q2.** `draw()` 有副作用吗？副作用被放在哪一层？

<details><summary>参考答案</summary>

没有。它只做纯计算。副作用（写 `DRAW_LOG`、加锁）在 `game/server.py` 的 `record()` 里。
这正是单测能直接测 `draw` 而不需要起服务的原因。
</details>

**Q3.** `record()` 为什么要加锁？不加会怎样？

<details><summary>参考答案</summary>

`ThreadingHTTPServer` 会并发处理请求，多个线程同时 `list.append` 虽在 CPython 里通常安全，
但"读-改-写"类的复合操作（以及未来换成 DB）会丢更新。加锁把写操作串行化，代价可忽略。
</details>

**Q4.** `@pytest.mark.parametrize(..., id="空奖池")` 里的 `id` 有什么用？

<details><summary>参考答案</summary>

让报告里显示可读的场景名（`[空奖池]`），而不是 `[case1]`。CI 失败时靠它一眼定位是哪行数据。
</details>

**Q5.** 什么时候用参数化表，什么时候用"一条循环断言"？

<details><summary>参考答案</summary>

需要**每个场景独立报告失败** → 参数化；只是校验**整体不变式**（如概率合计 100）→ 一条循环。
参数化会把用例数放大，别滥用。
</details>

**Q6.** 统计测试（2 万次抽样验权重）为什么不会 flaky？

<details><summary>参考答案</summary>

因为随机源是 `sha256(seed:index)`，样本本身是确定的；同一个 seed 永远得到同一组 2 万个结果，
所以误差不会"这次超了下次不超"。
</details>

**Q7.** 排行榜的排序规则有哪三级？

<details><summary>参考答案</summary>

分数降序 → 同分按达成时间升序（先到先得）→ 再同分按名字升序（兜底，保证可复现）。
</details>

**Q8.** 为什么排序 key 最后要加 `player`（名字）？

<details><summary>参考答案</summary>

分数和时间都相同时，若没有第三关键字，排序结果依赖输入顺序，断言会飘。加名字让结果稳定。
</details>

**Q9.** 同一个玩家抽了 10 次，排行榜里会出现几条记录？为什么？

<details><summary>参考答案</summary>

1 条。`rank()` 用 `best` 字典按玩家聚合，只保留最好成绩（同分则保留更早达成的那条）。
</details>

**Q10.**（开放题）如果要加"10 连抽必出史诗及以上"的保底机制，你会怎么设计、怎么测？

<details><summary>参考思路</summary>

设计上把"保底计数器"从纯函数里拿出来（否则 `draw` 不再是纯函数），放在服务层的玩家状态里；
测试分三层：① 单测 `draw` 的纯逻辑不变；② 单测保底判定函数（第 10 次强制提升）；③ E2E 连点 10 次断言必出史诗。
再补一条"中途出了史诗，计数器归零"的用例。
</details>

## 3. 提交产出（15 min）

把 Day 04/05 写的东西交给 Git（这也是面试时能翻的记录）：

```powershell
git checkout -b learn/day01-07
git add tests/unit/test_gaps.py
git commit -m "test: 补齐 total_weight 与 rank 默认 limit 的覆盖缺口（学习 Day 05）"
git push -u origin learn/day01-07
```

然后在 GitHub 上开一个 PR，标题写清"学习产出"，**自己 review 自己一次**，留一条评论说明你学到了什么。

> 这一步的意义：面试官问"你怎么保证学习有产出"，你可以直接给 PR 链接。

## 4. 计划下周（5 min）

Day 08-14 的主线是 E2E + AI + CI，全是"要跑起来"的东西。
提前确认：Node 装好了吗？浏览器下载过了吗？（Day 01 里没跑成的，今天补上。）

## 验收清单

- [ ] 10 道题至少答对 8 道
- [ ] progress.md 的复盘区写了三段
- [ ] 分支 `learn/day01-07` 推上去了，且有 PR
- [ ] 下周环境就绪（`npx playwright --version` 有输出）

## 面试口径

> 我学东西有个硬要求：每周必须留下一个能被别人看见的产出——这次是一个 PR，
> 里面补了三处没被覆盖的公共函数。学没学会，看 PR 比看笔记准。
