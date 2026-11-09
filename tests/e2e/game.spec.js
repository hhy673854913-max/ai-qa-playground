// @ts-check
/**
 * 抽奖页 E2E：点击 → 断言 → 截图。
 *
 * 选择器原则（面试常问「怎么让用例不脆」）：
 *   优先 getByRole / getByText（贴着用户能看到的东西），其次 data-* 属性，
 *   最后才是 CSS 类。class 是给样式用的，改个皮肤就全红，不值得为它写死。
 */
const { test, expect } = require('@playwright/test');

const SEED = 7;
const PLAYER = 'qa-bot';

/** 点一次抽奖，等结果渲染完，返回奖品 id */
async function drawAndReadPrize(page) {
  const prize = page.locator('#prize-name');
  await page.getByRole('button', { name: '抽一次' }).click();
  await expect(prize).not.toHaveText('准备好了吗？');
  await expect(prize).toHaveAttribute('data-prize', /.+/);
  return prize.getAttribute('data-prize');
}

test.describe('抽奖页', () => {
  test.beforeEach(async ({ page, request }) => {
    // 被测服务是有状态的（排行榜），串行 + 每例重置，断言才稳定
    await request.post('/api/reset');
    await page.goto(`/?seed=${SEED}&player=${PLAYER}`);
  });

  test('首屏渲染：标题、按钮、空历史 @smoke', async ({ page }) => {
    await expect(page.getByRole('heading', { name: '幸运抽奖机' })).toBeVisible();
    await expect(page.getByRole('button', { name: '抽一次' })).toBeEnabled();
    await expect(page.getByText('还没有记录，先抽一次吧')).toBeVisible();
    await expect(page.locator('#seed-label')).toHaveText(String(SEED));
    await expect(page.locator('#player-badge')).toHaveText(PLAYER);
  });

  test('点击抽奖：奖品、计数、历史、上榜，并留存截图 @smoke', async ({ page }, testInfo) => {
    await page.getByRole('button', { name: '抽一次' }).click();

    // 1. 结果区出现具体奖品（不是「中了某一个」这种废话断言）
    await expect(page.locator('#prize-name')).toHaveAttribute('data-prize', /.+/);
    await expect(page.locator('#prize-meta')).toContainText('分');

    // 2. 计数与历史
    await expect(page.locator('#draw-count')).toHaveText('1');
    await expect(page.locator('#history li')).toHaveCount(1);
    await expect(page.locator('#history li').first()).toContainText('#1');

    // 3. 排行榜出现自己
    await expect(page.locator(`#leaderboard li[data-player="${PLAYER}"]`)).toBeVisible();

    // 4. 截图：既落盘，也挂到 HTML 报告的附件里
    const shot = testInfo.outputPath('after-draw.png');
    await page.screenshot({ path: shot, fullPage: true });
    await testInfo.attach('抽奖结果', { path: shot, contentType: 'image/png' });
  });

  test('同一 seed 的抽奖结果可复现', async ({ page }) => {
    const first = await drawAndReadPrize(page);

    await page.reload();
    const second = await drawAndReadPrize(page);

    expect(second, '同一 seed 下第一次抽奖结果应完全一致').toBe(first);
  });

  test('连抽三次：历史三条、奖品都来自奖池', async ({ page, request }) => {
    const odds = await (await request.get('/api/odds')).json();
    const validIds = new Set(odds.items.map((item) => item.id));

    const drawn = [];
    for (let i = 0; i < 3; i += 1) {
      drawn.push(await drawAndReadPrize(page));
    }

    await expect(page.locator('#history li')).toHaveCount(3);
    await expect(page.locator('#draw-count')).toHaveText('3');
    for (const id of drawn) expect(validIds.has(id), `意外的奖品 id: ${id}`).toBeTruthy();

    // 按钮在动画结束后必须恢复可用，否则用户只能抽一次
    await expect(page.getByRole('button', { name: '抽一次' })).toBeEnabled();
  });

  test('排行榜按分数降序，且与接口一致', async ({ page, request }) => {
    // 通过接口造数：比在 UI 上点几十次快得多，也不受动画时长影响
    const players = ['bronze', 'silver', 'gold'];
    for (const [i, player] of players.entries()) {
      const resp = await request.post('/api/draw', { data: { player, seed: 99, index: i } });
      expect(resp.ok()).toBeTruthy();
    }

    const board = await (await request.get('/api/leaderboard?limit=5')).json();
    const scores = board.items.map((item) => item.score);
    expect(scores).toEqual([...scores].sort((a, b) => b - a));

    await page.reload();
    const rows = page.locator('#leaderboard li');
    await expect(rows).toHaveCount(board.items.length);
    for (const [i, item] of board.items.entries()) {
      await expect(rows.nth(i)).toContainText(item.player);
      await expect(rows.nth(i)).toContainText(String(item.score));
    }
  });

  test('奖池概率展示：四条奖品，合计 100%', async ({ page }) => {
    const items = page.locator('#odds li');
    await expect(items).toHaveCount(4);

    const text = await items.allInnerTexts();
    const total = text.reduce((sum, line) => sum + Number.parseFloat(line.split('%')[0].replace(/[^\d.]/g, '') || '0'), 0);
    expect(Math.abs(total - 100)).toBeLessThan(0.5);
  });
});
