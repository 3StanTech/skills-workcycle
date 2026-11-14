// Background measuring tool (skills-workcycle, MIT; see the repository LICENSE).
// Opens a page in a fresh headless Chrome and counts lit pixels on a background canvas:
// near and far from a synthetic cursor, at rest and while hovering, and at the top and
// bottom of the screen while scrolling down and then up. Use it to tune an interactive
// background by numbers instead of by eye; record each reading in the gate log.
//
// Usage: node sky-measure.mjs <url> [selector=canvas]
// Needs Node 22+ (global WebSocket and fetch) and Chrome: CHROME_PATH, else the macOS
// default, else google-chrome / chromium on PATH. Reads viewport-sized 2D canvases only
// (a WebGL canvas exits with an error). The page needs ~1.5 screens of scroll.
// Prints JSON; exits 1 when the canvas is missing or unsupported, the page throws, or a
// step times out.
import { spawn, execFileSync } from 'node:child_process';
import { existsSync, mkdtempSync, readFileSync, rmSync } from 'node:fs';
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
const timeout = (p, ms, what) => Promise.race([p, sleep(ms).then(() => { throw new Error(`timed out: ${what}`); })]);

// Port 0: Chrome picks a free port and writes it to the profile we own, so we never
// attach to another Chrome that happens to listen on a guessed port.
const profile = mkdtempSync(join(tmpdir(), 'sky-measure-'));
const proc = spawn(chrome, ['--headless=new', '--remote-debugging-port=0', `--user-data-dir=${profile}`, '--window-size=1440,900', 'about:blank'], { stdio: 'ignore' });
// 'error' fires both when the launch fails and when a later kill() fails; only a launch
// failure (no 'spawn' event yet) means there is no process to wait for.
let spawned = false, spawnError = null;
proc.once('spawn', () => { spawned = true; });
const exited = new Promise((r) => { proc.once('exit', r); proc.on('error', (e) => { if (!spawned) { spawnError = e; r(); } }); });

let cleaning = null;
function cleanup() {
  cleaning ??= (async () => {
    const done = () => spawnError || proc.exitCode !== null || proc.signalCode !== null;
    const waitExit = (ms) => Promise.race([exited.then(() => true), sleep(ms).then(() => done())]);
    if (!done()) {
      proc.kill('SIGTERM');
      if (!(await waitExit(3000))) { proc.kill('SIGKILL'); await waitExit(2000); }
    }
    if (done()) { try { rmSync(profile, { recursive: true, force: true }); } catch {} }
    else console.error(`Chrome did not exit; profile left at ${profile}`);
  })();
  return cleaning;
}
for (const sig of ['SIGINT', 'SIGTERM']) process.once(sig, () => { cleanup().then(() => process.exit(130)); });

let code = 0, ws;
try {
  let port;
  for (let i = 0; i < 100 && !port && !spawnError; i++) {
    await sleep(100);
    try { port = Number(readFileSync(join(profile, 'DevToolsActivePort'), 'utf8').split('\n')[0]); } catch {}
  }
  if (spawnError) throw new Error(`Chrome failed to start: ${spawnError.message}`);
  if (!port) throw new Error('Chrome did not start');
  const list = await timeout(fetch(`http://127.0.0.1:${port}/json/list`).then((r) => r.json()), 5000, 'target list');
  const page = list.find((t) => t.type === 'page');
  if (!page) throw new Error('no page target');
  ws = new WebSocket(page.webSocketDebuggerUrl);
  await timeout(new Promise((r, j) => { ws.addEventListener('open', r, { once: true }); ws.addEventListener('error', () => j(new Error('socket error')), { once: true }); }), 5000, 'debugger connection');

  let id = 0; const pend = new Map(), errors = [];
  const failAll = (why) => { for (const { j } of pend.values()) j(new Error(why)); pend.clear(); };
  ws.addEventListener('close', () => failAll('debugger connection closed'));
  ws.addEventListener('error', () => failAll('debugger connection error'));
  ws.addEventListener('message', (e) => {
    const m = JSON.parse(e.data);
    if (m.id && pend.has(m.id)) { pend.get(m.id).r(m); pend.delete(m.id); }
    else if (m.method === 'Runtime.exceptionThrown') errors.push(m.params.exceptionDetails.exception?.description?.split('\n')[0] || m.params.exceptionDetails.text);
  });
  const send = (method, params = {}, ms = 10000) => timeout(new Promise((r, j) => { const i = ++id; pend.set(i, { r, j }); ws.send(JSON.stringify({ id: i, method, params })); }), ms, method);

  await send('Runtime.enable');
  await send('Emulation.setDeviceMetricsOverride', { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false });
  await send('Page.navigate', { url });
  await sleep(4000);

  const sel = JSON.stringify(selector), missing = JSON.stringify(`no canvas matches ${selector}`), webgl = JSON.stringify(`unsupported: ${selector} is not a 2D canvas`);
  const expr = `(async () => {
    const cv = document.querySelector(${sel});
    if (!cv || !cv.getContext) return JSON.stringify({ error: ${missing} });
    const x = cv.getContext('2d');
    if (!x) return JSON.stringify({ error: ${webgl} });
    const dpr = cv.width / cv.clientWidth, W = innerWidth, H = innerHeight;
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
  const r = await send('Runtime.evaluate', { expression: expr, awaitPromise: true, returnByValue: true }, 60000);
  const value = JSON.parse(r.result?.result?.value || '{"error":"evaluation failed"}');
  value.errors = errors;
  console.log(JSON.stringify(value, null, 2));
  if (value.error || errors.length) code = 1;
} catch (e) {
  console.error(String(e?.message || e)); code = 1;
}
try { ws?.close(); } catch {}
await cleanup();
process.exit(code);
