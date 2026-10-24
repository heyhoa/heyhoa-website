// hey portal: list + drawer, keyboard, bulk select. No framework.
(function () {
  const rows = () => Array.from(document.querySelectorAll('table.data tbody tr[data-drawer]'));
  const drawers = () => Array.from(document.querySelectorAll('.drawer'));
  let current = null;

  function closeAll() {
    drawers().forEach(d => d.classList.remove('open'));
    rows().forEach(r => r.classList.remove('selected'));
    document.body.classList.remove('drawer-open');
    current = null;
  }
  function open(id) {
    const d = document.getElementById(id);
    if (!d) return;
    closeAll();
    d.classList.add('open');
    document.body.classList.add('drawer-open');
    const row = rows().find(r => r.dataset.drawer === id);
    if (row) { row.classList.add('selected'); row.scrollIntoView({ block: 'nearest' }); current = row; }
    const first = d.querySelector('textarea, input[type=text]:not([type=hidden]), input:not([type=hidden]):not([type=checkbox])');
    if (first && d.dataset.autofocus === '1') first.focus();
    if (history.replaceState) history.replaceState(null, '', '#' + id);
  }
  function move(delta) {
    const list = rows();
    if (!list.length) return;
    let i = current ? list.indexOf(current) : -1;
    i = Math.min(list.length - 1, Math.max(0, i + delta));
    open(list[i].dataset.drawer);
  }

  document.addEventListener('click', e => {
    const t = e.target;
    if (t.closest('[data-open]')) { e.preventDefault(); open(t.closest('[data-open]').dataset.open); return; }
    if (t.closest('.drawer-close') || t.classList.contains('drawer-backdrop')) { closeAll(); return; }
    const row = t.closest('table.data tbody tr[data-drawer]');
    if (row && !t.closest('a, button, input, select, label, form')) open(row.dataset.drawer);
  });

  document.addEventListener('keydown', e => {
    const typing = /^(INPUT|TEXTAREA|SELECT)$/.test(document.activeElement.tagName);
    if (e.key === 'Escape') { if (typing) { document.activeElement.blur(); } else { closeAll(); } return; }
    if (typing || e.metaKey || e.ctrlKey || e.altKey) return;
    if (e.key === 'j' || e.key === 'ArrowDown') { e.preventDefault(); move(1); return; }
    if (e.key === 'k' || e.key === 'ArrowUp') { e.preventDefault(); move(-1); return; }
    if (e.key === 'Enter' && current) { open(current.dataset.drawer); return; }
    const d = document.querySelector('.drawer.open');
    if (!d) return;
    const btn = d.querySelector('[data-key="' + e.key + '"]');
    if (btn) { e.preventDefault(); btn.click(); }
  });

  // bulk selection
  function refreshBulk() {
    const bar = document.querySelector('.bulkbar');
    if (!bar) return;
    const checked = Array.from(document.querySelectorAll('.rowcheck:checked'));
    const sum = checked.reduce((s, c) => s + parseFloat(c.dataset.amount || 0), 0);
    bar.classList.toggle('show', checked.length > 0);
    bar.querySelector('.bulk-count').textContent = checked.length;
    const sumEl = bar.querySelector('.bulk-sum');
    if (sumEl) sumEl.textContent = sum.toLocaleString('en-US', { style: 'currency', currency: 'USD' });
    bar.querySelectorAll('input[name=ids]').forEach(i => i.remove());
    checked.forEach(c => { const h = document.createElement('input'); h.type = 'hidden'; h.name = 'ids'; h.value = c.value; bar.querySelector('form').appendChild(h); });
  }
  document.addEventListener('change', e => {
    if (e.target.classList.contains('rowcheck')) refreshBulk();
    if (e.target.classList.contains('checkall')) { document.querySelectorAll('.rowcheck').forEach(c => { c.checked = e.target.checked; }); refreshBulk(); }
  });

  // page-aware ask hey
  document.addEventListener('submit', e => {
    const form = e.target.closest('.ask-form');
    if (!form) return;
    e.preventDefault();
    const log = form.closest('.drawer-body').querySelector('.ask-log');
    const q = form.q.value.trim();
    if (!q) return;
    const add = (who, text) => { const b = document.createElement('div'); b.className = 'bubble ' + (who === 'you' ? 'me' : 'them'); b.innerHTML = '<span class="who">' + who + '</span>'; b.appendChild(document.createTextNode(text)); log.appendChild(b); log.scrollTop = log.scrollHeight; return b; };
    add('you', q); form.q.value = '';
    const wait = add('hey', '…');
    fetch(form.action, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ q: q, context: form.dataset.context }) })
      .then(r => r.json()).then(j => { wait.lastChild.textContent = j.answer || j.error || 'No answer.'; })
      .catch(() => { wait.lastChild.textContent = 'Could not reach hey. Try again.'; });
  });

  if (location.hash && document.getElementById(location.hash.slice(1))) open(location.hash.slice(1));
})();
