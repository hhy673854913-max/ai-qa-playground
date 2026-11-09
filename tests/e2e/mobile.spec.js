// @ts-check
/**
 * 移动端（H5）用例。
 * 同一个 spec 会在两个 project 里各跑一遍，这里用 isMobile 只让移动端 project 真正执行，
 * 桌面端自动 skip —— 这样「一条用例覆盖多端」而不用复制文件。
 */
const { test, expect } = require('@playwright/test');

test.describe('移动端适配', () => {
  test('手机视口下抽奖按钮可见可点，布局不横向溢出', async ({ page, isMobile }, testInfo) => {
    test.skip(!isMobile, '仅在移动端 project 运行');

    await page.goto('/?seed=11&player=mobile-qa');

    const button = page.getByRole('button', { name: '抽一次' });
    await expect(button).toBeVisible();

    // 横向溢出是 H5 最常见的低级事故：断言 scrollWidth 不超过视觉视口
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    expect(overflow).toBeLessThanOrEqual(1);

    await button.click();
    await expect(page.locator('#draw-count')).toHaveText('1');

    const shot = testInfo.outputPath('mobile-after-draw.png');
    await page.screenshot({ path: shot, fullPage: true });
    await testInfo.attach('移动端抽奖', { path: shot, contentType: 'image/png' });
  });
});
