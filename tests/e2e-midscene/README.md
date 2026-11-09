# Midscene 用例（AI 驱动的 UI 自动化）

同一个抽奖页，换一种写法：**不写选择器，用自然语言操作和断言**。

```js
const agent = new PlaywrightAgent(page);
await agent.aiAct('点击页面中间那个写着「抽一次」的按钮');
await agent.aiAssert('页面上出现了一个奖品名称，并且「已抽」后面的数字是 1');
const result = await agent.aiQuery('{ prizeName: string, drawCount: string }, 当前奖品与已抽次数');
// => { prizeName: '再来一次', drawCount: '1' }
```

## 跑起来（实测通过）

```powershell
cd tests/e2e-midscene
npm ci
npx playwright install chromium          # 浏览器装在本包 node_modules 里，和根套件互不干扰

# 把你的多模态 Key 放进一个文件（例如仓库外的 ../../../.key），然后：
powershell -File run-local.ps1 -KeyFile ..\..\..\.key
```

`run-local.ps1` 只做一件事：把 Key 读进环境变量再启动 Playwright —— **Key 不落盘、不进仓库、不打印**。

等价的手动方式：

```powershell
$env:MIDSCENE_MODEL_API_KEY = (Get-Content ..\..\..\.key -Raw).Trim()
$env:MIDSCENE_MODEL_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
$env:MIDSCENE_MODEL_NAME = "qwen3-vl-plus"
$env:MIDSCENE_MODEL_FAMILY = "qwen3-vl"
$env:PLAYWRIGHT_BROWSERS_PATH = "0"
npm run test:midscene
```

## 实测配置与结果

| 项 | 值 |
| --- | --- |
| Midscene | `@midscene/web` 1.17.7 |
| 模型 | 阿里云百炼 `qwen3-vl-plus`（OpenAI 兼容模式） |
| family | `qwen3-vl` |
| 结果 | **2 passed**：13.8s / 10.3s（每条含 2~3 次模型调用） |
| 产出 | `midscene_run/report/*.html`（含每步截图与模型原始响应） |

单次 `aiAct` 约 4~6 秒，比传统脚本慢 5 倍以上 —— 但改版时你改的是一句中文，不是 20 行选择器。
这个取舍写在 [../../docs/ai-ui-automation.md](../../docs/ai-ui-automation.md)。

## 踩过的坑（都是真实的）

| 现象 | 原因 | 处理 |
| --- | --- | --- |
| `Model not exist` | 账号里没有 `qwen-vl-max`，模型目录是 `qwen3-vl-plus` 这一代 | 先 `GET /models` 列一下再选模型 |
| `Executable doesn't exist` | 浏览器装在根套件的 `node_modules`，本包找不到 | 在**本目录**执行 `npx playwright install chromium`，并设 `PLAYWRIGHT_BROWSERS_PATH=0` |
| `aiAction` 有 deprecated 提示 | 1.17 起改名 `aiAct` | 用 `aiAct`，旧名还能跑但会持续告警 |
| 点击后拿到旧值 | 页面动画/请求还没结束就断言 | 断言用 `aiAssert`（内部会重试），取值用 `aiQuery` 并在其后执行 |

## 环境变量

| 变量 | 说明 |
| --- | --- |
| `MIDSCENE_MODEL_API_KEY` | 模型 Key（必填，没有就整组 skip） |
| `MIDSCENE_MODEL_BASE_URL` | OpenAI 兼容入口，默认 `https://dashscope.aliyuncs.com/compatible-mode/v1` |
| `MIDSCENE_MODEL_NAME` | 模型名，实测 `qwen3-vl-plus` |
| `MIDSCENE_MODEL_FAMILY` | 解析坐标用的适配器族：`qwen3-vl` / `qwen2.5-vl` / `gemini` / `doubao-vision` / `vlm-ui-tars` |
| `PLAYWRIGHT_BROWSERS_PATH` | `0` 表示用本包内的浏览器 |

## 产物不看会后悔

`midscene_run/report/*.html` 是 Midscene 自己的报告：每一步的截图、模型输入输出、耗时全在里面。
AI 自动化的排障成本主要花在「它当时到底看到了什么」，这份报告就是答案。
