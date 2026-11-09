# Day 11 · 移动端与视觉断言

> 60 分钟 = 读 15 · 加设备 15 · 加断言 20 · 记 10
> H5 的事故八成是"布局溢出"和"点不到"，今天把这两类变成断言。

## 今天结束时要能做到

1. 用 `isMobile` 让一条用例只在一个端跑；
2. 给项目加一个新设备（iPhone 13），并解释 `browserName` 覆盖的意义；
3. 写出"按钮在视口内、可点、尺寸达标"三条断言。

## 1. 读（15 min）

### 1.1 一条用例覆盖多端（8 min）

[`tests/e2e/mobile.spec.js`](../../tests/e2e/mobile.spec.js) 第 11 行：

```js
test.skip(!isMobile, '仅在移动端 project 运行');
```

这个 spec 会被两个 project 各跑一遍；桌面端直接 skip。
好处：**不用复制文件**，也不会出现"移动端用例忘了同步改"。

### 1.2 配置里的设备（7 min）

[`playwright.config.js`](../../playwright.config.js) 42-51 行，两个 project：
`desktop-chromium` 用 `Desktop Chrome`，`mobile-chromium` 用 `Pixel 7`。
`devices['Pixel 7']` 一次性给你：视口、UA、`isMobile: true`、`deviceScaleFactor`、触摸支持。

## 2. 加设备（15 min）

在 projects 里加第三个：

```js
{
  name: 'mobile-iphone13',
  // devices['iPhone 13'] 默认 browserName 是 webkit；这里覆盖成 chromium，
  // 省掉一次 webkit 内核下载（约 100MB），代价是 UA 是 iPhone 但内核是 Chromium。
  use: { ...devices['iPhone 13'], browserName: 'chromium' }
}
```

跑：

```powershell
npx playwright test --project=mobile-iphone13
```

期望 1 passed（mobile 用例在 iPhone 13 视口下也通过）。

> 为什么值得覆盖 `browserName`：真机上 iOS 只有 WebKit，内核差异确实存在；
> 但 H5 的绝大多数问题是布局，Chromium 就能抓到。**先覆盖布局，再覆盖内核**，按成本排序。

## 3. 加断言（20 min）

在 `mobile.spec.js` 里补两段：

```js
// 1) 主按钮必须在视口内（否则用户要滚动才能抽）
await expect(button).toBeInViewport();

// 2) 触控目标不小于 44×44（iOS HIG / Material 的通行下限）
const box = await button.boundingBox();
expect(box.height, '按钮高度应 >= 44px').toBeGreaterThanOrEqual(44);
expect(box.width, '按钮宽度应 >= 44px').toBeGreaterThanOrEqual(44);
```

跑 `--project=mobile-iphone13`，两条都通过。

### 让它红一次

在 `web/style.css` 里把 `.draw-btn` 的 `padding` 改小（比如 `4px 8px`），重跑 ——
高度断言应该变红。改回去。**这就是"布局回归"的守门人。**

## 4. 记（10 min）

progress.md：`Day 11 | ✅ | 加了 iPhone 13 project（chromium 内核）；补了视口内 + 44px 断言`

## 验收清单

- [ ] 三个 project 都能单独跑
- [ ] `isMobile` 的 skip 机制说得清
- [ ] 44px 断言被改坏过一次
- [ ] 知道"UA 是 iPhone、内核是 Chromium"的取舍

## 面试口径

> H5 我固定测三类东西：横向溢出（`scrollWidth - innerWidth <= 1`）、
> 主操作在首屏视口内、触控目标 >= 44px。
> 设备矩阵上我先用 Chromium 覆盖 iPhone 13 的视口——布局问题它全能抓；
> 内核差异另开小规模 WebKit 任务，按成本排优先级。

## 卡住了怎么办

| 现象 | 处理 |
| --- | --- |
| `browserType.launch: Executable doesn't exist` | 覆盖 `browserName: 'chromium'` 后仍报 webkit？确认 spread 顺序（覆盖在后） |
| 三个 project 全跑 | 用 `--project=` 指定；不指定就是全部 |
| 44px 断言不稳定 | 动画中出现中间态；等 `toBeEnabled()` 后再量 |
