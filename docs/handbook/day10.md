# Day 10 · 造数与状态隔离：为什么这组用例只能串行

> 60 分钟 = 读 15 · 实验 25 · 设计 15 · 记 5
> 今天要拿到一个"能讲清楚取舍"的结论，而不是一句"因为会挂所以串行"。

## 今天结束时要能做到

1. 解释"用接口造数"比"用 UI 点 30 次"好在哪；
2. 亲手复现一次并发导致的 flaky；
3. 说出三种隔离方案的代价（串行 / 每 worker 独立实例 / 每例唯一数据）。

## 1. 读（15 min）

### 1.1 造数（8 min）

[`game.spec.js`](../../tests/e2e/game.spec.js) 85-104 行：排行榜用例先用接口塞了 3 个玩家：

```js
for (const [i, player] of players.entries()) {
  const resp = await request.post('/api/draw', { data: { player, seed: 99, index: i } });
  expect(resp.ok()).toBeTruthy();       // 造数本身也要断言，否则脏数据会伪装成 UI bug
}
```

对比：如果在 UI 上点 3 次，你要等 3 次动画、受随机奖品影响，还可能被限流。
**接口造数 = 直接构造前置条件，UI 只负责验证你关心的那段。**

### 1.2 隔离（7 min）

看 [`playwright.config.js`](../../playwright.config.js) 里的 `workers: 1` 和 `fullyParallel: false`，
以及 `game.spec.js:26` 的 `beforeEach → /api/reset`。

现在的方案是"**全局串行 + 每例重置**"。它成立的前提是：所有用例共享同一个服务实例。

## 2. 实验（25 min）

### 2.1 复现并发问题（15 min）

```powershell
npx playwright test --workers=2
```

多跑两次。期望看到**至少一次失败或 flaky**，典型报错：

```
expect(received).toHaveCount(expected)
Expected: 1  Received: 2
```

原因：worker A 刚 reset 完，worker B 抽了一次，A 的断言就看到 2 条历史。

> 如果你连跑三次都没复现，别急着说"没问题"——把它写进 progress.md 当作观察，
> 然后做 2.2：**把失败变成"必然"**，比如在两条用例里各加一次 `waitForTimeout(300)` 制造窗口。

### 2.2 看 `test.describe.configure`（10 min）

在 describe 上方临时加：

```js
test.describe.configure({ mode: 'serial' });
```

再跑 `--workers=2`。观察：串行模式让同文件用例排队，但**跨文件仍然并行**，
所以 `mobile.spec.js` 和 `game.spec.js` 还是会打架。

结论：`serial` 只解决文件内顺序，解决不了共享状态。

## 3. 设计（15 min）

把三种方案写进 progress.md，各写一句代价：

| 方案 | 做法 | 代价 | 什么时候用 |
| --- | --- | --- | --- |
| 全局串行 | `workers: 1` | 慢，且随用例数线性变慢 | 用例少、状态强耦合（本项目） |
| 每 worker 独立实例 | worker 启动时起独立端口 + 独立数据目录 | 需要服务支持"按实例隔离存储" | 真实项目首选 |
| 每例唯一数据 | 玩家名带 `workerIndex + date`，断言只针对自己的数据 | 断言要避开"总数/顺序"这类全局事实 | 只读接口多、写少 |

## 4. 记（5 min）

progress.md：`Day 10 | ✅ | --workers=2 复现了 history 计数冲突；结论：共享状态只能靠实例隔离，不能靠 reset`

## 验收清单

- [ ] 亲手用 `--workers=2` 跑出过一次失败/不稳定
- [ ] 能解释 `serial` 为什么不够
- [ ] 三种隔离方案各能说一句代价
- [ ] 知道造数后为什么要 `expect(resp.ok())`

## 面试口径

> 这组 E2E 我设成 `workers: 1`，但我不会只说"因为会挂"。
> 我实际操作过：`--workers=2` 时两个 worker 共享同一个服务实例，
> 一个 reset 另一个正在断言，必挂。`serial` 只保证文件内顺序，跨文件照样并发。
> 正确的做法是每个 worker 独立实例；这个 demo 里服务是内存态、改造成本高，
> 所以我选了串行，并在配置里写清原因和代价。

## 卡住了怎么办

| 现象 | 处理 |
| --- | --- |
| `--workers=2` 一直不挂 | 用例太快、窗口太窄；加 `waitForTimeout` 人为放大窗口，先证明机制存在 |
| 改完配置全挂 | 检查是否漏了 `fullyParallel: false` |
| 忘记改回 | `git diff playwright.config.js`，`git checkout -- playwright.config.js` |
