// sandbox-e2e.mjs (explore-design live-viewer template): end-to-end test of the live viewer and the
// docked sheet inside Lavish's sandbox. Node 22+ (global WebSocket, fetch) and Chrome: CHROME_PATH,
// else the macOS default, else google-chrome / chromium on PATH.
//
//   node tools/sandbox-e2e.mjs [--url <page>] [--shot <png>] [--report <json>]
//   node tools/sandbox-e2e.mjs --portable <exported.html>
//
// Without --url it serves the folder above tools/ on a free port and opens tools/sandbox-test.html,
// which frames compare.html with Lavish's exact sandbox flags; then it frames mock-<first>.html on
// its own for the docked sheet. With --url it opens that page (a running Lavish session) and runs
// the viewer checks or the dock checks, whichever the page holds. --portable copies one exported
// file alone into an empty folder and passes only when nothing fails to load and no error fires.
// Every check reads VIEWER_CONFIG, so a project needs no test code of its own. Frames are reached
// through CDP auto-attach (flatten), whether Chrome isolates them or not.
// Prints PASS/FAIL per check. Exit 0 all pass, 1 any fail, 2 setup error.
import { spawn, execFileSync } from 'node:child_process';
import http from 'node:http';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const TOOLS = path.dirname(fileURLToPath(import.meta.url));
let ROOT = path.dirname(TOOLS);
const argv = process.argv.slice(2);
const opt = (n) => { const i = argv.indexOf(n); return i >= 0 ? argv[i + 1] : null; };
const URL_ARG = opt('--url'), SHOT = opt('--shot'), REPORT = opt('--report'), PORTABLE = opt('--portable');
const W = 1080, H = 700;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const results = [];
const check = (name, ok, seen) => { results.push({ name, ok: !!ok, seen }); console.log(`${ok ? 'PASS' : 'FAIL'}  ${name}${seen !== undefined ? '  · ' + (typeof seen === 'string' ? seen : JSON.stringify(seen)) : ''}`); };
class SetupError extends Error {}

function findChrome() {
  if (process.env.CHROME_PATH) return process.env.CHROME_PATH;
  const mac = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
  if (fs.existsSync(mac)) return mac;
  for (const n of ['google-chrome', 'google-chrome-stable', 'chromium', 'chromium-browser']) { try { return execFileSync('which', [n], { encoding: 'utf8' }).trim(); } catch {} }
  return null;
}

// ---------- Static server (no CORS headers, like Lavish and python -m http.server) ----------
const MIME = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript', '.mjs': 'text/javascript', '.css': 'text/css', '.json': 'application/json', '.svg': 'image/svg+xml', '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.webp': 'image/webp', '.woff2': 'font/woff2', '.woff': 'font/woff', '.ttf': 'font/ttf', '.otf': 'font/otf', '.ico': 'image/x-icon' };
function serve(dir) {
  return new Promise((res) => {
    const srv = http.createServer((req, rsp) => {
      const p = path.join(dir, decodeURIComponent(new URL(req.url, 'http://x').pathname));
      if (!p.startsWith(dir) || !fs.existsSync(p) || fs.statSync(p).isDirectory()) { rsp.writeHead(404); rsp.end('not found'); return; }
      rsp.writeHead(200, { 'content-type': MIME[path.extname(p).toLowerCase()] || 'application/octet-stream', 'cache-control': 'no-store' });
      fs.createReadStream(p).pipe(rsp);
    });
    srv.listen(0, '127.0.0.1', () => res(srv));
  });
}

// Files of the mocks folder: a failed request or a script error counts only when it is ours.
function ourNames(dir) {
  const s = new Set();
  const walk = (d, depth) => { for (const e of fs.readdirSync(d, { withFileTypes: true })) { if (e.name.startsWith('.') || e.name === 'node_modules') continue; const p = path.join(d, e.name); if (e.isDirectory()) { if (depth < 4) walk(p, depth + 1); } else s.add(e.name); } };
  walk(dir, 0);
  return s;
}

// ---------- Chrome + CDP ----------
const chrome = findChrome();
const profile = fs.mkdtempSync(path.join(os.tmpdir(), 'live-viewer-e2e-'));
let proc, ws, server, tmpPortable;
let id = 0;
const pending = new Map();
const contexts = []; // { sessionId, contextId }
const failures = []; // { url, error }
const scriptErrors = []; // { url, text }
const reqUrls = new Map();
let BASE = '', OURS = new Set();
const ours = (u) => { try { const n = decodeURIComponent(new URL(u).pathname.split('/').pop()); return !!n && OURS.has(n); } catch { return false; } };

function send(method, params = {}, sessionId, ms = 15000) {
  return Promise.race([
    new Promise((res, rej) => { const i = ++id; pending.set(i, (m) => (m.error ? rej(new Error(`${method}: ${m.error.message}`)) : res(m.result))); ws.send(JSON.stringify({ id: i, method, params, ...(sessionId ? { sessionId } : {}) })); }),
    sleep(ms).then(() => { throw new Error(`timed out: ${method}`); }),
  ]);
}
async function prepSession(s) {
  await Promise.all([send('Runtime.enable', {}, s).catch(() => {}), send('Network.enable', {}, s).catch(() => {})]);
  await send('Target.setAutoAttach', { autoAttach: true, waitForDebuggerOnStart: true, flatten: true }, s).catch(() => {});
  await send('Runtime.runIfWaitingForDebugger', {}, s).catch(() => {});
}
function onMessage(ev) {
  const m = JSON.parse(ev.data);
  if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); return; }
  const p = m.params || {};
  if (m.method === 'Runtime.executionContextCreated' && p.context.auxData?.isDefault) contexts.push({ sessionId: m.sessionId, contextId: p.context.id });
  else if (m.method === 'Runtime.executionContextDestroyed') { const k = contexts.findIndex((c) => c.contextId === p.executionContextId && c.sessionId === m.sessionId); if (k >= 0) contexts.splice(k, 1); }
  else if (m.method === 'Runtime.executionContextsCleared') { for (let k = contexts.length - 1; k >= 0; k--) if (contexts[k].sessionId === m.sessionId) contexts.splice(k, 1); }
  else if (m.method === 'Target.attachedToTarget') prepSession(p.sessionId);
  else if (m.method === 'Network.requestWillBeSent') reqUrls.set(`${m.sessionId}|${p.requestId}`, p.request.url);
  else if (m.method === 'Network.loadingFailed') {
    const url = reqUrls.get(`${m.sessionId}|${p.requestId}`) || '?';
    if (!p.canceled && (ours(url) || PORTABLE)) failures.push({ url, error: p.errorText + (p.corsErrorStatus ? ` (CORS ${p.corsErrorStatus.corsError})` : '') + (p.blockedReason ? ` (blocked ${p.blockedReason})` : '') });
  } else if (m.method === 'Runtime.exceptionThrown') {
    const d = p.exceptionDetails, url = d.url || d.stackTrace?.callFrames?.[0]?.url || '';
    if (ours(url) || PORTABLE) scriptErrors.push({ url, text: (d.exception?.description || d.text || '').split('\n')[0] });
  } else if (m.method === 'Runtime.consoleAPICalled' && p.type === 'error') {
    const url = p.stackTrace?.callFrames?.[0]?.url || '';
    if (ours(url) || PORTABLE) scriptErrors.push({ url, text: p.args.map((a) => a.value ?? a.description ?? '').join(' ').slice(0, 200) });
  }
}

async function evalIn(pred, expr) {
  for (const c of [...contexts].reverse()) {
    try {
      const r = await send('Runtime.evaluate', { expression: `(${pred}) ? (async () => (${expr}))() : '__skip'`, contextId: c.contextId, returnByValue: true, awaitPromise: true }, c.sessionId, 8000);
      if (r.exceptionDetails) continue;
      if (r.result?.value !== '__skip') return r.result.value;
    } catch {}
  }
  return undefined;
}
async function waitFor(pred, expr, test = (v) => !!v, ms = 8000) {
  const end = Date.now() + ms; let v;
  for (;;) { v = await evalIn(pred, expr); if (v !== undefined && test(v)) return v; if (Date.now() > end) return v; await sleep(150); }
}
async function key(k, code, text) {
  await send('Input.dispatchKeyEvent', { type: 'keyDown', key: k, code, text, windowsVirtualKeyCode: text ? text.charCodeAt(0) : 27 });
  await send('Input.dispatchKeyEvent', { type: 'keyUp', key: k, code, windowsVirtualKeyCode: text ? text.charCodeAt(0) : 27 });
}

const IN_VIEWER = `!!window.VIEWER_CONFIG && !!document.querySelector('[data-frame]')`;
const IN_MOCK = `!!window.MockLive && !document.querySelector('[data-frame]')`;
const MOCK_STATE = `({ file: location.pathname.split('/').pop(), search: location.search, ds: { ...document.documentElement.dataset }, marker: window.__e2e || null, w: innerWidth, h: innerHeight, sw: document.documentElement.scrollWidth, ready: document.readyState === 'complete' })`;
const toDs = (k) => k.replace(/-([a-z])/g, (_, c) => c.toUpperCase());
const fitExpr = (scope) => `(() => { const out = []; for (const el of document.querySelectorAll('${scope} input, ${scope} button, ${scope} textarea, ${scope} a, ${scope} select')) { const r = el.getBoundingClientRect(); if (!r.width && !r.height) { out.push('hidden:' + (el.name || el.textContent.trim().slice(0, 20))); continue; } if (r.left < 0 || r.top < 0 || r.right > innerWidth + 0.5 || r.bottom > innerHeight + 0.5) out.push((el.name || el.textContent.trim().slice(0, 20)) + '@' + Math.round(r.right) + 'x' + Math.round(r.bottom)); } return { n: document.querySelectorAll('${scope} input, ${scope} button, ${scope} textarea').length, out, vw: innerWidth, vh: innerHeight }; })()`;
const clickViewer = (name, value) => evalIn(IN_VIEWER, `(() => { const i = document.querySelector('.osh-root input[name="${name}"]${value !== undefined ? `[value="${value}"]` : ''}'); if (!i) return 'missing'; i.click(); return 'ok'; })()`);
const mark = (tag) => evalIn(IN_MOCK, `(window.__e2e = ${JSON.stringify(tag)})`);
const mockState = () => evalIn(IN_MOCK, MOCK_STATE);

// ---------- Viewer checks ----------
async function viewerChecks() {
  const cfg = await evalIn(IN_VIEWER, `JSON.parse(JSON.stringify({ ...VIEWER_CONFIG, pages: VIEWER_CONFIG.pages.map((p) => ({ ...p, files: Object.fromEntries(VIEWER_CONFIG.mocks.map((m) => [m.value, p.file(m.value)])) })) }))`);
  if (!cfg) throw new SetupError('VIEWER_CONFIG not readable in the viewer');
  const recMock = (cfg.mocks.find((m) => m.rec) || cfg.mocks[0]).value;
  const fileOf = (mock, page) => (cfg.pages.find((p) => p.value === page) || cfg.pages[0]).files[mock];
  let cur = { mock: recMock, page: cfg.pages[0].value };
  const applies = (o, mock) => !o.only || o.only.includes(mock);
  const goto = async (mock, page) => {
    if (mock !== cur.mock) await clickViewer('__mock', mock);
    if (page !== cur.page) await clickViewer('__page', page);
    cur = { mock, page };
    return waitFor(IN_MOCK, MOCK_STATE, (s) => s.ready && s.file === fileOf(mock, page), 10000);
  };
  await goto(recMock, cfg.pages[0].value);

  // 1. Really sandboxed.
  const vo = await evalIn(IN_VIEWER, 'self.origin'), mo = await evalIn(IN_MOCK, 'self.origin');
  check('1 viewer and mock run at an opaque origin', vo === 'null' && mo === 'null', { viewer: vo, mock: mo });
  // 2. The open sheet fits 1080x700.
  const fit = await evalIn(IN_VIEWER, fitExpr('.osh-sheet'));
  check('2 every sheet control inside the window', fit && fit.vw === W && fit.vh === H && fit.n > 0 && !fit.out.length, fit);
  // 3. Every option and choice applies in place.
  for (const o of cfg.options) {
    const m = applies(o, cur.mock) ? cur.mock : cfg.mocks.find((x) => applies(o, x.value)).value;
    await goto(m, cur.page);
    for (const c of o.choices) {
      const tag = `m-${o.key}-${c.value}`; await mark(tag);
      await clickViewer(o.key, c.value);
      const s = await waitFor(IN_MOCK, MOCK_STATE, (v) => v.ds[toDs(o.key)] === c.value, 4000);
      check(`3 ${o.key}=${c.value} applies in place`, s && s.ds[toDs(o.key)] === c.value && s.marker === tag, s && { value: s.ds[toDs(o.key)], marker: s.marker });
    }
    await clickViewer(o.key, (o.choices.find((c) => c.rec) || o.choices[0]).value);
  }
  // 4. An `only` option is disabled under a mock it excludes.
  for (const o of cfg.options.filter((x) => x.only)) {
    const ex = cfg.mocks.find((m) => !o.only.includes(m.value));
    if (!ex) continue;
    await goto(ex.value, cur.page);
    const dis = await evalIn(IN_VIEWER, `document.querySelector('.osh-root [data-row="${o.key}"]').disabled`);
    check(`4 ${o.key} disabled under mock ${ex.value}`, dis === true, dis);
  }
  await goto(recMock, cfg.pages[0].value);
  // 5. States: live ones toggle in place; reload ones change the URL.
  for (const st of cfg.states) {
    const tag = `s-${st.key}`; await mark(tag);
    await clickViewer(st.key);
    if (st.reload) {
      const s = await waitFor(IN_MOCK, MOCK_STATE, (v) => v.ready && v.search.includes(`${st.key}=${st.on}`) && v.marker !== tag, 8000);
      check(`5 ${st.key} (read once) reloads with ${st.key}=${st.on}`, s && s.search.includes(`${st.key}=${st.on}`) && s.ds[toDs(st.key)] === st.on, s && { search: s.search });
      await clickViewer(st.key);
      const b = await waitFor(IN_MOCK, MOCK_STATE, (v) => v.ready && v.search.includes(`${st.key}=${st.off}`), 8000);
      check(`5 ${st.key} back to ${st.off}`, b && b.ds[toDs(st.key)] === st.off, b && b.search);
    } else {
      const s = await waitFor(IN_MOCK, MOCK_STATE, (v) => v.ds[toDs(st.key)] === st.on, 4000);
      check(`5 ${st.key} on in place`, s && s.ds[toDs(st.key)] === st.on && s.marker === tag, s && { v: s.ds[toDs(st.key)], marker: s.marker });
      await clickViewer(st.key);
      const b = await waitFor(IN_MOCK, MOCK_STATE, (v) => v.ds[toDs(st.key)] === st.off, 4000);
      check(`5 ${st.key} off in place`, b && b.ds[toDs(st.key)] === st.off && b.marker === tag, b && { v: b.ds[toDs(st.key)], marker: b.marker });
    }
  }
  // 6. Mock and page switches load the expected file and carry the option values.
  const nonRec = cfg.options[0] && cfg.options[0].choices.find((c) => !c.rec);
  if (nonRec) await clickViewer(cfg.options[0].key, nonRec.value);
  const plan = [];
  for (const p of cfg.pages) plan.push([cur.mock, p.value]);
  for (const m of cfg.mocks) plan.push([m.value, cfg.pages[cfg.pages.length - 1].value]);
  plan.push([recMock, cfg.pages[0].value]);
  for (const [m, p] of plan) {
    if (m === cur.mock && p === cur.page) continue; // only real switches reload the frame
    const s = await goto(m, p);
    const want = nonRec ? `${cfg.options[0].key}=${nonRec.value}` : '';
    check(`6 mock ${m} page ${p} loads ${fileOf(m, p)} with the values`, s && s.file === fileOf(m, p) && s.search.includes(want) && s.search.includes('dock=0'), s && (s.file + s.search));
  }
  if (nonRec) await clickViewer(cfg.options[0].key, (cfg.options[0].choices.find((c) => c.rec) || cfg.options[0].choices[0]).value);
  // 7 and 15. Width toggle; no sideways scroll at either width.
  await clickViewer('__width', 'phone');
  const ph = await waitFor(IN_MOCK, MOCK_STATE, (v) => v.w === cfg.phoneWidth, 4000);
  check(`7 phone width gives ${cfg.phoneWidth}`, ph && ph.w === cfg.phoneWidth, ph && ph.w);
  check('15 no sideways scroll at phone width', ph && ph.sw <= ph.w, ph && { scrollWidth: ph.sw, innerWidth: ph.w });
  await clickViewer('__width', 'desktop');
  const want = Math.max(W, cfg.designWidth);
  const dt = await waitFor(IN_MOCK, MOCK_STATE, (v) => v.w === want, 4000);
  check(`7 desktop width gives ${want}`, dt && dt.w === want, dt && dt.w);
  check('15 no sideways scroll at desktop width', dt && dt.sw <= dt.w, dt && { scrollWidth: dt.sw, innerWidth: dt.w });
  // 12. Number keys (real key presses).
  await evalIn(IN_VIEWER, `document.querySelector('.osh-root input[name="__mock"]:checked').focus()`);
  const second = cfg.mocks[1];
  if (second) {
    await key('2', 'Digit2', '2');
    const s = await waitFor(IN_MOCK, MOCK_STATE, (v) => v.ready && v.file === fileOf(second.value, cur.page), 6000);
    check('12 key 2 loads the second mock', s && s.file === fileOf(second.value, cur.page), s && s.file);
    cur.mock = second.value;
    await evalIn(IN_VIEWER, `(() => { const t = document.querySelector('.osh-root textarea'); t.value = ''; t.focus(); return 1; })()`);
    await key('1', 'Digit1', '1');
    await sleep(800);
    const typed = await evalIn(IN_VIEWER, `document.querySelector('.osh-root textarea').value`);
    const s2 = await mockState();
    check('12 key 1 while typing types and switches nothing', typed === '1' && s2 && s2.file === fileOf(second.value, cur.page), { typed, file: s2 && s2.file });
    await evalIn(IN_VIEWER, `(document.querySelector('.osh-root textarea').value = '', 1)`);
    await goto(recMock, cur.page);
  }
  // 13. Why-notes show for the selected value; the sheet still fits.
  const whyMock = cfg.mocks.find((m) => m.why);
  if (whyMock) { await goto(whyMock.value, cur.page); const t = await evalIn(IN_VIEWER, `document.querySelector('.osh-root [data-row="__mock"] [data-why]').textContent`); check('13 mock why-note shows', t === whyMock.why, t); }
  for (const o of cfg.options) {
    const c = o.choices.find((x) => x.why); if (!c || !applies(o, cur.mock)) continue;
    await clickViewer(o.key, c.value);
    const t = await evalIn(IN_VIEWER, `document.querySelector('.osh-root [data-row="${o.key}"] [data-why]').textContent`);
    check(`13 ${o.key} why-note shows`, t === c.why, t);
  }
  const fit2 = await evalIn(IN_VIEWER, fitExpr('.osh-sheet'));
  check('13 sheet still fits with why-notes showing', fit2 && !fit2.out.length, fit2 && fit2.out);
  // 10. Fonts load in each mock.
  for (const m of cfg.mocks) {
    await goto(m.value, cfg.pages[0].value);
    const f = await evalIn(IN_MOCK, `(async () => { await Promise.all([...document.fonts].map((x) => x.load().catch(() => null))); await document.fonts.ready; return [...document.fonts].map((x) => x.family + ':' + x.status); })()`);
    const bad = (f || []).filter((x) => !x.endsWith(':loaded'));
    check(`10 fonts load in mock ${m.value}`, Array.isArray(f) && !bad.length, f && (f.length ? f : 'no web fonts'));
  }
  // 11. Links: same-folder links keep the state inside the frame; outside links open a new tab.
  for (const m of cfg.mocks) {
    await goto(m.value, cfg.pages[0].value);
    const ch = cfg.options.find((o) => applies(o, m.value) && o.choices.length > 1);
    let wantVal = null;
    if (ch) { wantVal = ch.choices.find((c) => !c.rec)?.value || ch.choices[1].value; await clickViewer(ch.key, wantVal); await waitFor(IN_MOCK, MOCK_STATE, (v) => v.ds[toDs(ch.key)] === wantVal, 4000); }
    const links = await evalIn(IN_MOCK, `(() => { const folder = location.href.split(/[?#]/)[0].replace(/[^/]*$/, ''); const here = location.pathname.split('/').pop(); const inn = [], out = []; for (const a of document.querySelectorAll('a[href]')) { if (a.closest('[data-review-dock]')) continue; const raw = a.getAttribute('href'); if (raw.startsWith('#')) continue; const u = new URL(raw, location.href); if (u.href.startsWith(folder) && /\\.html$/.test(u.pathname)) { const f = u.pathname.split('/').pop(); if (f !== here && !inn.includes(f)) inn.push(f); } else if (/^https?:$/.test(u.protocol)) out.push({ href: u.href, target: a.target }); } return { inn, out }; })()`);
    for (const f of links?.inn || []) {
      await evalIn(IN_MOCK, `(() => { const a = [...document.querySelectorAll('a[href]')].find((x) => !x.closest('[data-review-dock]') && new URL(x.getAttribute('href'), location.href).pathname.endsWith('/${f}')); a.click(); return 1; })()`);
      const s = await waitFor(IN_MOCK, MOCK_STATE, (v) => v.ready && v.file === f, 8000);
      check(`11 mock ${m.value} link to ${f} keeps the setup`, s && s.file === f && (!ch || s.ds[toDs(ch.key)] === wantVal) && s.ds.dock === '0', s && { file: s.file, value: ch && s.ds[toDs(ch.key)], dock: s.ds.dock });
      await evalIn(IN_VIEWER, `(document.querySelector('.osh-root input[name="__page"]:checked')?.dispatchEvent(new Event('change', { bubbles: true })), 1)`);
      await waitFor(IN_MOCK, MOCK_STATE, (v) => v.ready && v.file === fileOf(m.value, cfg.pages[0].value), 8000);
    }
    const badOut = (links?.out || []).filter((l) => l.target !== '_blank');
    check(`11 mock ${m.value} outside links open a new tab`, links && !badOut.length, links ? { outside: links.out.length, wrong: badOut } : 'no links read');
    if (ch) await clickViewer(ch.key, (ch.choices.find((c) => c.rec) || ch.choices[0]).value);
  }
  await goto(recMock, cfg.pages[0].value);
  // 8. Esc closes the sheet; the pill reopens it.
  await evalIn(IN_VIEWER, `document.querySelector('.osh-root input[name="__mock"]:checked').focus()`);
  await key('Escape', 'Escape');
  const closed = await waitFor(IN_VIEWER, `({ open: document.querySelector('.osh-sheet').open, pill: getComputedStyle(document.querySelector('.osh-pill')).display })`, (v) => !v.open, 3000);
  check('8 Esc closes the sheet', closed && !closed.open && closed.pill !== 'none', closed);
  await evalIn(IN_VIEWER, `(document.querySelector('.osh-pill').click(), 1)`);
  const reopened = await evalIn(IN_VIEWER, `document.querySelector('.osh-sheet').open`);
  check('8 the pill reopens it', reopened === true, reopened);
  // 9. Queue without Lavish shows the fallback.
  const st = await evalIn(IN_VIEWER, `(async () => { if (window.lavish) return 'lavish present'; document.querySelector('.osh-form').requestSubmit(); await new Promise((r) => setTimeout(r, 200)); return document.querySelector('[data-osh-status]').textContent; })()`);
  check('9 queue without Lavish shows the copy fallback', st === 'lavish present' || /not running/.test(st || ''), st);
  await evalIn(IN_VIEWER, `(document.querySelector('[data-osh-status]').textContent = '', 1)`);
  return cfg;
}

// ---------- Dock checks (one mock opened on its own) ----------
async function dockChecks(cfg, dockZeroUrl) {
  const s = await waitFor(IN_MOCK, MOCK_STATE, (v) => v.ready, 10000);
  if (!s) throw new SetupError('the mock never loaded for the dock checks');
  cfg ||= await evalIn(IN_MOCK, `JSON.parse(JSON.stringify(VIEWER_CONFIG))`);
  const mock = await evalIn(IN_MOCK, 'MockLive.mock');
  const o0 = await evalIn(IN_MOCK, 'self.origin');
  check('14 dock: the mock runs at an opaque origin', o0 === 'null', o0);
  const pill = await waitFor(IN_MOCK, `(() => { const p = document.querySelector('.osh-root[data-host="dock"] .osh-pill'); if (!p) return null; const r = p.getBoundingClientRect(); return { w: r.width, open: document.querySelector('.osh-sheet').open }; })()`, (v) => v, 4000);
  check('14 dock: the pill shows and the sheet starts closed', pill && pill.w > 0 && pill.open === false, pill);
  await evalIn(IN_MOCK, `(document.querySelector('.osh-pill').click(), 1)`);
  const applies = (o) => !o.only || o.only.includes(mock);
  for (const o of cfg.options) {
    if (!applies(o)) {
      const dis = await evalIn(IN_MOCK, `document.querySelector('.osh-root [data-row="${o.key}"]').disabled`);
      check(`14 dock: ${o.key} disabled under mock ${mock}`, dis === true, dis);
      continue;
    }
    for (const c of o.choices) {
      const tag = `d-${o.key}-${c.value}`; await mark(tag);
      await evalIn(IN_MOCK, `(document.querySelector('.osh-root input[name="${o.key}"][value="${c.value}"]').click(), 1)`);
      const v = await waitFor(IN_MOCK, MOCK_STATE, (x) => x.ds[toDs(o.key)] === c.value, 3000);
      check(`14 dock: ${o.key}=${c.value} applies in place`, v && v.ds[toDs(o.key)] === c.value && v.marker === tag, v && { value: v.ds[toDs(o.key)], marker: v.marker });
    }
  }
  const form = await evalIn(IN_MOCK, `(() => { const vis = (el) => { if (!el) return false; const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0 && r.left >= 0 && r.top >= 0 && r.right <= innerWidth + 0.5 && r.bottom <= innerHeight + 0.5; }; const verdicts = [...document.querySelectorAll('.osh-root input[name="__verdict"]')]; return { note: vis(document.querySelector('.osh-root textarea')), verdict: verdicts.length === 2 && verdicts.every((v) => vis(v)), queue: vis(document.querySelector('.osh-root [data-osh-queue]')), label: document.querySelector('.osh-root [data-osh-queue]')?.textContent || null }; })()`);
  check('14 dock: note, verdict and queue button inside the window', form && form.note && form.verdict && form.queue && /final pick/i.test(form.label || ''), form);
  const fit = await evalIn(IN_MOCK, fitExpr('.osh-sheet'));
  check('14 dock: every sheet control inside the window', fit && fit.n > 0 && !fit.out.length, fit);
  const sw = await mockState();
  check('15 dock: no sideways scroll at 1080', sw && sw.sw <= sw.w, sw && { scrollWidth: sw.sw, innerWidth: sw.w });
  if (dockZeroUrl) {
    await send('Page.navigate', { url: dockZeroUrl });
    const z = await waitFor(IN_MOCK, `({ ready: document.readyState === 'complete', sheet: !!document.querySelector('.osh-root'), dock: document.documentElement.dataset.dock })`, (v) => v.ready && v.dock === '0', 8000);
    check('14 dock: with ?dock=0 no sheet exists', z && z.dock === '0' && z.sheet === false, z);
  }
}

// ---------- Main ----------
let code = 0;
try {
  if (!chrome) throw new SetupError('Chrome not found: set CHROME_PATH');
  if (PORTABLE) {
    if (!fs.existsSync(PORTABLE)) throw new SetupError(`--portable: ${PORTABLE} not found`);
    tmpPortable = fs.mkdtempSync(path.join(os.tmpdir(), 'live-viewer-portable-'));
    fs.copyFileSync(PORTABLE, path.join(tmpPortable, 'page.html'));
    ROOT = tmpPortable;
  }
  OURS = ourNames(ROOT);
  if (!URL_ARG) { server = await serve(ROOT); BASE = `http://127.0.0.1:${server.address().port}`; }
  proc = spawn(chrome, ['--headless=new', '--remote-debugging-port=0', `--user-data-dir=${profile}`, '--no-first-run', `--window-size=${W},${H}`, 'about:blank'], { stdio: 'ignore' });
  let port;
  for (let i = 0; i < 100 && !port; i++) { await sleep(100); try { port = Number(fs.readFileSync(path.join(profile, 'DevToolsActivePort'), 'utf8').split('\n')[0]); } catch {} }
  if (!port) throw new SetupError('Chrome did not start');
  const list = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();
  const page = list.find((t) => t.type === 'page');
  if (!page) throw new SetupError('no page target');
  ws = new WebSocket(page.webSocketDebuggerUrl);
  await new Promise((r, j) => { ws.addEventListener('open', r, { once: true }); ws.addEventListener('error', () => j(new SetupError('debugger connection failed')), { once: true }); });
  ws.addEventListener('message', onMessage);
  await send('Runtime.enable'); await send('Page.enable'); await send('Network.enable');
  await send('Emulation.setDeviceMetricsOverride', { width: W, height: H, deviceScaleFactor: 1, mobile: false });
  await send('Target.setAutoAttach', { autoAttach: true, waitForDebuggerOnStart: true, flatten: true });

  if (PORTABLE) {
    await send('Page.navigate', { url: `${BASE}/page.html` });
    await sleep(4000);
    check('portable: every request loads', !failures.length, failures);
    check('portable: no script error', !scriptErrors.length, scriptErrors);
  } else {
    if (URL_ARG) OURS = ourNames(ROOT);
    const start = URL_ARG || `${BASE}/tools/sandbox-test.html`;
    await send('Page.navigate', { url: start });
    // The viewer wins whenever it exists (its framed mock also matches IN_MOCK); a mock alone
    // counts only once it has finished loading with no viewer around it.
    let hasViewer = null;
    for (const end = Date.now() + 15000; Date.now() < end && !hasViewer;) {
      if (await evalIn(IN_VIEWER, `'viewer'`)) hasViewer = 'viewer';
      else if (await evalIn(IN_MOCK, `document.readyState === 'complete' ? 'mock' : undefined`)) { await sleep(1000); hasViewer = (await evalIn(IN_VIEWER, `'viewer'`)) || 'mock'; }
      else await sleep(200);
    }
    if (!hasViewer) throw new SetupError('neither the viewer (VIEWER_CONFIG and a frame) nor a mock (MockLive) appeared');
    let cfg = null;
    if (hasViewer === 'viewer') {
      await waitFor(IN_MOCK, MOCK_STATE, (v) => v.ready, 15000);
      cfg = await viewerChecks();
      if (SHOT) { await sleep(500); const shot = await send('Page.captureScreenshot', { format: 'png' }); fs.writeFileSync(SHOT, Buffer.from(shot.data, 'base64')); console.log(`shot: ${SHOT}`); }
      if (!URL_ARG) {
        const first = cfg.pages[0].files[(cfg.mocks.find((m) => m.rec) || cfg.mocks[0]).value];
        await send('Page.navigate', { url: `${BASE}/tools/sandbox-test.html?src=../${encodeURIComponent(first)}` });
        await dockChecks(cfg, `${BASE}/tools/sandbox-test.html?src=../${encodeURIComponent(first + '?dock=0')}`);
      }
    } else {
      await dockChecks(null, null);
      if (SHOT) { const shot = await send('Page.captureScreenshot', { format: 'png' }); fs.writeFileSync(SHOT, Buffer.from(shot.data, 'base64')); console.log(`shot: ${SHOT}`); }
    }
    check('0 no request failed and no script error in the mocks folder', !failures.length && !scriptErrors.length, { failures, scriptErrors });
  }
  code = results.every((r) => r.ok) ? 0 : 1;
} catch (e) {
  console.error(`SETUP ERROR: ${e.message}`);
  if (failures.length || scriptErrors.length) console.error(JSON.stringify({ failures, scriptErrors }, null, 1));
  code = e instanceof SetupError ? 2 : 2;
}
const passed = results.filter((r) => r.ok).length;
console.log(`${passed}/${results.length} checks passed${code === 2 ? ' (setup error)' : ''}`);
if (REPORT) fs.writeFileSync(REPORT, JSON.stringify({ when: new Date().toISOString(), url: URL_ARG || BASE, exit: code, results, failures, scriptErrors }, null, 1));
try { ws?.close(); } catch {}
if (proc && proc.exitCode === null) { proc.kill('SIGTERM'); await Promise.race([new Promise((r) => proc.once('exit', r)), sleep(3000)]); if (proc.exitCode === null) proc.kill('SIGKILL'); }
try { fs.rmSync(profile, { recursive: true, force: true }); } catch {}
if (tmpPortable) try { fs.rmSync(tmpPortable, { recursive: true, force: true }); } catch {}
server?.close();
process.exit(code);
