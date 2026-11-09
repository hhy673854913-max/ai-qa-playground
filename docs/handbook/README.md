# 学习手册 · 14 天，每天 1 小时

> 目标不是"看完"，而是**每天留下一个能拿给别人看的产出**：一条新用例、一段改动、一份对比数据、一段能背下来的口径。
> 14 天 × 60 分钟 ≈ 14 小时，正好够把这个仓库从"别人写的"变成"你的"。

## 适合谁

- 有 Python 基础，但没系统做过测试开发；
- 用过 Playwright / pytest 的零散 API，但说不清"为什么这么设计"；
- 准备面试，需要一个能在 3 分钟里讲完、又经得起追问的项目。

## 开始前（只做一次，约 20 分钟）

```powershell
cd ai-qa-playground
python -m pip install -r requirements.txt      # pytest
python -m pytest -q                            # 期望 40 passed
python ai/react_loop.py                        # 期望 3 轮 Thought/Action/Observation

npm ci                                         # Playwright 依赖
npx playwright install chromium                # 浏览器（约 150MB）
npm run test:e2e                               # 期望 13 passed / 1 skipped
```

跑不通就先别看 Day 01 —— 见每篇文末的「卡住了怎么办」。

## 14 天路线

| 天 | 主题 | 主文件 | 当天产出（证据） |
| --- | --- | --- | --- |
| [Day 01](day01.md) | 跑通全链路，建立"绿"的体感 | `README.md` | 三条命令的成功输出截图 / 记录 |
| [Day 02](day02.md) | 读懂被测服务：路由、错误码、状态 | `game/server.py` | 一张"请求 → 校验 → 状态变化"图 |
| [Day 03](day03.md) | 抽奖算法：为什么用 `sha256(seed:index)` | `game/core.py:65` | 一段 seed 序列观察记录 |
| [Day 04](day04.md) | pytest：fixture 与参数化 | `tests/unit/test_lottery.py` | 一条自己写的参数化用例 |
| [Day 05](day05.md) | 用例设计：边界、不变式、统计断言 | `tests/unit/` | 6 条新用例（有 2 条会失败并被你修掉） |
| [Day 06](day06.md) | 排行榜：排序里的魔鬼细节 | `game/core.py:132` | 改坏排序规则并让 2 条用例变红 |
| [Day 07](day07.md) | 第一周复盘 + 自测 10 题 | 全部 | 复盘笔记 + 自测得分 |
| [Day 08](day08.md) | Playwright 地基：定位器与 web-first 断言 | `playwright.config.js` | 能解释为什么不写 CSS 选择器 |
| [Day 09](day09.md) | 写你的第一条 E2E | `tests/e2e/game.spec.js` | 新增 1 条用例并通过 |
| [Day 10](day10.md) | 造数与状态隔离 | `game.spec.js:85` | 一份"为什么串行"的取舍说明 |
| [Day 11](day11.md) | 移动端与视觉断言 | `tests/e2e/mobile.spec.js` | 一条溢出/视口断言 |
| [Day 12](day12.md) | Midscene：AI 驱动 UI 的真实体感 | `tests/e2e-midscene/` | 一次 AI 用例运行 + 耗时对比 |
| [Day 13](day13.md) | CI：从 push 到 artifact | `.github/workflows/ci.yml` | 一次自己触发的 run 链接 |
| [Day 14](day14.md) | ReAct 循环：自己实现一遍 | `ai/react_loop.py` | 新增一个工具并跑出 trace |
| [Day 15（加餐）](day15.md) | 讲成面试故事：STAR + 数据 | `docs/metrics.md` | 3 分钟自我介绍稿 |

## 每天怎么用（60 分钟）

| 阶段 | 时长 | 做什么 |
| --- | --- | --- |
| 读 | 20~25 min | 只看当天指定的文件与行号，带着问题读，别通读全仓 |
| 练 | 25~30 min | 按"改动 → 跑命令 → 看输出"的顺序做，**必须让某条测试红一次再绿** |
| 记 | 5~10 min | 在 [progress.md](progress.md) 写一行：今天做了什么、卡在哪、一句话面试口径 |

## 三条学习原则

1. **先改坏，再修好。** 看懂代码不算懂，能预测"改这里会让哪条用例红"才算。
2. **先看失败信息。** 用例红了先读报错（哪个断言、期望值、实际值），再动手查代码。
3. **每天留一句能背的话。** 面试考的是表达，不是记忆；当天写下的那句话，就是 14 天后你的底稿。

## 时间不够怎么办

每天只有 20 分钟时，只做一件事：**跑当天"练"里的一条命令，并解释输出**。
连续性比时长重要——14 天各 20 分钟，远好过一天 4 小时然后断掉。

## 打卡

把每天的结果写进 [progress.md](progress.md)。14 天后它就是你简历里"学习能力"的证据，
面试聊到项目时可以直接念。
