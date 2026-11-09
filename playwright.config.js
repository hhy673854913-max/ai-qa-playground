// @ts-check
/**
 * Playwright 配置。
 *
 * 两个关键设计：
 *  1. webServer：测试自己拉被测服务，`npm run test:e2e` 一条命令就够，
 *     不依赖「先手动启动服务」这种口头约定。url 是 /health，服务没起完不会开始跑用例。
 *  2. 失败留证：trace + screenshot + video 只在失败时保留，报告里能直接回放现场。
 */
const { defineConfig, devices } = require('@playwright/test');

const PORT = Number(process.env.GAME_PORT || 8100);
const PYTHON = process.env.GAME_PYTHON || 'python';

module.exports = defineConfig({
  testDir: './tests/e2e',
  testMatch: '**/*.spec.js',
  // 这里刻意串行：所有 worker 共享同一个有状态的被测服务（排行榜），
  // 并行跑会互相污染数据。真实项目应该给每个 worker 一套独立环境
  // （独立 DB schema / 独立容器 / 独立测试账号），而不是靠「重置接口」硬扛。
  fullyParallel: false,
  workers: 1,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  timeout: 30_000,
  expect: { timeout: 5_000 },

  reporter: [
    ['list'],
    ['html', { outputFolder: 'reports/playwright', open: 'never' }],
    ['junit', { outputFile: 'reports/playwright-junit.xml' }]
  ],

  use: {
    baseURL: `http://127.0.0.1:${PORT}`,
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    actionTimeout: 10_000
  },

  projects: [
    {
      name: 'desktop-chromium',
      use: { ...devices['Desktop Chrome'] }
    },
    {
      name: 'mobile-chromium',
      use: { ...devices['Pixel 7'] }
    }
  ],

  webServer: {
    command: `${PYTHON} -m game.server --port ${PORT}`,
    url: `http://127.0.0.1:${PORT}/health`,
    cwd: __dirname,
    reuseExistingServer: !process.env.CI,
    timeout: 30_000,
    stdout: 'ignore',
    stderr: 'pipe'
  }
});
