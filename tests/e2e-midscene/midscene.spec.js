// @ts-check
/**
 * Midscene.js：用自然语言驱动页面，不写选择器。
 *
 * 对比上层 tests/e2e/game.spec.js —— 那边是「我知道按钮叫什么，直接点」，
 * 这边是「让模型看图找按钮」。两者的取舍写在 docs/ai-ui-automation.md。
 *
 * 实测配置（阿里云百炼 DashScope，qwen3-vl 系列）：
 *   MIDSCENE_MODEL_API_KEY=sk-...
 *   MIDSCENE_MODEL_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
 *   MIDSCENE_MODEL_NAME=qwen3-vl-plus
 *   MIDSCENE_MODEL_FAMILY=qwen3-vl
 *
 * 一条命令跑：
 *   powershell -File run-local.ps1 -KeyFile ..\..\..\.key
 * 或在已设好上述环境变量时：npm run test:midscene
 */
const { test, expect } = require('@playwright/test');
const { PlaywrightAgent } = require('@midscene/web/playwright');

// 没配 Key 就整体跳过：既不会红一片，也不会假装跑过了
const hasModel = Boolean(
  process.env.MIDSCENE_MODEL_API_KEY || process.env.MIDSCENE_OPENAI_API_KEY || process.env.OPENAI_API_KEY
);

test.describe('Midscene：自然语言驱动抽奖', () => {
  test.skip(!hasModel, '缺少多模态模型 API Key（MIDSCENE_MODEL_API_KEY），跳过 Midscene 用例');

  test('说人话完成一次抽奖，并让模型自己断言结果', async ({ page }, testInfo) => {
    await page.goto('/?seed=7&player=ai-qa');
    const agent = new PlaywrightAgent(page);

    // 1. 自然语言操作：全程没有选择器
    await agent.aiAct('点击页面中间那个写着「抽一次」的按钮');

    // 2. 自然语言断言：模型看截图判断页面状态
    await agent.aiAssert('页面上出现了一个奖品名称，并且「已抽」后面的数字是 1');

    // 3. 结构化抽取：把「看到的东西」变成 JSON，方便继续做强断言
    const result = await agent.aiQuery(
      '{ prizeName: string, drawCount: string }, 当前展示的奖品名称，以及已经抽了几次'
    );
    console.log('[midscene] aiQuery 结果:', JSON.stringify(result));

    expect(String(result.drawCount)).toContain('1');
    expect(result.prizeName.length).toBeGreaterThan(0);

    const shot = testInfo.outputPath('midscene-after-draw.png');
    await page.screenshot({ path: shot, fullPage: true });
    await testInfo.attach('Midscene 抽奖后页面', { path: shot, contentType: 'image/png' });
  });

  test('用自然语言验证排行榜里出现了自己', async ({ page }) => {
    await page.goto('/?seed=7&player=ai-qa');
    const agent = new PlaywrightAgent(page);

    await agent.aiAct('点击「抽一次」按钮');
    await agent.aiAssert('页面上有一个「排行榜」区域，并且里面出现了玩家 ai-qa');
  });
});
