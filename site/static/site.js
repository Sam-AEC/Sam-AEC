(function () {
  // Copy buttons
  document.querySelectorAll('[data-copy]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var code = btn.parentElement.querySelector('code');
      var done = function () { var t = btn.textContent; btn.textContent = 'Copied'; setTimeout(function () { btn.textContent = t; }, 1500); };
      if (navigator.clipboard) { navigator.clipboard.writeText(code.textContent).then(done, function () {}); }
    });
  });
  // Tool catalogue filter (pure DOM, no network)
  var q = document.getElementById('q'); if (!q) return;
  var fp = document.getElementById('f-provider'), fk = document.getElementById('f-kind');
  var tools = Array.prototype.slice.call(document.querySelectorAll('details.tool'));
  var groups = Array.prototype.slice.call(document.querySelectorAll('[data-provider-group]'));
  var out = document.getElementById('result-count');
  function apply() {
    var term = q.value.trim().toLowerCase(), n = 0;
    tools.forEach(function (t) {
      var ok = (!term || t.dataset.text.indexOf(term) > -1) && (!fp.value || t.dataset.provider === fp.value) && (!fk.value || t.dataset.kind === fk.value);
      t.hidden = !ok; if (ok) n++;
    });
    groups.forEach(function (g) { g.hidden = !g.querySelector('details.tool:not([hidden])'); });
    out.textContent = 'Showing ' + n + ' of ' + tools.length + ' tools.';
  }
  [q, fp, fk].forEach(function (el) { el.addEventListener('input', apply); el.addEventListener('change', apply); });
  // Deep links: open the targeted tool
  function openHash() { var el = location.hash && document.getElementById(location.hash.slice(1)); if (el && el.tagName === 'DETAILS') { el.open = true; el.hidden = false; el.scrollIntoView(); } }
  window.addEventListener('hashchange', openHash); openHash();
})();
