# Day 01 · 跑通全链路，建立"绿"的体感

> 60 分钟 = 读 10 · 装与跑 40 · 记 10
> 今天不写代码。目标是让**三条链路各自出一次绿**，并在脑子里建立"这个仓库我能跑"的确定感。

## 今天结束时要能做到

1. 说出这个仓库的四块内容（单测 / E2E / AI E2E / ReAct demo）各自由什么驱动；
2. 在自己的机器上跑出 `40 passed` 和 `13 passed / 1 skipped`；
3. 知道自己环境里哪一步和别人不一样（Python 版本、是否需要代理、有没有 Node）。

## 1. 读（10 min）

打开 [README.md](../../README.md)，只看两节：**60 秒跑起来** 和 **目录结构**。
不要读设计取舍，那是 Day 08 之后的事。

读的时候回答自己：这个仓库里，**哪些东西是"被测对象"，哪些是"测试代码"？**
（答案：`game/` 与 `web/` 是被测对象；`tests/`、`playwright.config.js`、`ci/` 是测试代码。）

## 2. 跑（40 min）

### 2.1 单测（10 min）

```powershell
cd ai-qa-playground
python -m pip install -r requirements.txt
python -m pytest -q
```

期望最后一行：

```
40 passed in 0.2s
```

### 2.2 ReAct demo（5 min）

```powershell
python ai/react_loop.py
```

期望看到 3 轮 `Thought / Action / Observation`，最后一行是"奖池概率为：…；服务健康检查结果：ok"。
它不需要任何 API Key —— 这是刻意的，Day 14 会解释为什么。

### 2.3 E2E（20 min）

```powershell
npm ci
npx playwright install chromium
npm run test:e2e
```

期望：

```
13 passed (24.0s)
1 skipped
```

那条 skipped 是移动端用例在桌面 project 里主动跳过的（Day 11 会讲）。

### 2.4 看报告（5 min）

```powershell
npm run report
```

浏览器会打开 HTML 报告。点进任意一条用例，找到 **screenshot / trace**：
这就是"失败时你能不能自己排障"的关键，比看日志快 10 倍。

## 3. 记（10 min）

打开 [progress.md](progress.md)，填 Day 01，并额外写三行：

- 我的 Python 版本：`python --version`
- 我的 Node 版本：`node --version`
- 我多花时间的一步是：______（装浏览器？代理？路径？）

## 验收清单

- [ ] `python -m pytest -q` → 40 passed
- [ ] `python ai/react_loop.py` → 3 轮循环，最后有 Final Answer
- [ ] `npm run test:e2e` → 13 passed / 1 skipped
- [ ] 能在报告里找到某条用例的截图或 trace
- [ ] progress.md 写了 Day 01

## 面试口径（背一句）

> 这个项目我第一件事是把三条链路跑绿：pytest 单测 40 条、Playwright E2E 13 条、还有一个离线可跑的 ReAct demo。
> 先确认环境能复现，再谈改造——不然排查问题时会分不清是代码错还是环境错。

## 卡住了怎么办

| 现象 | 原因 | 处理 |
| --- | --- | --- |
| `No module named pytest` | 没用对解释器 | `python -m pip install -r requirements.txt`，别用 `pip` 裸命令 |
| `python` 打开应用商店 | Windows 商店占位符 | 用 `py -3.12`，或把真 Python 放前面 |
| 浏览器下载失败 | 公司网络/CDN 受限 | 设代理后重试：`$env:HTTPS_PROXY="http://127.0.0.1:7897"`，再 `npx playwright install chromium` |
| E2E 报端口占用 | 8100 被占 | `$env:GAME_PORT="8111"` 后重跑 |
| 完全没有 Node | 环境限制 | 跳过 2.3，在 progress.md 记 "E2E 未跑"，Day 09 前补上 |
