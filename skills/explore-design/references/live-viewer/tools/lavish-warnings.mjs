// lavish-warnings.mjs (explore-design live-viewer template): prints Lavish's own open layout
// findings for one opened page, for the pre-flight before the owner is told the page is ready.
// Usage: node tools/lavish-warnings.mjs <html-file> [--wait <seconds, default 20>]
// Reads ~/.lavish-axi/state.json (read-only). That file is Lavish's internal state, not a
// documented interface: when its shape is not the one this tool knows, it exits 2 with
// "state format changed" instead of printing nothing. Re-check it after a Lavish pin bump.
// Exit 0: no open finding. 1: findings open (printed as rule · selector · overflow_px · viewport).
// 2: no session for the file, no completed diagnostic pass within the wait, or a changed format.
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';

const args = process.argv.slice(2);
const file = args.find((a) => !a.startsWith('--') && args[args.indexOf(a) - 1] !== '--wait');
const wi = args.indexOf('--wait');
const waitS = wi >= 0 ? Number(args[wi + 1]) : 20;
if (!file || !Number.isFinite(waitS)) { console.error('usage: node tools/lavish-warnings.mjs <html-file> [--wait <seconds>]'); process.exit(2); }
const target = path.resolve(file);
const STATE = path.join(os.homedir(), '.lavish-axi', 'state.json');
const CLOSED = new Set(['resolved', 'dismissed']);
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

function load() {
  let s;
  try { s = JSON.parse(fs.readFileSync(STATE, 'utf8')); } catch (e) { return { error: `cannot read ${STATE}: ${e.message}` }; }
  if (!s || typeof s.sessions !== 'object') return { format: true };
  const all = Object.values(s.sessions).filter((x) => x && x.file === target);
  if (!all.length) return { none: true };
  const x = all.find((y) => y.status !== 'ended') || all[all.length - 1];
  if (!Array.isArray(x.layout_warnings) || typeof x.artifact_revision !== 'number' || !x.artifact_load || typeof x.artifact_load.last_pass_sequence !== 'number') return { format: true };
  return { x };
}

const deadline = Date.now() + waitS * 1000;
let r;
for (;;) {
  r = load();
  if (r.error || r.format) break;
  if (r.x && r.x.artifact_load.artifact_revision === r.x.artifact_revision && r.x.artifact_load.last_pass_sequence > 0) break;
  if (Date.now() > deadline) break;
  await sleep(500);
}
if (r.error) { console.error(r.error); process.exit(2); }
if (r.format) { console.error('state format changed: ~/.lavish-axi/state.json no longer has the fields this tool reads; update tools/lavish-warnings.mjs'); process.exit(2); }
if (r.none) { console.error(`no Lavish session for ${target}: open it first (npx -y lavish-axi@0.1.97 <file>)`); process.exit(2); }
const x = r.x;
if (!(x.artifact_load.artifact_revision === x.artifact_revision && x.artifact_load.last_pass_sequence > 0)) {
  console.error(`no completed diagnostic pass for revision ${x.artifact_revision} within ${waitS}s: the page must be open in a browser for Lavish to check it`);
  process.exit(2);
}
const open = x.layout_warnings.filter((w) => !CLOSED.has(w.status));
if (!open.length) { console.log(`no open layout findings (revision ${x.artifact_revision}, session ${x.status})`); process.exit(0); }
console.log(`${open.length} open layout finding(s) (revision ${x.artifact_revision}):`);
for (const w of open) console.log(`  ${w.rule} · ${w.selector} · ${w.overflow_px ?? '?'}px · ${w.viewport_width ?? '?'} (${w.status})`);
process.exit(1);
