# Day 12 · Midscene：AI 驱动 UI 的真实体感

> 60 分钟 = 读 15 · 跑 25 · 改一句 15 · 记 5
> 今天的目标不是"会用 Midscene"，而是**能说清它什么时候值得用、什么时候是灾难**。

## 今天结束时要能做到

1. 用它跑通 2 条 AI 用例，看到 `aiAct` / `aiAssert` / `aiQuery` 三件套的分工；
2. 只改一句自然语言，观察行为变化；
3. 说出一条"传统脚本比 AI 更合适"的场景。

## 1. 读（15 min）

### 1.1 用例（8 min）

[`tests/e2e-midscene/midscene.spec.js`](../../tests/e2e-midscene/midscene.spec.js)：

```js
await agent.aiAct('点击页面中间那个写着「抽一次」的按钮');
await agent.aiAssert('页面上出现了一个奖品名称，并且「已抽」后面的数字是 1');
const result = await agent.aiQuery('{ prizeName: string, drawCount: string }, 当前奖品与已抽次数');
```

三个原语，分工完全不同：

| 原语 | 语义 | 失败时 |
| --- | --- | --- |
| `aiAct` | 执行动作（点、输入、滚动） | 找不到目标会重试/报错 |
| `aiAssert` | 断言自然语言描述成立 | 抛错，**成功时返回 undefined** |
| `aiQuery` | 从页面**取值**，返回结构化对象 | 拿不到会返回空/异常 |

顺序有讲究：先 Act，再 Assert/Query。**不要在动作前 Query** —— 拿到的还是旧值。

### 1.2 取舍（7 min）

打开 [`docs/ai-ui-automation.md`](../../docs/ai-ui-automation.md) 的「实测数据」：

| 方案 | 用例数 | 总耗时 | 单条耗时 |
| --- | --- | --- | --- |
| 传统 Playwright | 14 | 24s | ~1.7s |
| Midscene | 2 | 27.4s | ~13s |

**AI 单条慢 10 倍**，换来的是"改版时改一句话而不是 20 行选择器"。
文档里还写了另一条更重要的：**选择器漂移 vs 多模态误识别** —— 两种失败模式，排障方式完全不同。

## 2. 跑（25 min）

```powershell
cd tests/e2e-midscene
npm ci
npx playwright install chromium

# Key 放在仓库外（例如 C:\space\测开\.key），脚本只把它读进环境变量
powershell -File run-local.ps1 -KeyFile ..\..\..\.key
```

期望 `2 passed`，每条 10~15s。

跑完**一定打开报告**（这一步大多数人都跳过，但它才是 AI 自动化能落地的原因）：

```powershell
start midscene_run\report
```

报告里有每一步的截图、模型输入输出、耗时。问自己：**模型当时"看到"的和我以为的一致吗？**

## 3. 改一句（15 min）

把第一条用例的指令改成"连续点击抽奖按钮两次"，再跑：

```powershell
# run-local.ps1 会把多余的参数原样转给 playwright，所以 -g 可以直接用
powershell -File run-local.ps1 -KeyFile ..\..\..\.key -g "说人话"
```

观察两件事：

1. 模型是否真的点了两次（看报告里的步骤数）；
2. `aiAssert` 的"已抽 1 次"是否开始失败 —— **说明断言和动作是解耦的，这正是它的价值**。

改回去。

## 4. 记（5 min）

progress.md：`Day 12 | ✅ | Midscene 2 条跑通（13.8s/10.3s）；改成连点两次后断言如预期失败`

## 验收清单

- [ ] 2 条 AI 用例通过
- [ ] 打开过 `midscene_run/report` 并看懂一步
- [ ] 改过一句指令，观察到行为/断言变化
- [ ] 能说出 AI 单条为什么慢

## 面试口径

> 我做过一次对比：同样覆盖抽奖主流程，传统 Playwright 14 条 24 秒，Midscene 2 条 27 秒。
> AI 单条慢十倍，但它解决的是"选择器漂移"——改版时我改一句中文就行。
> 不过它有另一种失败模式：多模态误识别，排障要看它当时的截图。
> 所以我的策略是分层：稳定的核心流程用手写选择器，易变的展示层用 AI；而不是二选一。

## 卡住了怎么办

| 现象 | 原因 | 处理 |
| --- | --- | --- |
| 全 skip | 没读到 `MIDSCENE_MODEL_API_KEY` | `run-local.ps1` 的 KeyFile 路径写对了吗 |
| `Model not exist` | 账号没有该模型 | 先 `GET /models` 看可用列表 |
| `Executable doesn't exist` | 浏览器装在了根套件 | 在 `tests/e2e-midscene` 里重装，并设 `PLAYWRIGHT_BROWSERS_PATH=0` |
| 断言偶发失败 | 动画未结束 | 用 `aiAssert`（内部重试），别用 `aiQuery` 做布尔判断 |
