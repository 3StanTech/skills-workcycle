// Background measuring tool (skills-workcycle, MIT; see the repository LICENSE).
// Opens a page in a fresh headless Chrome and counts lit pixels on a background canvas:
// near and far from a synthetic cursor, at rest and while hovering, and at the top and
// bottom of the screen while scrolling down and then up. Use it to tune an interactive
// background by numbers instead of by eye; record each reading in the gate log.
//
// Usage: node sky-measure.mjs <url> [selector=canvas]
// Needs Node 22+ (global WebSocket and fetch) and Chrome: CHROME_PATH, else the macOS
// default, else google-chrome / chromium on PATH. The page needs ~1.5 screens of scroll.
// Prints JSON; exits 1 when the canvas is missing or the page throws.
import { spawn, execFileSync } from 'node:child_process';
import { existsSync, mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

const [url, selector = 'canvas'] = process.argv.slice(2);
if (!url) { console.error('usage: node sky-measure.mjs <url> [selector=canvas]'); process.exit(2); }

function findChrome() {
  if (process.env.CHROME_PATH) return process.env.CHROME_PATH;
  const mac = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
  if (existsSync(mac)) return mac;
  for (const name of ['google-chrome', 'google-chrome-stable', 'chromium', 'chromium-browser']) {
    try { return execFileSync('which', [name], { encoding: 'utf8' }).trim(); } catch {}
  }
  return null;
}
const chrome = findChrome();
if (!chrome) { console.error('Chrome not found: set CHROME_PATH'); process.exit(2); }

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const port = 9950 + Math.floor(Math.random() * 40);
const profile = mkdtempSync(join(tmpdir(), 'sky-measure-'));
const proc = spawn(chrome, ['--headless=new', `--remote-debugging-port=${port}`, `--user-data-dir=${profile}`, '--window-size=1440,900', 'about:blank'], { stdio: 'ignore' });
const cleanup = () => { try { proc.kill(); } catch {} try { rmSync(profile, { recursive: true, force: true }); } catch {} };
process.on('exit', cleanup);

let code = 0;
try {
  let list;
  for (let i = 0; i < 60 && !list; i++) { await sleep(150); try { list = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json(); } catch {} }
  if (!list) throw new Error('Chrome did not start');
  const ws = new WebSocket(list.find((t) => t.type === 'page').webSocketDebuggerUrl);
  await new Promise((r, j) => { ws.addEventListener('open', r, { once: true }); ws.addEventListener('error', j, { once: true }); });
  let id = 0; const pend = new Map(), errors = [];
  ws.addEventListener('message', (e) => {
    const m = JSON.parse(e.data);
    if (m.id) pend.get(m.id)?.(m);
    else if (m.method === 'Runtime.exceptionThrown') errors.push(m.params.exceptionDetails.exception?.description?.split('\n')[0] || m.params.exceptionDetails.text);
  });
  const send = (method, params = {}) => new Promise((r) => { const i = ++id; pend.set(i, r); ws.send(JSON.stringify({ id: i, method, params })); });
  await send('Runtime.enable');
  await send('Emulation.setDeviceMetricsOverride', { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false });
  await send('Page.navigate', { url });
  await sleep(4000);

  const expr = `(async () => {
    const cv = document.querySelector(${JSON.stringify(selector)});
    if (!cv || !cv.getContext) return JSON.stringify({ error: 'no canvas matches ${selector.replace(/[`$\\]/g, '')}' });
    const x = cv.getContext('2d'), dpr = cv.width / cv.clientWidth, W = innerWidth, H = innerHeight;
    const wait = (ms) => new Promise((r) => setTimeout(r, ms));
    const count = (cx, cy, r = 160) => { const d = x.getImageData((cx - r) * dpr, (cy - r) * dpr, 2 * r * dpr, 2 * r * dpr).data; let n = 0;
      for (let i = 0; i < d.length; i += 4) if (d[i + 3] > 40 && d[i] > 120 && d[i + 1] > 120 && d[i + 2] > 120) n++; return n; };
    const avg = async (f, k = 10) => { let s = 0; for (let i = 0; i < k; i++) { s += f(); await wait(100); } return Math.round(s / k); };
    const near = [W * 0.7, H / 2], far = [W * 0.2, H / 2];
    const rest = [await avg(() => count(...near)), await avg(() => count(...far))];
    dispatchEvent(new PointerEvent('pointermove', { clientX: near[0], clientY: near[1], pointerType: 'mouse', bubbles: true }));
    await wait(1800);
    const hover = [await avg(() => count(...near)), await avg(() => count(...far))];
    document.dispatchEvent(new PointerEvent('pointerleave')); await wait(3000);
    const dn = [0, 0], up = [0, 0];
    for (let i = 0; i < 24; i++) { scrollBy(0, 30); await wait(60); if (i > 10) { dn[0] += count(W / 2, H * 0.19); dn[1] += count(W / 2, H * 0.81); } }
    await wait(2000);
    for (let i = 0; i < 24; i++) { scrollBy(0, -30); await wait(60); if (i > 10) { up[0] += count(W / 2, H * 0.19); up[1] += count(W / 2, H * 0.81); } }
    return JSON.stringify({ 'rest near/far': rest, 'hover near/far': hover, 'scroll down top/bottom': dn, 'scroll up top/bottom': up });
  })()`;
  const r = await send('Runtime.evaluate', { expression: expr, awaitPromise: true, returnByValue: true });
  const value = JSON.parse(r.result?.result?.value || '{"error":"evaluation failed"}');
  value.errors = errors;
  console.log(JSON.stringify(value, null, 2));
  if (value.error || errors.length) code = 1;
  ws.close();
} catch (e) {
  console.error(String(e?.message || e)); code = 1;
}
cleanup();
process.exit(code);
