// Mock side of the live-viewer contract (explore-design live-viewer template).
// Load after shared/viewer-config.js and shared/options-sheet.js, as classic scripts, then call
//   MockLive.init({ apply: { accent: (v) => { ... }, menu: (v) => { ... } } });
// Every applied key is mirrored first on <html data-KEY="value">, so CSS can style from it and
// the sandbox test can read it; the handler (optional) does the rest.
//
// State arrives three ways: URL params at load, {type:'mock-set', values} messages from the
// viewer that frames this page, and MockLive.set() from the docked sheet.
//
// Dock: the viewer always adds dock=0, which marks <html data-dock="0"> and mounts nothing
// (in-mock review controls carry data-review-dock and are hidden by the template CSS rule).
// Without a dock param (the mock opened on its own, as in Lavish) the Options sheet docks here.
//
// Links: same-folder page links are rewritten to carry the current values and dock state, so a
// page change inside the frame keeps the setup; links leaving the folder open a new tab (the
// sandbox allows pop-ups that escape it).
//
// No storage, no fetch(), no module syntax: Lavish runs this page at an opaque origin.
(function () {
  'use strict';
  const cfg = window.VIEWER_CONFIG || { options: [], states: [] };
  const root = document.documentElement;
  const params = new URLSearchParams(location.search);
  const handlers = {};
  const values = {};
  const listeners = [];
  const mock = root.dataset.mock || null;
  const dock = params.get('dock');
  const folder = location.href.split(/[?#]/)[0].replace(/[^/]*$/, '');
  let ready = false;

  const applicable = (o) => !o.only || !mock || o.only.includes(mock);
  const startValue = (o) => o.start || (o.choices.find((c) => c.rec) || o.choices[0]).value;

  function applyOne(key, value) {
    values[key] = String(value);
    root.dataset[key] = values[key];
    if (handlers[key]) {
      try { handlers[key](values[key]); } catch (e) { console.error('MockLive handler', key, e); }
    }
  }

  function relink() {
    for (const a of document.querySelectorAll('a[href]')) {
      if (a.closest('[data-review-dock]')) continue;
      const raw = a.dataset.liveHref || a.getAttribute('href');
      if (!raw || raw.startsWith('#') || /^(mailto|tel|javascript):/i.test(raw)) continue;
      let u;
      try { u = new URL(raw, location.href); } catch { continue; }
      if (u.href.startsWith(folder) && /\.html$/i.test(u.pathname)) {
        a.dataset.liveHref = raw;
        const q = new URLSearchParams(u.search);
        for (const [k, v] of Object.entries(values)) q.set(k, v);
        if (dock !== null) q.set('dock', dock);
        a.setAttribute('href', u.pathname.split('/').pop() + '?' + q + u.hash);
      } else if (/^https?:$/.test(u.protocol)) {
        a.target = '_blank';
        a.rel = 'noopener';
      }
    }
  }

  function notify() { for (const fn of listeners) { try { fn({ ...values }); } catch {} } }

  function init(opts = {}) {
    if (ready) return MockLive;
    ready = true;
    Object.assign(handlers, opts.apply || {});
    if (dock === '0') {
      root.dataset.dock = '0';
      const st = document.createElement('style');
      st.textContent = 'html[data-dock="0"] [data-review-dock]{display:none!important}';
      document.head.append(st);
    }
    for (const o of cfg.options || []) {
      if (!applicable(o)) continue;
      applyOne(o.key, params.has(o.key) ? params.get(o.key) : startValue(o));
    }
    for (const s of cfg.states || []) applyOne(s.key, params.has(s.key) ? params.get(s.key) : s.off);
    relink();
    if (dock === null && window.OptionsSheet) window.OptionsSheet.mount({ host: 'dock' });
    return MockLive;
  }

  // '*' was used by the sender on purpose (opaque origin), so the origin is not checked here:
  // only the frame's own parent, sending a mock-set message, may drive the mock.
  addEventListener('message', (e) => {
    if (e.source !== window.parent || e.data?.type !== 'mock-set') return;
    for (const [k, v] of Object.entries(e.data.values || {})) applyOne(k, v);
    relink();
    notify();
  });

  const MockLive = {
    mock,
    values,
    init,
    set(key, value) { applyOne(key, value); relink(); notify(); },
    onChange(fn) { listeners.push(fn); },
  };
  window.MockLive = MockLive;
  // A mock that never calls init still mirrors its state and gets the dock.
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', () => init());
  else setTimeout(() => init(), 0);
})();
