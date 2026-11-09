// @ts-check
/**
 * Midscene 用例独立跑：自己的 package.json / 自己的端口，主 Playwright 套件不装它。
 * 原因很实际 —— 它依赖多模态模型和 API Key，不该把整个 CI 卡在这里。
 */
const { defineConfig, devices } = require('@playwright/test');

const PORT = Number(process.env.GAME_PORT || 8200);
const PYTHON = process.env.GAME_PYTHON || 'python';

module.exports = defineConfig({
  testDir: '.',
  testMatch: '**/*.spec.js',
  timeout: 120_000, // 每次 aiAction 都要等模型返回，比传统用例慢一个量级
  reporter: [['list'], ['html', { outputFolder: 'reports/midscene', open: 'never' }]],
  use: {
    baseURL: `http://127.0.0.1:${PORT}`,
    trace: 'on-first-retry',
    screenshot: 'only-on-failure'
  },
  projects: [{ name: 'midscene-chromium', use: { ...devices['Desktop Chrome'] } }],
  webServer: {
    command: `${PYTHON} -m game.server --port ${PORT}`,
    url: `http://127.0.0.1:${PORT}/health`,
    cwd: '../..',
    reuseExistingServer: true,
    timeout: 30_000
  }
});
