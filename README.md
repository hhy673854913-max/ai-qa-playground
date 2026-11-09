# ai-qa-playground

一个把「测开」四件事串起来的练习仓库：**Playwright E2E**、**Midscene.js（AI 驱动 UI）**、**pytest 参数化单测**、**最小 ReAct / Function Calling 循环**，外加一份把 AI 提效翻译成质量语言的 [metrics 口径](docs/metrics.md)。

被测对象是一个自己写的 H5 抽奖小游戏（抽奖 + 排行榜），所以整条链路是完整的：
**业务代码 → 单测 → E2E → CI → 报告**，不是拿一堆孤立的 Hello World 拼凑。

```
pytest 40 条单测：0.2s       Playwright 用例：桌面 + 移动双 project      ReAct demo：离线可跑，无需 API Key
```

---

## 60 秒跑起来

```bash
# 1) 单测（只要 Python + pytest）
pip install -r requirements.txt
python -m pytest -v

# 2) 最小 ReAct 循环（不需要任何 API Key，用脚本化"模型"演示循环机制）
python ai/react_loop.py

# 3) E2E（需要 Node）
npm install
npx playwright install chromium
npm run test:e2e          # webServer 会自动拉起被测服务，不用手动开
npm run report            # 打开 HTML 报告：报告里有截图、trace、用例耗时
```

Windows 上如果 `python` 指向 Microsoft Store 的占位程序，用 `py -3.12`，并在跑 E2E 时指定
`$env:GAME_PYTHON="py"`。

---

## 目录结构

```
ai-qa-playground/
├─ game/
│  ├─ core.py                # 抽奖概率 + 排行榜排序（纯逻辑，pytest 直接测）
│  └─ server.py              # 标准库 HTTP：静态页 + /api/draw /api/leaderboard /api/odds
├─ web/                      # H5 页面（原生 JS，无框架，方便当靶子）
│  ├─ index.html
│  ├─ app.js
│  └─ style.css
├─ tests/
│  ├─ unit/                  # pytest 参数化单测（40 条）
│  │  ├─ test_lottery.py
│  │  └─ test_leaderboard.py
│  ├─ e2e/                   # Playwright（点击 / 断言 / 截图 / 双端）
│  │  ├─ game.spec.js
│  │  └─ mobile.spec.js
│  └─ e2e-midscene/          # 自然语言驱动（独立 package.json，需要模型 Key）
├─ ai/
│  └─ react_loop.py          # 最小 ReAct / Function Calling 循环（约 60 行核心逻辑）
├─ docs/
│  ├─ ai-ui-automation.md    # 传统 vs AI 自动化：各脆在哪、怎么组合
│  └─ metrics.md             # 采纳率 / 返工率 / 交付周期：口径 + 话术
├─ .github/workflows/ci.yml  # 单测 job + E2E job + 报告 artifact
├─ playwright.config.js
└─ pytest.ini
```

---

## 这个仓库对应哪几个面试问题

| 面试问题 | 仓库里的答案 |
| --- | --- |
| 「做过自动化吗？」 | `tests/e2e`：web-first 断言、`getByRole` 定位、trace/截图、双 project（桌面 + Pixel 7）、`webServer` 自启动 |
| 「用例怎么设计？」 | `tests/unit`：不变式 / 边界 / 统计 / 非法输入四类，参数化表格，一条用例一行数据 |
| 「AI 自动化了解吗？」 | `tests/e2e-midscene` + [docs/ai-ui-automation.md](docs/ai-ui-automation.md)：选择器漂移 vs 多模态误识别，分工策略 |
| 「用过 Function Calling 吗？」 | `ai/react_loop.py`：两个工具、while 循环、Thought/Action/Observation 全打印 |
| 「AI 提效怎么衡量？」 | [docs/metrics.md](docs/metrics.md)：采纳率 / 返工率 / 交付周期，含分子分母与数据来源 |
| 「CI 怎么接？」 | `.github/workflows/ci.yml`：单测 + E2E 两个 job，失败现场与报告都作为 artifact 上传 |

---

## 三个设计取舍（面试可以主动讲）

**1. 业务逻辑放在 Python，不放在前端。**
抽奖概率、排行榜排序都在 `game/core.py`，前端只负责调接口和渲染。
这样 pytest 能直接测纯函数（不用起浏览器），E2E 测到的是真业务而不是前端自演的一套。
**测试金字塔的塔基必须是能秒级跑的东西。**

**2. 抽奖用 `sha256(seed:index)` 而不是 `random`。**
同一 seed 永远得到同一串奖品，所以 E2E 可以断言「具体中了哪个奖品」，
而不是"中了某一个"这种永远为真的废话断言。同时它无状态，服务重启 / 并发都不影响结果。

**3. E2E 串行跑，不追并行。**
所有 worker 共享同一个有状态的被测服务，并行会互相污染排行榜数据。
真实项目应该给每个 worker 独立环境（独立 DB schema / 独立容器 / 独立账号），
而不是靠"重置接口"硬扛 —— 这个取舍写在 `playwright.config.js` 的注释里。

---

## 验证状态（重要，别拿没跑过的东西吹）

| 部分 | 状态 |
| --- | --- |
| `pytest` 单测（40 条） | ✅ 实跑通过（Python 3.12，0.2s） |
| 被测服务 + H5 页面 | ✅ 实跑通过（`/health`、`/api/draw`、`/api/leaderboard` 均已验证） |
| `ai/react_loop.py` 离线模式 | ✅ 实跑通过（3 轮 Thought/Action/Observation，含真实工具调用） |
| `tests/e2e`（Playwright） | ⚠️ 代码已写完，但作者环境无外网、装不了浏览器，**未在本机实跑** |
| `tests/e2e-midscene` | ⚠️ 需模型 Key，未实跑；API 以 Midscene 官方文档为准（见该目录 README） |
| GitHub Actions | ⚠️ 尚未在真实仓库跑过，首次 push 后请确认两个 job 都绿 |

第一次 push 之后，建议先手动 `workflow_dispatch` 跑一次，把 E2E job 的 Playwright 版本、
Chromium 下载、`python -m game.server` 启动链路都验证掉，再把 CI 徽章贴到 README 顶部。

---

## 已知限制

- 服务状态在内存里，重启即清空（够用，但不要当生产模板）。
- 没有数据库、没有登录态、没有多用户隔离 —— 这些会在真实项目里出现，见下一节。
- Midscene 依赖 `latest` 版本，第一次 `npm install` 后请把 `package-lock.json` 提交上来锁版本。

## 如果继续做，下一步

1. **环境隔离**：给每个 Playwright worker 一个独立端口 + 独立数据目录，然后打开 `fullyParallel`。
2. **视觉回归**：`expect(page).toHaveScreenshot()` 存基线，覆盖 3 种视口。
3. **AI 到确定的转化**：用 Midscene 探索新页面 → 人工审 → codegen 成选择器脚本进回归集。
4. **报告聚合**：junit + trace 汇总成一个静态页，把"最近 7 天 flaky 排行"算出来。
