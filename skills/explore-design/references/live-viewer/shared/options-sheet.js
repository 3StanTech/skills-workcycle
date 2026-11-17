// Options sheet (explore-design live-viewer template): one script, two hosts.
//   OptionsSheet.mount({ host: 'viewer', frame, setWidth })  in compare.html: every row; options
//     are posted to the framed mock as {type:'mock-set', values}; mock, page and reload-states set
//     a new frame src; Desktop/Phone calls setWidth.
//   OptionsSheet.mount({ host: 'dock' })  inside a single mock (mock-live.js calls it when the mock
//     is opened on its own): no mock, page or width rows; changes call MockLive.set; a verdict.
// Both hosts always render the form, the note field, the queue button and Copy answers.
// Rendered from window.VIEWER_CONFIG (shared/viewer-config.js). Classic script; every storage
// call is wrapped because Lavish's sandbox (an opaque origin) throws on storage.
(function () {
  'use strict';

  // '*' on purpose: inside Lavish the real origin is opaque even though location.origin still
  // reads as the server's, so a named target origin silently drops every message. The mock
  // accepts messages only from its parent frame (the e.source check in mock-live.js).
  const TARGET = '*';

  const CSS = `
.osh-root{--osh-ink:#f2f3f5;--osh-soft:#b3b7bf;--osh-hair:rgb(255 255 255/.14);--osh-acc:#e0a040;--osh-bg:rgb(22 24 30/.97);
  font:400 13px/1.4 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;color:var(--osh-ink);color-scheme:dark;letter-spacing:normal;text-transform:none}
.osh-root *{box-sizing:border-box}
.osh-root :focus-visible{outline:2px solid var(--osh-acc);outline-offset:2px}
.osh-pill{position:fixed;z-index:2147483000;display:inline-flex;align-items:center;gap:8px;min-height:40px;max-width:calc(100vw - 32px);padding:0 14px;border:0;border-radius:999px;cursor:pointer;
  color:var(--osh-ink);background:var(--osh-bg);box-shadow:inset 0 0 0 1px var(--osh-hair),0 8px 24px -8px rgb(0 0 0/.7);font:600 13px/1 system-ui,sans-serif}
.osh-pill .osh-sum{font-weight:500;color:var(--osh-soft);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:260px}
.osh-pill[aria-expanded=true]{display:none}
.osh-c-bottom-right{right:16px;bottom:16px}.osh-c-bottom-left{left:16px;bottom:16px}.osh-c-top-right{right:16px;top:16px}.osh-c-top-left{left:16px;top:16px}
.osh-sheet{position:fixed;z-index:2147483001;margin:0;width:min(420px,calc(100vw - 24px));max-height:calc(100dvh - 24px);overflow:auto;padding:14px;border:0;border-radius:18px;
  color:var(--osh-ink);background:var(--osh-bg);box-shadow:inset 0 0 0 1px var(--osh-hair),0 20px 50px -16px rgb(0 0 0/.9);scrollbar-width:thin}
.osh-sheet.osh-c-bottom-right,.osh-sheet.osh-c-top-right{inset:12px 12px auto auto}.osh-sheet.osh-c-bottom-left,.osh-sheet.osh-c-top-left{inset:12px auto auto 12px}
.osh-sheet[open]{display:grid;gap:8px}
.osh-head{display:flex;align-items:center;justify-content:space-between;gap:10px}
.osh-head h2{margin:0;font:650 15px/1.2 system-ui,sans-serif;color:var(--osh-ink)}
.osh-eyebrow{display:block;margin-bottom:2px;font:600 10.5px/1.2 system-ui,sans-serif;letter-spacing:.08em;text-transform:uppercase;color:var(--osh-acc)}
.osh-x{width:32px;height:32px;flex:none;border:0;border-radius:50%;cursor:pointer;color:var(--osh-ink);background:rgb(255 255 255/.08);font:600 16px/1 system-ui,sans-serif}
.osh-form{display:grid;gap:7px;margin:0}
.osh-row{margin:0;padding:0;border:0;min-width:0;display:grid;grid-template-columns:76px minmax(0,1fr);gap:4px 8px;align-items:center}
.osh-row[disabled]{opacity:.38}
.osh-row legend{float:left;padding:0;font:600 10.5px/1.2 system-ui,sans-serif;letter-spacing:.05em;text-transform:uppercase;color:var(--osh-soft)}
.osh-row legend small{display:block;font:inherit;color:var(--osh-acc);letter-spacing:.03em}
.osh-segs{display:flex;flex-wrap:wrap;gap:3px;padding:3px;border-radius:12px;background:rgb(255 255 255/.06)}
.osh-segs label{position:relative;flex:1 1 auto;margin:0}
.osh-segs input{position:absolute;inset:0;opacity:0;margin:0;cursor:pointer;width:100%;height:100%}
.osh-segs span{display:flex;align-items:center;justify-content:center;gap:4px;min-height:28px;padding:0 8px;border-radius:9px;white-space:nowrap;font:600 12.5px/1 system-ui,sans-serif;color:var(--osh-soft)}
.osh-segs input:checked+span{background:var(--osh-ink);color:#111}
.osh-segs input:focus-visible+span{outline:2px solid var(--osh-acc);outline-offset:1px}
.osh-segs kbd{font:500 10px/1 ui-monospace,monospace;opacity:.7}
.osh-rec{color:var(--osh-acc);font-size:11px}
.osh-chips{display:flex;flex-wrap:wrap;gap:6px}
.osh-chips label{display:inline-flex;align-items:center;gap:6px;min-height:28px;margin:0;padding:0 10px;border-radius:999px;background:rgb(255 255 255/.06);cursor:pointer;font:600 12.5px/1 system-ui,sans-serif;color:var(--osh-soft)}
.osh-chips input{accent-color:var(--osh-acc);margin:0}
.osh-why{grid-column:2;margin:0;color:var(--osh-soft);font-size:12px;line-height:1.35}
.osh-why:empty{display:none}
.osh-note-l{font:600 10.5px/1.2 system-ui,sans-serif;letter-spacing:.05em;text-transform:uppercase;color:var(--osh-soft)}
.osh-root textarea{width:100%;min-height:38px;margin:0;padding:7px 9px;border-radius:10px;border:1px solid var(--osh-hair);background:rgb(0 0 0/.35);color:var(--osh-ink);font:inherit;resize:vertical}
.osh-queue{width:100%;min-height:38px;padding:0 14px;border:0;border-radius:999px;background:var(--osh-acc);color:#111;font:650 13.5px/1 system-ui,sans-serif;cursor:pointer}
.osh-foot{margin:0;color:var(--osh-soft);font-size:11.5px}
.osh-link{padding:0;border:0;background:none;color:var(--osh-ink);font:inherit;font-weight:600;text-decoration:underline;text-underline-offset:.2em;cursor:pointer}
.osh-status{margin:0;color:var(--osh-soft);font-size:12px}
.osh-status:empty{display:none}`;

  const esc = (s) => String(s ?? '').replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]);
  const startValue = (o) => o.start || (o.choices.find((c) => c.rec) || o.choices[0]).value;
  const store = {
    get(k) { try { return JSON.parse(localStorage.getItem(k) || 'null'); } catch { return null; } },
    set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch {} },
  };

  function mount(opts = {}) {
    const cfg = window.VIEWER_CONFIG;
    if (!cfg) { console.error('OptionsSheet: window.VIEWER_CONFIG is missing'); return null; }
    if (document.querySelector('.osh-root')) return null;
    const host = opts.host === 'dock' ? 'dock' : 'viewer';
    const viewer = host === 'viewer';
    const live = window.MockLive;
    const q = new URLSearchParams(location.search);
    const corner = viewer ? 'bottom-right' : (cfg.dockCorner || 'bottom-left');
    const mocks = cfg.mocks || [], pages = cfg.pages || [], options = cfg.options || [], states = cfg.states || [];

    // ---- State: config defaults, then saved (viewer), then URL params, then the live mock (dock).
    const state = {
      mock: (mocks.find((m) => m.rec) || mocks[0] || {}).value,
      page: (pages[0] || {}).value,
      values: Object.fromEntries(options.map((o) => [o.key, startValue(o)])),
      on: Object.fromEntries(states.map((s) => [s.key, false])),
      width: 'desktop',
    };
    if (viewer) {
      const saved = store.get('live-viewer:' + cfg.id);
      if (saved) Object.assign(state, saved, { values: { ...state.values, ...saved.values }, on: { ...state.on, ...saved.on } });
    }
    if (q.has('mock') && mocks.some((m) => m.value === q.get('mock'))) state.mock = q.get('mock');
    if (q.has('page') && pages.some((p) => p.value === q.get('page'))) state.page = q.get('page');
    for (const o of options) if (q.has(o.key)) state.values[o.key] = q.get(o.key);
    for (const s of states) if (q.has(s.key)) state.on[s.key] = q.get(s.key) === s.on;
    if (!viewer && live) {
      state.mock = live.mock || state.mock;
      // Lavish serves an opened page as .../index.html, so the page comes from <html data-page>.
      const file = location.pathname.split('/').pop();
      const pg = pages.find((p) => p.value === live.page) || pages.find((p) => p.file(state.mock) === file);
      if (pg) state.page = pg.value;
      for (const o of options) if (live.values[o.key] !== undefined) state.values[o.key] = live.values[o.key];
      for (const s of states) if (live.values[s.key] !== undefined) state.on[s.key] = live.values[s.key] === s.on;
    }

    const applies = (o) => !o.only || o.only.includes(state.mock);
    const urlValues = (dockParam) => {
      const p = new URLSearchParams();
      for (const o of options) if (applies(o)) p.set(o.key, state.values[o.key]);
      for (const s of states) p.set(s.key, state.on[s.key] ? s.on : s.off);
      if (dockParam) p.set('dock', '0');
      return p;
    };
    const fileFor = () => (pages.find((p) => p.value === state.page) || pages[0]).file(state.mock);
    const viewerUrl = () => { const p = urlValues(false); p.set('mock', state.mock); p.set('page', state.page); return 'compare.html?' + p; };

    // ---- Markup.
    const seg = (name, items, current, keyed) => `<div class="osh-segs">${items.map((c, i) =>
      `<label><input type="radio" name="${esc(name)}" value="${esc(c.value)}"${c.value === current ? ' checked' : ''}><span>${keyed && i < 9 ? `<kbd>${i + 1}</kbd> ` : ''}${esc(c.label)}${c.rec ? ' <b class="osh-rec" aria-label="recommended">★</b>' : ''}</span></label>`).join('')}</div>`;
    const row = (legend, body, extra = '', note = '') => `<fieldset class="osh-row"${extra}><legend>${legend}${note ? `<small>${esc(note)}</small>` : ''}</legend>${body}<p class="osh-why" data-why></p></fieldset>`;
    let rows = '';
    if (viewer && mocks.length) rows += row('Mock', seg('__mock', mocks, state.mock, true), ' data-row="__mock"');
    if (viewer && pages.length > 1) rows += row('Page', seg('__page', pages, state.page), ' data-row="__page"');
    for (const o of options) rows += row(esc(o.label), seg(o.key, o.choices, state.values[o.key]), ` data-row="${esc(o.key)}"${o.only ? ` data-only="${esc(o.only.join(' '))}"` : ''}`, o.only ? o.only.map((m) => m.toUpperCase()).join(', ') + ' only' : '');
    const chips = states.map((s) => `<label><input type="checkbox" name="${esc(s.key)}"${state.on[s.key] ? ' checked' : ''}> ${esc(s.label)}</label>`);
    if (chips.length) rows += row('Preview', `<div class="osh-chips">${chips.join('')}</div>`, ' data-row="__states"', 'not the pick');
    if (viewer) rows += row('Width', seg('__width', [{ value: 'desktop', label: `Desktop ${cfg.designWidth || 1440}` }, { value: 'phone', label: `Phone ${cfg.phoneWidth || 390}` }], state.width), ' data-row="__width"', 'not the pick');
    const presets = cfg.presets || [];
    if (presets.length) rows += row('Presets', `<div class="osh-chips">${presets.map((p) => `<button class="osh-link" type="button" data-osh-preset="${esc(p.id)}">${esc(p.label)}</button>`).join('')}</div>`, ' data-row="__presets"');
    if (!viewer) rows += row('Verdict', seg('__verdict', [{ value: 'approve', label: 'Approve' }, { value: 'changes', label: 'Changes needed' }], 'approve'), ' data-row="__verdict"');

    const rootEl = document.createElement('div');
    rootEl.className = 'osh-root';
    rootEl.setAttribute('data-review-dock', '');
    rootEl.dataset.host = host;
    const qid = esc(cfg.id || 'live-pick');
    rootEl.innerHTML = `<style>${CSS}</style>
<button class="osh-pill osh-c-${corner}" type="button" aria-controls="osh-sheet" aria-expanded="false" data-osh-open><span aria-hidden="true">◆</span> Options <span class="osh-sum" data-osh-sum></span></button>
<dialog class="osh-sheet osh-c-${corner}" id="osh-sheet" aria-labelledby="osh-title">
  <div class="osh-head"><div><span class="osh-eyebrow">${esc(cfg.eyebrow || 'Live review')}</span><h2 id="osh-title">${esc(viewer ? cfg.title : 'Review this mock')}</h2></div>
    <button class="osh-x" type="button" aria-label="Close options (Esc)" data-osh-close>✕</button></div>
  <form class="osh-form" data-lavish-question="${qid}">
    ${rows}
    <label class="osh-note-l" for="osh-note">${viewer ? 'Changes for the next round (optional)' : 'Notes (optional)'}</label>
    <textarea id="osh-note" name="__note" rows="2"></textarea>
    <button class="osh-queue" type="submit" data-osh-queue>${viewer ? 'Queue this setup as my pick' : 'Queue final pick'}</button>
    <p class="osh-foot"><b class="osh-rec">★</b> recommended · Esc closes · <button class="osh-link" type="button" data-osh-copy>Copy answers</button> · ${viewer
      ? '<a class="osh-link" data-osh-full href="#" target="_blank" rel="noopener">Open full size</a>'
      : '<a class="osh-link" data-osh-viewer href="compare.html" target="_blank" rel="noopener">Open in viewer</a>'}</p>
    <p class="osh-status" role="status" aria-live="polite" data-osh-status></p>
  </form>
</dialog>`;
    document.body.append(rootEl);

    const $ = (s) => rootEl.querySelector(s);
    const form = $('.osh-form'), sheet = $('.osh-sheet'), pill = $('[data-osh-open]'), status = $('[data-osh-status]');
    const labelOf = (list, v) => (list.find((c) => c.value === v) || {}).label || v;

    function setSrc() { if (opts.frame) opts.frame.setAttribute('src', fileFor() + '?' + urlValues(true)); }
    function post(values) { opts.frame?.contentWindow?.postMessage({ type: 'mock-set', values }, TARGET); }

    function paint() {
      for (const fs of rootEl.querySelectorAll('[data-only]')) {
        fs.disabled = !fs.dataset.only.split(' ').includes(state.mock);
        if (!viewer) fs.disabled = fs.disabled || !live; // dock: only this mock's options
      }
      const why = (k, list, v) => { const el = rootEl.querySelector(`[data-row="${k}"] [data-why]`); if (el) el.textContent = (list.find((c) => c.value === v) || {}).why || ''; };
      why('__mock', mocks, state.mock);
      for (const o of options) why(o.key, o.choices, state.values[o.key]);
      const sum = [];
      if (viewer) sum.push(labelOf(mocks, state.mock));
      for (const o of options) if (applies(o)) sum.push(labelOf(o.choices, state.values[o.key]));
      $('[data-osh-sum]').textContent = sum.join(' · ');
      const full = $('[data-osh-full]'); if (full) full.href = fileFor() + '?' + urlValues(false);
      const vw = $('[data-osh-viewer]'); if (vw) vw.href = viewerUrl();
      if (viewer) store.set('live-viewer:' + cfg.id, { mock: state.mock, page: state.page, values: state.values, on: state.on, width: state.width });
    }

    form.addEventListener('change', (e) => {
      const t = e.target, n = t.name;
      if (!n || n === '__note' || n === '__verdict') return;
      if (n === '__mock' || n === '__page') { state[n.slice(2)] = t.value; paint(); setSrc(); return; }
      if (n === '__width') { state.width = t.value; paint(); opts.setWidth?.(t.value); return; }
      const st = states.find((s) => s.key === n);
      if (st) {
        state.on[n] = t.checked; paint();
        const v = t.checked ? st.on : st.off;
        // Dock: keep every parameter the page was opened with (Lavish's revision and load token).
        if (st.reload) { if (viewer) setSrc(); else { const p = new URLSearchParams(location.search); for (const [k, v] of urlValues(false)) p.set(k, v); location.search = '?' + p; } }
        else if (viewer) post({ [n]: v }); else live?.set(n, v);
        return;
      }
      state.values[n] = t.value; paint();
      if (viewer) post({ [n]: t.value }); else live?.set(n, t.value);
    });

    // Presets set several options at once (e.g. "Recommended set" when every effect starts off).
    const presetValues = (p) => Object.fromEntries(options.filter(applies).map((o) => [o.key,
      p.values === 'rec' ? (o.choices.find((c) => c.rec) || o.choices[0]).value : p.values === 'start' ? startValue(o) : p.values?.[o.key]]).filter(([, v]) => v !== undefined));
    rootEl.addEventListener('click', (e) => {
      const b = e.target.closest('[data-osh-preset]'); if (!b) return;
      const p = presets.find((x) => x.id === b.dataset.oshPreset); if (!p) return;
      const vals = presetValues(p);
      for (const [k, v] of Object.entries(vals)) { state.values[k] = v; const i = form.querySelector(`input[name="${CSS_ESC(k)}"][value="${CSS_ESC(v)}"]`); if (i) i.checked = true; }
      paint();
      if (viewer) post(vals); else for (const [k, v] of Object.entries(vals)) live?.set(k, v);
    });

    // Viewer: a link followed inside the frame reports its mock and page, so the pick stays true.
    if (viewer) addEventListener('message', (e) => {
      if (!opts.frame || e.source !== opts.frame.contentWindow || e.data?.type !== 'mock-nav') return;
      const { mock, page } = e.data;
      if (mocks.some((m) => m.value === mock)) state.mock = mock;
      if (pages.some((p) => p.value === page)) state.page = page;
      for (const [n, v] of [['__mock', state.mock], ['__page', state.page]]) { const i = form.querySelector(`input[name="${n}"][value="${CSS_ESC(v)}"]`); if (i) i.checked = true; }
      paint();
    });

    function setSheet(open) {
      if (open) sheet.show(); else sheet.close();
      pill.setAttribute('aria-expanded', String(open));
      (open ? form.querySelector('input:checked:not(:disabled)') || form.querySelector('textarea') : pill)?.focus({ preventScroll: true });
    }
    pill.addEventListener('click', () => setSheet(true));
    $('[data-osh-close]').addEventListener('click', () => setSheet(false));
    addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && sheet.open) { e.preventDefault(); setSheet(false); return; }
      // Keys 1-9 pick the nth mock (viewer only), never while typing.
      const t = e.target, typing = t && (t.isContentEditable || /^(TEXTAREA|SELECT)$/.test(t.tagName) || (t.tagName === 'INPUT' && !/^(radio|checkbox|button|submit|reset)$/i.test(t.type)));
      if (!viewer || typing || e.altKey || e.ctrlKey || e.metaKey || !/^[1-9]$/.test(e.key)) return;
      const m = mocks[Number(e.key) - 1];
      if (!m || m.value === state.mock) return;
      const input = form.querySelector(`input[name="__mock"][value="${CSS_ESC(m.value)}"]`);
      if (input) { input.checked = true; input.dispatchEvent(new Event('change', { bubbles: true })); }
    });

    function answers() {
      const v = {};
      for (const o of options) if (applies(o)) v[o.key] = state.values[o.key];
      const data = { question: cfg.id, host, mock: state.mock, page: state.page, values: v, note: form.elements.__note.value.trim() };
      if (!viewer) data.verdict = form.elements.__verdict.value;
      return data;
    }
    function text(d) {
      const parts = [`Mock: ${labelOf(mocks, d.mock)}`];
      for (const o of options) if (o.key in d.values) parts.push(`${o.label}: ${labelOf(o.choices, d.values[o.key])}`);
      if (d.verdict) parts.push(`Verdict: ${d.verdict === 'approve' ? 'Approve' : 'Changes needed'}`);
      if (d.note) parts.push(`Note: ${d.note}`);
      return `${cfg.id} ${viewer ? 'pick' : 'final pick'}. ` + parts.join('. ');
    }
    form.addEventListener('submit', (e) => {
      e.preventDefault();
      const d = answers(), t = text(d);
      if (window.lavish?.queuePrompt) { window.lavish.queuePrompt(t, { tag: 'choice', text: t, element: form, data: d }); status.textContent = 'Queued. Press Send in the Lavish bar.'; }
      else status.textContent = 'Lavish is not running here: use Copy answers and paste them in the chat.';
    });
    $('[data-osh-copy]').addEventListener('click', async () => {
      const t = text(answers());
      try { await navigator.clipboard.writeText(t); status.textContent = 'Answers copied.'; }
      catch { status.textContent = 'Clipboard unavailable: ' + t; }
    });

    paint();
    if (viewer) { setSrc(); opts.setWidth?.(state.width); setSheet(true); }
    return { state, open: () => setSheet(true), close: () => setSheet(false) };
  }

  const CSS_ESC = (s) => (window.CSS && window.CSS.escape ? window.CSS.escape(s) : String(s).replace(/"/g, '\\"'));
  window.OptionsSheet = { mount };
})();
