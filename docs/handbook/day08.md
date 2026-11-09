# Day 08 · Playwright 地基：定位器、等待、配置

> 60 分钟 = 读 25 · 跑 25 · 记 10
> 今天的核心不是"会点按钮"，而是理解**为什么你的用例会变脆，以及框架怎么帮你兜住**。

## 今天结束时要能做到

1. 说出定位器的优先级（role > testid > text > CSS），并解释为什么禁 CSS；
2. 解释 `expect(locator).toBeVisible()` 和 `sleep(1)` 的本质区别；
3. 看懂 `playwright.config.js` 里 `webServer` / `retries` / `reporter` 三个配置的作用。

## 1. 读（25 min）

### 1.1 配置（10 min）

打开 [`playwright.config.js`](../../playwright.config.js)，找三处：

- **webServer**：测试前自动起 `python -m game.server`，等 `/health` 通了才开始跑。
  好处：不需要"先手动开服务"这种口头约定，CI 里也一样。
- **workers: 1 / fullyParallel: false**：注释里写了原因——共享一个有状态的服务。
- **retries / trace**：CI 上重试 1 次；trace 只在首次重试时保留（省空间但不丢排障现场）。

### 1.2 用例（15 min）

打开 [`tests/e2e/game.spec.js`](../../tests/e2e/game.spec.js)，只看 30-57 行（前两条用例）：

```js
await expect(page.getByRole('heading', { name: '幸运抽奖机' })).toBeVisible();
await expect(page.getByRole('button', { name: '抽一次' })).toBeEnabled();
```

问自己：如果改成 `page.locator('.draw-btn')`，下次换皮肤会怎样？
（答：类名一改，全红；而 role+name 是"用户看到的东西"，改版通常不动。）

## 2. 跑（25 min）

### 2.1 只跑一条，带界面（10 min）

```powershell
npx playwright test -g "首屏渲染" --headed --workers=1
```

观察浏览器自己打开、点击、关闭。**这一步能建立"测试就是替你点"的直觉。**

### 2.2 断点调试（10 min）

```powershell
npx playwright test -g "点击抽奖" --debug
```

会打开 Playwright Inspector：可以单步执行、看每一步的 locator 命中情况。
**这是排查"点错元素"最快的方式**，比加 log 快。

### 2.3 看它怎么失败（5 min）

故意把期望改错（比如把 `toHaveCount(1)` 改成 `toHaveCount(2)`），跑一次，读报错：

```
Expected: 2  Received: 1
```

注意报错里会带上 locator 的解析结果和页面快照提示 —— **失败信息本身就是排障入口**。改回去。

## 3. 记（10 min）

progress.md：`Day 08 | ✅ | 用 --debug 单步看了 locator 命中；改错期望值看过一次失败信息`

## 验收清单

- [ ] 能用一句话解释 `webServer` 解决了什么问题
- [ ] 用过 `--headed` 和 `--debug` 各一次
- [ ] 说得出为什么不用 CSS 类名定位
- [ ] 看过一次真实的断言失败信息

## 面试口径

> 我写 E2E 的第一原则是"贴着用户能感知的东西定位"：role + 可访问名称，其次 data-*，
> 最后才是 CSS。因为类名是给样式用的，改版必改；而按钮叫什么通常不改。
> 第二是等待：一律用 web-first 断言（内部自动重试），不写 sleep——sleep 要么不够、要么浪费时间。

## 卡住了怎么办

| 现象 | 原因 | 处理 |
| --- | --- | --- |
| `--headed` 没反应 | 无显示器/远程环境 | 只在本地用，服务器上不加 `--headed` |
| `--debug` 卡住 | 等待你操作 Inspector | 点 Step over 或 Resume |
| 找不到用例 | `-g` 是正则 | 用更短的关键字，如 `-g "首屏"` |
