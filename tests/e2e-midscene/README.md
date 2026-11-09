# Midscene 用例（AI 驱动的 UI 自动化）

同一个抽奖页，换一种写法：**不写选择器，用自然语言操作和断言**。

```bash
cd tests/e2e-midscene
npm install
npx playwright install chromium

# 配置多模态模型（任选其一，变量名以 Midscene 官方文档为准）
export MIDSCENE_OPENAI_API_KEY=sk-xxx
export MIDSCENE_MODEL_NAME=gpt-4o          # 可选，默认值见官方文档

npm run test:midscene
```

Windows PowerShell：

```powershell
$env:MIDSCENE_OPENAI_API_KEY="sk-xxx"
npm run test:midscene
```

## 说明：这部分没有在离线环境验证

本仓库作者在**无外网、无 API Key** 的环境里搭的这套 demo，所以：

- 主套件（`tests/e2e`，传统 Playwright）是实跑验证过的；
- 本目录的代码按 Midscene 官方示例编写，**没有真实跑过**，`npm install` 后如果 API 有出入，
  以 [Midscene 文档](https://midscenejs.com/) 为准（它迭代很快，`aiAction/aiQuery/aiAssert` 之外的方法名可能变化）；
- `package.json` 里 `@midscene/web` 用的是 `latest`，第一次装完请把版本锁进 `package-lock.json` 并提交，
  否则半年后别人 clone 下来跑的是另一个版本。

跑通之后建议做一件小事：把 `aiAction` 的截图存进报告附件。AI 自动化最大的排障成本是
「它当时到底看到了什么」，留下截图能让复盘从 30 分钟降到 3 分钟。
