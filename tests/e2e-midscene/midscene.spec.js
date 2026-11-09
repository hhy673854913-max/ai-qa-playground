// @ts-check
/**
 * Midscene.js：用自然语言驱动页面，不写选择器。
 *
 * 对比同目录上层的 tests/e2e/game.spec.js —— 那边是「我知道按钮叫什么，直接点」，
 * 这边是「让模型看图找按钮」。两者的取舍写在 docs/ai-ui-automation.md。
 *
 * 运行前需要配置多模态模型（见本目录 README.md）：
 *   export MIDSCENE_OPENAI_API_KEY=sk-...
 *   npm install && npx playwright install chromium
 *   npm run test:midscene
 */
const { test, expect } = require('@playwright/test');
const { PlaywrightAgent } = require('@midscene/web/playwright');

// 没配 Key 就整体跳过：既不会红一片，也不会假装跑过了
const hasModel = Boolean(process.env.MIDSCENE_OPENAI_API_KEY || process.env.OPENAI_API_KEY);

test.describe('Midscene：自然语言驱动抽奖', () => {
  test.skip(!hasModel, '缺少多模态模型 API Key，跳过 Midscene 用例（配置方式见 README）');

  test('说人话完成一次抽奖，并让模型自己断言结果', async ({ page }) => {
    await page.goto('/?seed=7&player=ai-qa');
    const agent = new PlaywrightAgent(page);

    // 1. 自然语言操作：不出现任何选择器
    await agent.aiAction('点击页面中间那个写着「抽一次」的按钮');

    // 2. 自然语言断言：模型看截图判断页面状态
    await agent.aiAssert('页面上方出现了一个奖品名称，并且「已抽」后面的数字是 1');

    // 3. 结构化抽取：把页面信息变成 JSON，方便继续断言 / 落库
    const result = await agent.aiQuery(
      '{ prizeName: string, drawCount: string }, 当前展示的奖品名称，以及已经抽了几次'
    );
    console.log('[midscene] aiQuery 结果:', JSON.stringify(result, null, 2));

    expect(String(result.drawCount)).toContain('1');
  });

  test('用自然语言验证排行榜面板存在', async ({ page }) => {
    await page.goto('/?seed=7&player=ai-qa');
    const agent = new PlaywrightAgent(page);

    await agent.aiAction('点击「抽一次」按钮');
    await agent.aiAssert('右侧或下方有一个「排行榜」，且里面出现了玩家 ai-qa');
  });
});
