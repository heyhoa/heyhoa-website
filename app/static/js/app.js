// hey hoa — shared behaviour (vanilla, no jQuery)
(function () {
  // mobile nav
  var toggle = document.querySelector('.nav-toggle');
  if (toggle) {
    toggle.addEventListener('click', function () {
      var ul = document.querySelector('.nav ul');
      ul.classList.toggle('open');
      toggle.setAttribute('aria-expanded', ul.classList.contains('open'));
    });
  }

  // multistep forms
  document.querySelectorAll('form.multistep').forEach(function (form) {
    var sets = Array.prototype.slice.call(form.querySelectorAll('fieldset'));
    var i = 0;
    function show(n) {
      sets.forEach(function (fs, idx) { fs.style.display = idx === n ? 'block' : 'none'; });
      i = n;
      var prog = form.querySelector('progress');
      if (prog) prog.value = Math.round(((n) / sets.length) * 100);
      var lbl = form.querySelector('.step-label');
      if (lbl) lbl.textContent = 'Step ' + (n + 1) + ' of ' + sets.length;
      window.scrollTo({ top: form.getBoundingClientRect().top + window.scrollY - 80, behavior: 'smooth' });
    }
    form.addEventListener('click', function (e) {
      var t = e.target.closest('.next, .previous');
      if (!t) return;
      e.preventDefault();
      if (t.classList.contains('next')) {
        var ok = true;
        sets[i].querySelectorAll('input, select, textarea').forEach(function (el) {
          if (!el.checkValidity()) { ok = false; el.reportValidity(); }
        });
        if (ok && i < sets.length - 1) show(i + 1);
      } else if (i > 0) {
        show(i - 1);
      }
    });
    show(0);
  });

  // remember partially-entered forms (per form id)
  document.querySelectorAll('form[data-remember]').forEach(function (form) {
    var key = 'hey:form:' + (form.id || location.pathname);
    try {
      var saved = JSON.parse(localStorage.getItem(key) || 'null');
      if (saved) Object.keys(saved).forEach(function (k) {
        var el = form.elements[k];
        if (el && el.type !== 'checkbox' && el.type !== 'radio' && el.type !== 'file') el.value = saved[k];
      });
    } catch (e) {}
    form.addEventListener('input', function () {
      var data = {};
      Array.prototype.forEach.call(form.elements, function (el) {
        if (el.name && el.type !== 'file' && el.type !== 'password') data[el.name] = el.value;
      });
      try { localStorage.setItem(key, JSON.stringify(data)); } catch (e) {}
    });
    form.addEventListener('submit', function () { try { localStorage.removeItem(key); } catch (e) {} });
  });

  // drag & drop upload areas
  document.querySelectorAll('.drag-drop-container').forEach(function (box) {
    var input = box.querySelector('input[type=file]');
    var info = box.parentElement.querySelector('.drag-drop-files');
    function list(files) {
      if (!info) return;
      info.innerHTML = '';
      Array.prototype.forEach.call(files, function (f) {
        var d = document.createElement('div');
        d.textContent = f.name + ' (' + Math.round(f.size / 1024) + ' KB)';
        info.appendChild(d);
      });
    }
    box.addEventListener('click', function () { input && input.click(); });
    box.addEventListener('dragover', function (e) { e.preventDefault(); box.classList.add('dragover'); });
    box.addEventListener('dragleave', function () { box.classList.remove('dragover'); });
    box.addEventListener('drop', function (e) {
      e.preventDefault(); box.classList.remove('dragover');
      if (input) { input.files = e.dataTransfer.files; list(input.files); }
    });
    if (input) input.addEventListener('change', function () { list(input.files); });
  });

  // demo "ask hey" chat (no network when no API key; server returns demo text)
  var chat = document.querySelector('[data-ask-hey]');
  if (chat) {
    var form = chat.querySelector('form');
    var log = chat.querySelector('.chat');
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var q = form.q.value.trim();
      if (!q) return;
      add('us', 'you', q);
      form.q.value = '';
      fetch(form.action, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ q: q, context: chat.dataset.askHey }) })
        .then(function (r) { return r.json(); })
        .then(function (d) { add('them', 'hey', d.answer); })
        .catch(function () { add('them', 'hey', 'Something went wrong. Try again in a moment.'); });
    });
    function add(side, who, text) {
      var b = document.createElement('div');
      b.className = 'bubble ' + side;
      var w = document.createElement('span'); w.className = 'who'; w.textContent = who;
      b.appendChild(w); b.appendChild(document.createTextNode(text));
      log.appendChild(b);
      log.scrollTop = log.scrollHeight;
    }
  }
})();
