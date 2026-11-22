// メニューの開閉（スマホ）
(function () {
  const btn = document.querySelector('.menu-btn');
  if (!btn) return;
  btn.addEventListener('click', () => {
    const open = btn.getAttribute('aria-expanded') !== 'true';
    btn.setAttribute('aria-expanded', String(open));
    document.body.classList.toggle('nav-open', open);
  });
})();

// お知らせの表示（assets/news-data.js の内容を読む）
(function () {
  const LABEL = { info: 'お知らせ', recruit: '募集', report: '活動報告' };
  const fmt = d => d.replace(/^(\d{4})-(\d{2})-(\d{2})$/, (_, y, m, day) => `${y}年${+m}月${+day}日`);
  const esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const news = (window.NEWS || []).slice().sort((a, b) => b.date.localeCompare(a.date));
  const tag = cat => `<span class="tag ${cat}">${LABEL[cat] || ''}</span>`;

  // トップ：最新5件。見出しを押すと一覧ページの該当記事へ
  const latest = document.getElementById('news-latest');
  if (latest) {
    latest.innerHTML = news.slice(0, 5).map(n =>
      `<li><div class="news-row"><time datetime="${n.date}">${fmt(n.date)}</time>${tag(n.cat)}<a class="title" href="news.html#n-${n.date}">${esc(n.title)}</a></div></li>`
    ).join('');
  }

  // 一覧ページ：年ごと・種類で絞り込み・開いて本文を読む
  const box = document.getElementById('news-all');
  if (!box) return;
  const render = cat => {
    const list = news.filter(n => cat === 'all' || n.cat === cat);
    let html = '', year = '';
    list.forEach(n => {
      const y = n.date.slice(0, 4);
      if (y !== year) { if (year) html += '</ul>'; html += `<h2 class="year">${y}年</h2><ul class="news-list">`; year = y; }
      const body = esc(n.body).split('\n').map(l => `<p>${l}</p>`).join('');
      html += `<li id="n-${n.date}"><details><summary class="news-row"><time datetime="${n.date}">${fmt(n.date)}</time>${tag(n.cat)}<span class="title">${esc(n.title)}</span></summary><div class="news-body prose">${body}</div></details></li>`;
    });
    box.innerHTML = list.length ? html + '</ul>' : '<p>該当するお知らせはありません。</p>';
    const target = location.hash && document.getElementById(location.hash.slice(1));
    if (target) { target.querySelector('details').open = true; target.scrollIntoView(); }
  };
  document.querySelectorAll('.filter button').forEach(b => b.addEventListener('click', () => {
    document.querySelectorAll('.filter button').forEach(x => x.setAttribute('aria-pressed', String(x === b)));
    render(b.dataset.cat);
  }));
  render('all');
})();
