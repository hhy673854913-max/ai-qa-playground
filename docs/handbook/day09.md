# Day 09 · 写你的第一条 E2E

> 60 分钟 = 读 15 · 写 30 · 修 10 · 记 5
> 目标：从"能跑别人的用例"到"能写一条别人挑不出毛病的用例"。

## 今天结束时要能做到

1. 把一条业务规则（历史最多 5 条）翻译成 E2E 断言；
2. 用 `beforeEach` 处理有状态服务的脏数据；
3. 失败时能从报错定位到"哪一行、期望什么、实际什么"。

## 1. 读（15 min）

打开 [`tests/e2e/game.spec.js`](../../tests/e2e/game.spec.js)，重点看三处：

- **15-21 行** `drawAndReadPrize()`：把"点一次 + 等结果 + 读奖品"封装成一个动作。
  抽 3 次、6 次都复用它 —— **别在循环里复制粘贴四行等待**。
- **24-28 行** `beforeEach`：每例先 `/api/reset`，再带 `?seed=7&player=qa-bot` 打开页面。
  有状态的服务，不重置就等着用例互相污染。
- **68-83 行** "连抽三次"：这就是今天要写的东西的 3 次版。

再看 [`web/app.js`](../../web/app.js) 44-53 行，确认被测行为：

```js
els.history.prepend(li);                                  // 新的插到最前面
while (els.history.children.length > 5) els.history.lastElementChild.remove();  // 超过 5 条删最旧
```

**规则读清楚了再写断言**：新在最上、只留 5 条、被挤掉的是最旧的那条。

## 2. 写（30 min）

在 `game.spec.js` 的 describe 块末尾，新增一条用例：

```js
test('连抽六次：历史只保留最近五条，最新在最上面', async ({ page }) => {
  for (let i = 0; i < 6; i += 1) {
    await drawAndReadPrize(page);
  }

  // 1) 计数是 6（说明真的抽了 6 次，不是被按钮禁用卡住）
  await expect(page.locator('#draw-count')).toHaveText('6');

  // 2) 历史截断到 5 条
  await expect(page.locator('#history li')).toHaveCount(5);

  // 3) 最新的在最上面，最旧的已经被挤掉
  await expect(page.locator('#history li').first()).toContainText('#6');
  await expect(page.locator('#history li').last()).toContainText('#2');
});
```

跑：

```powershell
npx playwright test -g "连抽六次"
```

期望 1 passed。

### 如果它红了（大概率会红一次）

按顺序读报错里的三样东西：**哪一行断言、Expected 多少、Received 多少**。

| 你看到的 | 说明 | 怎么办 |
| --- | --- | --- |
| `Expected: 6, Received: 5` | 第 6 次点击没生效 | 上一次点击还在动画中？检查 `drawAndReadPrize` 的等待条件 |
| `Expected: 5, Received: 6` | 截断逻辑没生效（或你抽了 7 次） | 回看 `app.js:53` 的 `> 5` |
| `first()` 读到 `#5` | 顺序反了 | 去确认 `prepend` 还是 `append` |

## 3. 修（10 min）

把 `app.js` 的 `> 5` 改成 `> 6`，重跑 —— 你的用例应该变红（Received: 6）。
这一步证明**你的用例真的在守规则**，而不是碰巧通过。改回去。

## 4. 记（5 min）

progress.md：`Day 09 | ✅ | 新增"连抽六次"用例；把 >5 改成 >6 验证它能红`

## 验收清单

- [ ] 新用例独立跑通过
- [ ] 全量 E2E 通过（14 passed / 1 skipped）
- [ ] 亲手让新用例红过一次（改 `app.js` 的截断阈值）
- [ ] 能说出 `beforeEach` 里两行各自防的是什么

## 面试口径

> 我写的 E2E 不写"中了一个奖"这种废话断言，而是断言**具体的序号和数量**：
> 连抽 6 次后历史必须正好 5 条、第一条是 #6、最后一条是 #2。
> 为了让断言站得住，我先把 `app.js` 的截断阈值改坏，确认这条用例会红——
> 验证过"能失败"的用例才算用例。

## 卡住了怎么办

| 现象 | 处理 |
| --- | --- |
| 抽 6 次很慢（每次都在等动画） | 说明你在等固定时长；改成等 `data-prize` 变化（`drawAndReadPrize` 已封装） |
| `#6` 匹配不到 | 检查 `#history li` 的文本格式，先 `console.log(await page.locator('#history').innerText())` |
| 全量跑时只有这条挂 | 状态污染：确认 `beforeEach` 的 `/api/reset` 没被你删 |
