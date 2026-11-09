/* 页面交互层：只负责「调接口 + 渲染状态」，不实现业务规则。
   抽奖概率与排序规则都在 Python 侧（game/core.py），这样 pytest 能直接测，
   也能保证 E2E 测到的是真业务，而不是前端自己编的一套。 */

(function () {
  const params = new URLSearchParams(location.search);

  // seed 决定抽奖序列：同一个 seed 必然得到同一串奖品，E2E 才能断言具体结果
  const seedParam = params.get('seed');
  const seed = seedParam !== null && /^-?\d+$/.test(seedParam) ? Number(seedParam) : Math.floor(Math.random() * 100000);
  const player = (params.get('player') || 'guest').slice(0, 24);

  let index = 0;
  let busy = false;

  const $ = (id) => document.getElementById(id);
  const els = {
    badge: $('player-badge'),
    orb: $('orb'),
    prizeName: $('prize-name'),
    prizeMeta: $('prize-meta'),
    button: $('draw-btn'),
    count: $('draw-count'),
    history: $('history'),
    leaderboard: $('leaderboard'),
    odds: $('odds'),
    seed: $('seed-label')
  };

  const RARITY = {
    legendary: '传说',
    epic: '史诗',
    rare: '稀有',
    common: '普通'
  };

  function renderPrize(prize) {
    els.prizeName.textContent = prize.name;
    els.prizeName.dataset.prize = prize.id;
    els.prizeMeta.textContent = `${RARITY[prize.id] || '奖品'} · +${prize.points} 分`;
  }

  function pushHistory(prize, seq) {
    if (els.history.querySelector('.empty')) els.history.innerHTML = '';
    const li = document.createElement('li');
    li.dataset.prize = prize.id;
    li.dataset.seq = String(seq);
    li.innerHTML =
      `<span class="name">${prize.name}</span>` +
      `<span class="pts">+${prize.points} 分</span>` +
      `<span class="time">#${seq}</span>`;
    els.history.prepend(li);
    while (els.history.children.length > 5) els.history.lastElementChild.remove();
  }

  function renderLeaderboard(items) {
    if (!items.length) {
      els.leaderboard.innerHTML = '<li class="empty">暂无上榜玩家</li>';
      return;
    }
    els.leaderboard.innerHTML = items
      .map(
        (item, i) =>
          `<li data-player="${item.player}">` +
          `<span class="rank">${i + 1}</span>` +
          `<span class="name">${item.player}</span>` +
          `<span class="score">${item.score}</span>` +
          `</li>`
      )
      .join('');
  }

  async function getJSON(url, options) {
    const res = await fetch(url, options);
    const data = await res.json();
    if (!res.ok) throw new Error(data.message || `HTTP ${res.status}`);
    return data;
  }

  async function refreshLeaderboard() {
    try {
      const data = await getJSON('/api/leaderboard?limit=5');
      renderLeaderboard(data.items);
    } catch (err) {
      els.leaderboard.innerHTML = `<li class="empty">加载失败：${err.message}</li>`;
    }
  }

  async function refreshOdds() {
    try {
      const data = await getJSON('/api/odds');
      els.odds.innerHTML = data.items
        .map((item) => `<li><span>${item.name}</span><span class="prob">${item.probability}%</span></li>`)
        .join('');
    } catch (err) {
      els.odds.innerHTML = `<li class="empty">加载失败：${err.message}</li>`;
    }
  }

  async function drawOnce() {
    if (busy) return;
    busy = true;
    els.button.disabled = true;
    els.orb.classList.add('spinning');

    try {
      const data = await getJSON('/api/draw', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ player, seed, index })
      });

      index += 1;
      els.count.textContent = String(index);
      renderPrize(data.prize);
      pushHistory(data.prize, index);
      await refreshLeaderboard();
    } catch (err) {
      els.prizeName.textContent = '抽奖失败';
      els.prizeMeta.textContent = err.message;
    } finally {
      // 留一点点动画时间，用户能感知到「抽」这个动作
      setTimeout(() => {
        busy = false;
        els.button.disabled = false;
        els.orb.classList.remove('spinning');
      }, 360);
    }
  }

  els.badge.textContent = player;
  els.seed.textContent = String(seed);
  els.button.addEventListener('click', drawOnce);

  refreshOdds();
  refreshLeaderboard();
})();
