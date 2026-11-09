# Day 13 · CI：从 push 到 artifact

> 60 分钟 = 读 20 · 触发 20 · 故意失败 15 · 记 5
> 今天的产出是一个 **CI run 链接**：它证明"我的代码在别人机器上也绿"。

## 今天结束时要能做到

1. 说出三个 job 各自做什么、为什么互相独立；
2. 解释 `concurrency` 和 `if: always()` 各自解决什么问题；
3. 亲手制造一次失败，并从 artifact 里把现场捞出来。

## 1. 读（20 min）

打开 [`.github/workflows/ci.yml`](../../.github/workflows/ci.yml)，按顺序看四处：

| 位置 | 作用 | 你该记住的一句话 |
| --- | --- | --- |
| 3-7 行 `on` | push main / PR / 手动触发 | 手动触发（workflow_dispatch）在调试时救命 |
| 9-11 行 `concurrency` | 同一分支只保留最新一次 | 连推三次不会排队跑三次，省额度 |
| 14-41 行 `unit` | 装 Python → pytest → 跑 ReAct demo → 传报告 | 单测和 AI demo 放一起，因为都快（<1 分钟） |
| 43-75 行 `e2e` | 装 Node → 装浏览器 → playwright test → 传报告 | 浏览器安装是最慢的一步，单独一个 job 才不拖累单测 |
| 77-119 行 `midscene` | `if: vars.ENABLE_MIDSCENE == 'true'` | **job 级 if 拿不到 secrets 上下文**，所以用 vars 做开关 |

两个容易忽略的细节：

- `if: always()` 在"上传报告"这一步：**测试失败了也要把现场传上去**，否则你只能看日志里的几十行报错。
- e2e job 里的 `npm ci`，靠仓库里的 `package-lock.json` 保证依赖版本可复现。

## 2. 触发（20 min）

随便改一行文档（比如在 README 末尾加个空格），提交并推送：

```powershell
git add README.md
git commit -m "docs: 触发一次 CI（学习 Day 13）"
git push
```

然后打开 `https://github.com/hhy673854913-max/ai-qa-playground/actions`，做三件事：

1. 点进最新 run，看三个 job 的状态（midscene 应该是 **skipped**）；
2. 等 `unit` 绿了，点 **Artifacts → unit-report** 下载，解压看 `junit.xml`；
3. 点 `e2e` job 的步骤列表，找到 `npx playwright test` 那一步的耗时（约 1~2 分钟，大部分花在装浏览器）。

## 3. 故意失败（15 min）

在本地把某条单测改坏（例如把 `test_odds_sum_to_100` 的期望从 100 改成 99），
推到分支而不是 main：

```powershell
git checkout -b ci-fail-demo
git commit -am "test: 故意让 CI 红一次"
git push -u origin ci-fail-demo
```

打开这次 run，观察：

- 哪一步变红、日志里第一行错误是什么；
- `Artifacts → unit-report` 里的 junit 是否记录了失败。

然后删掉这个分支（或直接在本地 revert）：

```powershell
git checkout main
git branch -D ci-fail-demo
git push origin --delete ci-fail-demo
```

> 为什么不直接推 main：main 的红色记录会一直挂在仓库首页。**练手用分支**，这是习惯。

## 4. 记（5 min）

progress.md：`Day 13 | ✅ | 触发 2 次 CI；在分支上制造过一次失败并下载了 junit artifact`

## 验收清单

- [ ] 自己的 push 触发过一次 run
- [ ] 下载并打开过 artifact
- [ ] 在分支上红过一次，并知道报告里怎么看
- [ ] 能解释 `if: always()` 和 `concurrency`

## 面试口径

> 这个仓库的 CI 分三个 job：单测（含一个离线 ReAct demo）、Playwright E2E、可选的 AI E2E。
> 拆开是因为浏览器安装最慢，不该拖累单测的反馈速度。
> 两个细节我特意做了：上传报告用 `if: always()`，失败也能拿到 junit 和报告；
> 可选任务用仓库变量 `ENABLE_MIDSCENE` 做开关——因为 GitHub 的 job 级 `if` 读不到 secrets，
> 这是踩过才知道的坑。

## 卡住了怎么办

| 现象 | 原因 | 处理 |
| --- | --- | --- |
| push 后没有 run | 推到非 main 且没有 PR | 开 PR，或用 `workflow_dispatch` 手动触发 |
| `refusing to allow a Personal Access Token ... workflow` | PAT 缺 workflow scope | 用 SSH 推送，或给 token 补 scope |
| artifact 404 | 步骤没执行（前面失败了） | 看是不是 `if: always()` 被删了 |
| midscene job 一直 skipped | 变量没开 | 仓库 Settings → Variables 设 `ENABLE_MIDSCENE=true` |
