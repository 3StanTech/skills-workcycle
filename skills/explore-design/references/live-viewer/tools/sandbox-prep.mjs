// sandbox-prep.mjs (explore-design live-viewer template; Node 22+, built-ins only).
// Makes a mocks folder safe for Lavish's sandbox IN PLACE, so the folder Lavish opens is the only
// copy (never build a second, Lavish-only copy). Lavish frames every page without
// allow-same-origin: the page runs at an opaque origin, where module scripts, fetch() of local
// files, font files and crossorigin requests fail, and root-relative paths leave the served folder.
//
//   node tools/sandbox-prep.mjs            prepare the folder above tools/
//   node tools/sandbox-prep.mjs --check    change nothing; exit 1 and list what is not sandbox-safe
//   node tools/sandbox-prep.mjs --portable <exported.html>
//                                          finish a `lavish-axi export`: inline the local scripts,
//                                          stylesheets and assets it left as references
//
// What a run does:
//  - bundle (tools/prep.config.json "bundle": src, mods, data, expose, out): the listed ES modules
//    become one classic script exposing window.Mock, JSON files embedded as window.__MOCK_DATA[name];
//  - every page (*.html anywhere under the folder except tools/, classic/, node_modules/ and dot
//    folders; or config "pages" globs): module scripts become classic defer scripts in classic/
//    (same order; each module in its own function scope, imports and exports rewired, a module
//    shared by several entries emitted once and first). The source of each converted script is
//    kept (an inline module is moved beside its page as <page>.module-<n>.mjs) and recorded in
//    tools/prep.manifest.json, and every run rebuilds every converted script from its source, so
//    edit the source and re-run, never the generated file. Module and font preloads are removed;
//    crossorigin is dropped on local tags; root-relative src/href/url() made relative; local fonts
//    embedded as data URIs (local @import chains followed); a ?v=<content hash> stamp is put on
//    local scripts and stylesheets;
//  - stops with the file and line on what it cannot convert faithfully: default exports, import *,
//    re-exports, dynamic import(), import.meta, top-level await, destructuring exports, bare
//    imports, and exported bindings the module reassigns (`export let`/`var`, or an exported local
//    that is assigned again: importers receive values once, at load); on a local fetch(); and on a
//    remote font stylesheet unless config "allowRemoteFonts" lists it.
//  - Saving: nothing is written when anything fails. Otherwise every file is written to a temp
//    name first, then all are renamed into place back to back (assets first, pages last), so no
//    reader ever sees a half-written file. If a rename fails part way, the files already replaced
//    are listed. Idempotent: a second run changes nothing.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { fileURLToPath } from 'node:url';

const TOOLS = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.dirname(TOOLS);
const args = process.argv.slice(2);
const CHECK = args.includes('--check');
const portableAt = args.indexOf('--portable');
const rel = (p) => (path.relative(ROOT, p) || '.').split(path.sep).join('/');
const cfgPath = path.join(TOOLS, 'prep.config.json');
const MANIFEST = path.join(TOOLS, 'prep.manifest.json');
let cfg = {};
try { if (fs.existsSync(cfgPath)) cfg = JSON.parse(fs.readFileSync(cfgPath, 'utf8')); }
catch (e) { console.error(`tools/prep.config.json: ${e.message}`); process.exit(2); }

const writes = new Map(); // path -> new content (pending)
const changes = [];
const errors = [];
const read = (p) => (writes.has(p) ? writes.get(p) : fs.readFileSync(p, 'utf8'));
const exists = (p) => writes.has(p) || fs.existsSync(p);
const put = (p, content, why) => {
  const old = writes.has(p) ? writes.get(p) : fs.existsSync(p) ? fs.readFileSync(p, 'utf8') : null;
  if (old === content) return;
  writes.set(p, content);
  if (!changes.some((c) => c.startsWith(rel(p) + ':'))) changes.push(`${rel(p)}: ${why}`);
};
const lineOf = (text, index) => text.slice(0, index).split('\n').length;
const fail = (file, text, index, msg) => errors.push(`${rel(file)}:${index == null ? '' : lineOf(text, index)}: ${msg}`);
const hash = (s) => crypto.createHash('sha1').update(s).digest('hex').slice(0, 10);
const isLocal = (u) => !!u && !/^(?:[a-z][a-z0-9+.-]*:|\/\/|#)/i.test(u);
const isRootRel = (u) => !!u && u.startsWith('/') && !u.startsWith('//');
const stripQuery = (u) => u.split(/[?#]/)[0];
const FONT_EXT = { woff2: 'font/woff2', woff: 'font/woff', ttf: 'font/ttf', otf: 'font/otf' };
const IMG_EXT = { svg: 'image/svg+xml', png: 'image/png', jpg: 'image/jpeg', jpeg: 'image/jpeg', webp: 'image/webp', gif: 'image/gif', avif: 'image/avif' };
const FONT_HOSTS = /fonts\.googleapis\.com|fonts\.gstatic\.com|use\.typekit\.net|fonts\.bunny\.net|fast\.fonts\.net|fonts\.cdnfonts\.com/i;
const allowedRemote = (u) => (cfg.allowRemoteFonts || []).some((a) => u.includes(a));
const remoteFontLink = (u) => !!u && (FONT_HOSTS.test(u) || /font/i.test(u)) && !allowedRemote(u);
const REMOTE_FONT_FIX = 'remote fonts fail at Lavish\'s opaque origin. Fix: download the font files into the mocks folder and reference them locally (prep embeds them), or use a named system fallback; list the URL under "allowRemoteFonts" in tools/prep.config.json only to accept fallback type in review';
const FETCH_FIX = 'fetch() of a local file fails at Lavish\'s opaque origin. Embed the data instead: for a bundled module add it to "bundle.data" in tools/prep.config.json and read window.__MOCK_DATA[name]; otherwise inline it as <script>window.__MOCK_DATA = {...}</script> before the scripts that read it';

// Resolve a URL or import specifier written in `fromFile` to a path inside ROOT (or null).
function resolveLocal(spec, fromFile) {
  const clean = stripQuery(spec);
  if (!clean) return null;
  if (isRootRel(clean)) return path.join(ROOT, clean);
  if (!isLocal(clean)) return null;
  return path.resolve(path.dirname(fromFile), clean);
}
const relUrl = (target, fromFile) => path.relative(path.dirname(fromFile), target).split(path.sep).join('/') || path.basename(target);

// ---------- HTML attributes (quoted or unquoted) ----------
const ATTR = (name) => new RegExp(`\\s${name}\\s*=\\s*(?:"([^"]*)"|'([^']*)'|([^\\s"'>]+))`, 'i');
const attr = (tag, name) => { const m = tag.match(ATTR(name)); return m ? (m[1] ?? m[2] ?? m[3]) : null; };
const setAttr = (tag, name, value) => tag.replace(ATTR(name), ` ${name}="${value}"`);
const hasAttr = (tag, name) => new RegExp(`\\s${name}(?=[\\s=>/])`, 'i').test(tag);
const isModuleTag = (tag) => (attr(tag, 'type') || '').toLowerCase() === 'module';

// ---------- JS masking: string and template text, comments and regex bodies become spaces ----------
// Template ${…} expressions stay visible (they are code), so imports, exports, await and fetch()
// inside them are seen; nested templates and strings inside them are masked in turn.
// True when the ')' just before index i closes the condition of if/while/for/with, so a '/' there
// starts a regex literal, not a division.
function afterControlParenIn(code, i) {
  let k = i - 1, d = 0;
  while (k >= 0 && /\s/.test(code[k])) k--;
  for (; k >= 0; k--) { if (code[k] === ')') d++; else if (code[k] === '(' && --d === 0) break; }
  return /\b(if|while|for|with)\s*$/.test(code.slice(Math.max(0, k - 8), k));
}
function mask(code) {
  const afterControlParen = (i) => afterControlParenIn(code, i);
  const out = code.split('');
  const blank = (a, b) => { for (let k = a; k < b; k++) if (out[k] !== '\n') out[k] = ' '; };
  // Scan code from i; stop at an unmatched '}' when inExpr (end of a ${…}); return the index reached.
  function scan(i, inExpr) {
    let last = '', depth = 0;
    while (i < code.length) {
      const c = code[i], n = code[i + 1];
      if (c === '/' && n === '/') { const e = code.indexOf('\n', i); const end = e < 0 ? code.length : e; blank(i, end); i = end; continue; }
      if (c === '/' && n === '*') { const e = code.indexOf('*/', i + 2); const end = e < 0 ? code.length : e + 2; blank(i, end); i = end; continue; }
      if (c === '"' || c === "'") {
        let j = i + 1;
        while (j < code.length && code[j] !== c && code[j] !== '\n') { if (code[j] === '\\') j++; j++; }
        blank(i + 1, j); i = j + 1; last = c; continue;
      }
      if (c === '`') {
        let j = i + 1, from = j;
        while (j < code.length && code[j] !== '`') {
          if (code[j] === '\\') { j += 2; continue; }
          if (code[j] === '$' && code[j + 1] === '{') { blank(from, j); j = scan(j + 2, true) + 1; from = j; continue; }
          j++;
        }
        blank(from, j); i = j + 1; last = '`'; continue;
      }
      if (c === '/' && (last === '' || /[(,=:[!&|?{};+\-*%<>~^]/.test(last) || /\b(return|typeof|case|do|else|in|of|void|yield|await)$/.test(code.slice(Math.max(0, i - 8), i).trimEnd()) || (last === ')' && afterControlParen(i)))) {
        let j = i + 1, cls = false;
        while (j < code.length && code[j] !== '\n') { if (code[j] === '\\') { j += 2; continue; } if (code[j] === '[') cls = true; else if (code[j] === ']') cls = false; else if (code[j] === '/' && !cls) break; j++; }
        blank(i + 1, j); i = j + 1; last = '/'; continue;
      }
      if (c === '{') depth++;
      else if (c === '}') { if (inExpr && depth === 0) return i; depth--; }
      if (!/\s/.test(c)) last = c;
      i++;
    }
    return i;
  }
  scan(0, false);
  return out.join('');
}
function depthAt(masked) {
  const d = new Int16Array(masked.length + 1); let k = 0;
  for (let i = 0; i < masked.length; i++) { d[i] = k; const c = masked[i]; if (c === '{' || c === '(' || c === '[') k++; else if (c === '}' || c === ')' || c === ']') k = Math.max(0, k - 1); }
  d[masked.length] = k;
  return d;
}

// Names declared by `const|let|var a = …, b = …` starting at `from` (masked text).
function declaredNames(masked, from) {
  const names = []; let i = from, depth = 0;
  const ident = () => { const m = /^\s*([A-Za-z_$][\w$]*)/.exec(masked.slice(i)); if (!m) return null; i += m[0].length; return m[1]; };
  const first = ident(); if (!first) return null; names.push(first);
  for (; i < masked.length; i++) {
    const c = masked[i];
    if ('([{'.includes(c)) depth++;
    else if (')]}'.includes(c)) { if (depth === 0) break; depth--; }
    else if (depth === 0 && c === ';') break;
    else if (depth === 0 && c === ',') { i++; const n = ident(); if (!n) return null; names.push(n); i--; }
    else if (depth === 0 && c === '\n') {
      const before = masked.slice(0, i).trimEnd().slice(-1), after = masked.slice(i).trimStart()[0];
      if (!/[,?:.+\-*/%&|^=<>]/.test(after || '') && !/^(in|instanceof)\b/.test(masked.slice(i).trimStart()) && !/[,=+\-*/%&|^!?:<>(.]/.test(before)) break;
    }
  }
  return names;
}

// True when `name` is assigned anywhere in the masked module (=, compound =, ++/--, or inside a
// destructuring assignment pattern).
function reassigned(m, name) {
  const L = name.replace(/\$/g, '\\$');
  return new RegExp(`(?<![.\\w$])${L}\\s*(?:[-+*/%&|^]|\\*\\*|<<|>>>?|&&|\\|\\||\\?\\?)?=(?![=>])|(?:\\+\\+|--)\\s*${L}\\b|(?<![.\\w$])${L}\\s*(?:\\+\\+|--)|[\\[{][^\\]}=;]*(?<![.\\w$:])${L}\\b(?!\\s*:)[^\\]}=;]*[\\]}]\\s*=(?![=>])`).test(m);
}

// ---------- ES module -> function-scoped classic code ----------
function convertModule(code, file, key) {
  const m = mask(code), depth = depthAt(m);
  const deps = [], edits = [], exported = [];
  // Names declared at the top level: const (never reassigned) and let/var (reassignable).
  const consts = new Set(), letVar = new Set();
  for (const d of m.matchAll(/\b(const|let|var)\b\s*/g)) {
    if (depth[d.index] !== 0) continue;
    const at = d.index + d[0].length, into = d[1] === 'const' ? consts : letVar;
    if (/^[{[]/.test(m.slice(at))) { let k = at, dd = 0; for (; k < m.length; k++) { if ('{['.includes(m[k])) dd++; else if ('}]'.includes(m[k]) && --dd === 0) break; } for (const x of m.slice(at, k + 1).matchAll(/([A-Za-z_$][\w$]*)\s*(?=[,}\]=]|$)/g)) into.add(x[1]); continue; }
    for (const n of declaredNames(m, at) || []) into.add(n);
  }
  let bad = false;
  const err = (idx, msg) => { fail(file, code, idx, msg); bad = true; };
  const SUPPORTED = 'supported: side-effect imports, import { a, b as c } from \'./x.js\', export function|class|const, a trailing export { … }';
  const depKey = (spec, idx) => {
    const p = resolveLocal(spec, file);
    if (!p) { err(idx, `cannot bundle the bare or remote import '${spec}': vendor the file into the mocks folder and import it by a relative path`); return null; }
    if (!exists(p)) { err(idx, `import '${spec}' not found (${rel(p)})`); return null; }
    deps.push(p);
    return rel(p);
  };
  // await is allowed only inside an async function: find each async function's body range.
  const asyncRanges = [];
  for (const a of m.matchAll(/\basync\b/g)) {
    const arrow = /^\s*(?:function\b[^{]*|[A-Za-z_$][\w$]*\s*=>|\([^)]*\)\s*=>|[A-Za-z_$][\w$]*\s*\([^)]*\)\s*)/.exec(m.slice(a.index + 5));
    if (!arrow) continue;
    let j = a.index + 5 + arrow[0].length;
    while (/\s/.test(m[j] || '')) j++;
    if (m[j] === '{') { let d = 0, k = j; for (; k < m.length; k++) { if (m[k] === '{') d++; else if (m[k] === '}' && --d === 0) break; } asyncRanges.push([j, k]); }
    else { let d = 0, k = j; for (; k < m.length; k++) { const ch = m[k]; if ('([{'.includes(ch)) d++; else if (')]}'.includes(ch)) { if (d === 0) break; d--; } else if (d === 0 && (ch === ',' || ch === ';' || ch === '\n')) break; } asyncRanges.push([j, k]); }
  }
  for (const a of m.matchAll(/\bawait\b/g)) if (!/[.]\s*$/.test(m.slice(0, a.index)) && !/^\s*:/.test(m.slice(a.index + 5)) && !asyncRanges.some(([x, y]) => a.index >= x && a.index < y)) err(a.index, 'await outside an async function (top-level await) cannot run in a classic script; move it inside an async function');
  for (const k of m.matchAll(/\b(import|export)\b/g)) {
    const i = k.index;
    if (m.slice(0, i).trimEnd().endsWith('.') || /^\s*:/.test(m.slice(i + 6))) continue; // obj.import, { export: … }
    if (k[1] === 'import') {
      const after = m.slice(i + 6).trimStart();
      if (after.startsWith('(')) { err(i, `dynamic import() cannot be converted; ${SUPPORTED}`); continue; }
      if (after.startsWith('.meta')) { err(i, 'import.meta has no classic-script equivalent'); continue; }
      if (depth[i] !== 0) continue;
      let r = /import\s*\{([^}]*)\}\s*from\s*(['"])([^'"]+)\2\s*;?/y; r.lastIndex = i;
      let x = r.exec(code);
      if (x) {
        const k2 = depKey(x[3], i);
        if (k2) {
          const binds = x[1].split(',').map((s) => s.trim()).filter(Boolean).map((s) => s.replace(/\s+as\s+/, ': '));
          edits.push([i, i + x[0].length, `const { ${binds.join(', ')} } = window.__prepMods[${JSON.stringify(k2)}];`]);
        }
        continue;
      }
      r = /import\s*(['"])([^'"]+)\1\s*;?/y; r.lastIndex = i; x = r.exec(code);
      if (x) { if (depKey(x[2], i)) edits.push([i, i + x[0].length, '']); continue; }
      if (/^\*\s*as\b/.test(after)) err(i, `cannot convert import * as; ${SUPPORTED}`);
      else err(i, `cannot convert this import (default imports included); ${SUPPORTED}`);
      continue;
    }
    if (depth[i] !== 0) { err(i, 'export inside a block'); continue; }
    const after = m.slice(i + 6);
    let x;
    if (/^\s+default\b/.test(after)) { err(i, `cannot convert export default; ${SUPPORTED}`); continue; }
    if (/^\s*\*/.test(after)) { err(i, `cannot convert export * (re-export); ${SUPPORTED}`); continue; }
    if ((x = /^\s*\{[^}]*\}\s*from\b/.exec(after))) { err(i, `cannot convert export { … } from (re-export); ${SUPPORTED}`); continue; }
    if ((x = /^\s+(?:async\s+)?(?:function\s*\*?|class)\s*([A-Za-z_$][\w$]*)/.exec(after))) {
      if (reassigned(m, x[1])) { err(i, `exported '${x[1]}' is reassigned; importers read an export once, at load. Export a function that returns the value`); continue; }
      exported.push([x[1], x[1]]); edits.push([i, i + 6 + /^\s+/.exec(after)[0].length, '']); continue;
    }
    if ((x = /^\s+(let|var)\b/.exec(after))) { err(i, `export ${x[1]} is a binding importers would read only once; export a const or a function that returns the value`); continue; }
    if ((x = /^\s+const\b\s*/.exec(after))) {
      const at = i + 6 + x[0].length;
      if (/^[{[]/.test(m.slice(at))) { err(i, 'destructuring exports cannot be converted; declare each name'); continue; }
      const names = declaredNames(m, at);
      if (!names) { err(i, 'could not read the names of this export const'); continue; }
      for (const n of names) exported.push([n, n]);
      edits.push([i, i + 6 + /^\s+/.exec(after)[0].length, '']);
      continue;
    }
    if ((x = /^\s*\{([^}]*)\}\s*;?/.exec(after))) {
      for (const n of x[1].split(',').map((s) => s.trim()).filter(Boolean)) {
        const [local, as] = n.split(/\s+as\s+/).map((s) => s.trim());
        if (letVar.has(local)) { err(i, `exported '${local}' is a let/var binding; importers read an export once, at load. Export a const, or a function that returns the value`); continue; }
        if (!consts.has(local)) {
          if (reassigned(m, local)) { err(i, `exported '${local}' is reassigned; importers read an export once, at load. Export a function that returns the value`); continue; }
        }
        exported.push([local, as || local]);
      }
      edits.push([i, i + 6 + x[0].length, '']);
      continue;
    }
    err(i, `cannot convert this export; ${SUPPORTED}`);
  }
  if (bad) return null;
  let out = code;
  for (const [a, b, s] of edits.sort((p, q) => q[0] - p[0])) out = out.slice(0, a) + s + out.slice(b);
  const getters = exported.map(([local, name]) => `get ${JSON.stringify(name)}() { return ${local}; }`).join(', ');
  const body = `// ${key}\n(function () {\n${out}\nwindow.__prepMods[${JSON.stringify(key)}] = { ${getters} };\n})();\n`;
  return { body, deps, exports: exported.map(([, n]) => n) };
}

// Emit a module and its dependencies (dependencies first, each once per output).
function emitGraph(file, emitted, visiting = new Set()) {
  const key = rel(file);
  if (emitted.has(key)) return '';
  if (visiting.has(key)) { errors.push(`${key}: import cycle; break the cycle or merge the files`); return ''; }
  visiting.add(key);
  const code = read(file);
  const c = convertModule(code, file, key);
  if (!c) return '';
  let out = '';
  for (const d of c.deps) out += emitGraph(d, emitted, visiting);
  visiting.delete(key);
  emitted.add(key);
  emitted.exports = emitted.exports || new Map();
  emitted.exports.set(key, c.exports);
  checkFetch(code, file);
  return out + c.body;
}

function checkFetch(code, file) {
  const m = mask(code);
  for (const x of m.matchAll(/\bfetch\s*\(\s*(['"`])/g)) {
    const q = x[1], start = x.index + x[0].length, end = code.indexOf(q, start);
    const u = code.slice(start, end);
    if (isLocal(u) || isRootRel(u)) fail(file, code, x.index, `local fetch('${u}'): ${FETCH_FIX}`);
  }
}

// ---------- CSS: root-relative urls, local fonts embedded, local @import followed ----------
function processCss(css, file, seen = new Set()) {
  seen.add(file);
  let out = css.replace(/@import\s+(?:url\(\s*)?(['"]?)([^'")\s;]+)\1\s*\)?[^;]*;/gi, (m, q, u, idx) => {
    if (/^https?:|^\/\//.test(u)) { if (remoteFontLink(u)) fail(file, css, idx, `remote font import ${u}: ${REMOTE_FONT_FIX}`); return m; }
    const p = resolveLocal(u, file);
    if (!p || !exists(p)) { fail(file, css, idx, `@import ${u} not found`); return m; }
    if (!seen.has(p)) put(p, processCss(read(p), p, seen), 'fonts embedded / urls made relative');
    return isRootRel(u) ? m.replace(u, relUrl(p, file)) : m;
  });
  out = out.replace(/url\(\s*(['"]?)([^'")]+)\1\s*\)/g, (m, q, u, idx) => {
    if (u.startsWith('data:')) return m;
    const ext = (stripQuery(u).match(/\.([a-z0-9]+)$/i) || [])[1]?.toLowerCase();
    if (/^https?:|^\/\//.test(u)) { if (FONT_EXT[ext] && !allowedRemote(u)) fail(file, css, idx, `remote font file ${u}: ${REMOTE_FONT_FIX}`); return m; }
    const p = resolveLocal(u, file);
    if (!p) return m;
    if (FONT_EXT[ext]) {
      if (!fs.existsSync(p)) { fail(file, css, idx, `font ${u} not found (${rel(p)})`); return m; }
      return `url(data:${FONT_EXT[ext]};base64,${fs.readFileSync(p).toString('base64')})`;
    }
    if (isRootRel(u)) return `url(${q}${relUrl(p, file)}${u.slice(stripQuery(u).length)}${q})`;
    return m;
  });
  return out;
}
// Every stylesheet a page uses: linked local files and their local @import chains.
function cssFiles(page, html) {
  const out = [], seen = new Set();
  const walk = (p) => {
    if (seen.has(p) || !exists(p)) return; seen.add(p); out.push(p);
    for (const x of read(p).matchAll(/@import\s+(?:url\(\s*)?(['"]?)([^'")\s;]+)\1/gi)) { const q = resolveLocal(x[2], p); if (q) walk(q); }
  };
  for (const t of html.matchAll(/<link\b[^>]*>/gi)) {
    if ((attr(t[0], 'rel') || '').toLowerCase() !== 'stylesheet') continue;
    const h = attr(t[0], 'href'); if (!isLocal(h) && !isRootRel(h)) continue;
    const p = resolveLocal(h, page); if (p) walk(p);
  }
  for (const st of html.matchAll(/<style\b[^>]*>([\s\S]*?)<\/style>/gi)) {
    for (const x of st[1].matchAll(/@import\s+(?:url\(\s*)?(['"]?)([^'")\s;]+)\1/gi)) { const q = resolveLocal(x[2], page); if (q) walk(q); }
  }
  return out;
}

// ---------- Pages ----------
function listPages() {
  const skip = new Set(['tools', 'node_modules', 'classic']);
  const srcDir = cfg.bundle ? path.join(ROOT, cfg.bundle.src || 'shared/src') : null;
  const found = [];
  const walk = (d) => {
    for (const e of fs.readdirSync(d, { withFileTypes: true })) {
      if (e.name.startsWith('.')) continue;
      const p = path.join(d, e.name);
      if (e.isDirectory()) { if (!(d === ROOT && skip.has(e.name)) && e.name !== 'classic' && e.name !== 'node_modules' && p !== srcDir) walk(p); }
      else if (e.name.endsWith('.html')) found.push(p);
    }
  };
  walk(ROOT);
  if (!cfg.pages) return found;
  const res = cfg.pages.map((g) => new RegExp('^' + g.split('**').map((part) => part.split('*').map((s) => s.replace(/[.+?^${}()|[\]\\]/g, '\\$&')).join('[^/]*')).join('.*') + '$'));
  return found.filter((p) => res.some((r) => r.test(rel(p))));
}

// Manifest of converted entries: out (generated classic script) -> page and source.
let manifest = { entries: [] };
try { if (fs.existsSync(MANIFEST)) manifest = JSON.parse(fs.readFileSync(MANIFEST, 'utf8')); } catch { errors.push('tools/prep.manifest.json is not valid JSON; restore it or delete it with the generated classic/ files'); }
const nextManifest = [];
const banner = (src) => `// GENERATED by tools/sandbox-prep.mjs from ${src}. Do not edit; edit that source and re-run.\nwindow.__prepMods = window.__prepMods || {};\n`;

function transformPage(page) {
  let html = read(page);
  const base = path.basename(page, '.html');
  const emitted = new Set();
  const pageKey = rel(page);
  // 1. One pass over the script tags in document order: a module tag is converted to a classic
  //    defer script; a script converted on an earlier run is rebuilt from its recorded source.
  //    Both share one emitted set, so a shared dependency runs once, before its first user.
  const prev = (manifest.entries || []).filter((e) => e.page === pageKey);
  let n = prev.reduce((a, e) => Math.max(a, e.n), 0);
  html = html.replace(/<script\b([^>]*)>([\s\S]*?)<\/script>/gi, (m, attrs, code) => {
    const tag = `<script${attrs}>`;
    if (!isModuleTag(tag)) {
      const u = attr(tag, 'src'), p = u && resolveLocal(u, page);
      const e = p && prev.find((x) => path.join(ROOT, x.out) === p);
      if (!e) return m;
      const src = path.join(ROOT, e.src);
      if (!exists(src)) { errors.push(`${e.out}: its source ${e.src} is missing; restore it, or remove the script tag and the entry in tools/prep.manifest.json`); return m; }
      put(p, banner(e.src) + emitGraph(src, emitted), 'rebuilt from its source');
      nextManifest.push(e);
      return m;
    }
    const src = attr(tag, 'src');
    n++;
    let srcPath;
    if (src) {
      srcPath = resolveLocal(src, page);
      if (!srcPath) { fail(page, html, html.indexOf(m), `remote module script ${src}: vendor it into the mocks folder`); return m; }
      if (!exists(srcPath)) { fail(page, html, html.indexOf(m), `module script ${src} not found`); return m; }
    } else {
      srcPath = path.join(path.dirname(page), `${base}.module-${n}.mjs`); // beside the page, so its relative imports still resolve
      put(srcPath, code, 'inline module moved here (edit this file and re-run)');
    }
    const out = path.join(path.dirname(page), 'classic', `${base}.${n}.js`);
    put(out, banner(rel(srcPath)) + emitGraph(srcPath, emitted), 'module script converted');
    nextManifest.push({ page: pageKey, n, out: rel(out), src: rel(srcPath) });
    return `<script defer src="${relUrl(out, page)}"></script>`;
  });
  // 2. Module and font preloads removed; crossorigin dropped on local tags.
  html = html.replace(/<link\b[^>]*>/gi, (tag) => {
    const relv = (attr(tag, 'rel') || '').toLowerCase();
    if (relv === 'modulepreload' || (relv === 'preload' && (attr(tag, 'as') || '').toLowerCase() === 'font')) return '';
    return tag;
  });
  html = html.replace(/<(script|link)\b[^>]*>/gi, (tag) => {
    const u = attr(tag, 'src') || attr(tag, 'href');
    if (!hasAttr(tag, 'crossorigin') || !(isLocal(u) || isRootRel(u))) return tag;
    return tag.replace(/\s+crossorigin(?:\s*=\s*(?:"[^"]*"|'[^']*'|[^\s>]+))?/i, '');
  });
  // 3. Root-relative URLs made relative.
  html = html.replace(/(\s(?:src|href|poster|action|data-src)\s*=\s*)(["']?)\/(?!\/)([^"'\s>]*)\2/gi, (m, pre, q, u) => {
    let target = path.join(ROOT, stripQuery(u));
    if (u === '' || stripQuery(u).endsWith('/')) target = path.join(target, 'index.html');
    return `${pre}"${relUrl(target, page)}${u.slice(stripQuery(u).length)}"`;
  });
  // 4. Stylesheets (and their local @import chains) rewritten in place; inline <style> too.
  for (const t of html.matchAll(/<link\b[^>]*>/gi)) {
    if ((attr(t[0], 'rel') || '').toLowerCase() !== 'stylesheet') continue;
    const href = attr(t[0], 'href');
    if (!isLocal(href)) { if (remoteFontLink(href)) fail(page, html, t.index, `remote font stylesheet ${href}: ${REMOTE_FONT_FIX}`); continue; }
    const p = resolveLocal(href, page);
    if (p && exists(p)) put(p, processCss(read(p), p), 'fonts embedded / urls made relative');
    else fail(page, html, t.index, `stylesheet ${href} not found`);
  }
  html = html.replace(/(<style\b[^>]*>)([\s\S]*?)(<\/style>)/gi, (m, a, css, b) => a + processCss(css, page) + b);
  // 5. Local fetch() in classic scripts (inline and local files).
  for (const s of html.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/gi)) {
    const src = attr(`<script${s[1]}>`, 'src');
    if (!src) { checkFetch(s[2], page); continue; }
    const p = resolveLocal(src, page);
    if (p && exists(p) && !/[/\\]classic[/\\]/.test(p) && !/mock\.bundle\.js$/.test(p)) checkFetch(read(p), p);
  }
  put(page, html, 'made sandbox-safe');
}

function stampPage(page) {
  const html = read(page).replace(/<(script|link)\b[^>]*>/gi, (tag, kind) => {
    const name = kind.toLowerCase() === 'script' ? 'src' : 'href';
    if (kind.toLowerCase() === 'link' && (attr(tag, 'rel') || '').toLowerCase() !== 'stylesheet') return tag;
    const u = attr(tag, name);
    if (!isLocal(u)) return tag;
    const p = resolveLocal(u, page);
    if (!p || !exists(p)) return tag;
    return setAttr(tag, name, `${stripQuery(u)}?v=${hash(read(p))}`);
  });
  put(page, html, 'cache-bust stamps');
}

// ---------- Bundle mode ----------
function bundle() {
  const b = cfg.bundle;
  if (!b) return;
  const src = path.join(ROOT, b.src || 'shared/src');
  const outPath = path.join(ROOT, b.out || 'shared/mock.bundle.js');
  const emitted = new Set();
  let body = '';
  for (const m of b.mods || []) {
    const p = path.join(src, m);
    if (!fs.existsSync(p)) { errors.push(`tools/prep.config.json: bundle module ${m} not found in ${rel(src)}`); continue; }
    body += emitGraph(p, emitted);
  }
  let data = '';
  for (const [name, file] of Object.entries(b.data || {})) {
    const p = path.join(src, file);
    try { data += `window.__MOCK_DATA[${JSON.stringify(name)}] = ${JSON.stringify(JSON.parse(fs.readFileSync(p, 'utf8')))};\n`; }
    catch (e) { errors.push(`tools/prep.config.json: data ${name} (${rel(p)}): ${e.message}`); }
  }
  const all = new Map();
  for (const [k, names] of emitted.exports || []) for (const n of names) if (!all.has(n)) all.set(n, k);
  const pairs = [];
  for (const n of b.expose || [...all.keys()]) {
    if (!all.has(n)) errors.push(`tools/prep.config.json: expose '${n}' is not exported by any bundled module`);
    else pairs.push(`${JSON.stringify(n)}: window.__prepMods[${JSON.stringify(all.get(n))}][${JSON.stringify(n)}]`);
  }
  const text = `// GENERATED by tools/sandbox-prep.mjs from ${rel(src)} (${(b.mods || []).join(', ')}${Object.keys(b.data || {}).length ? ' + ' + Object.values(b.data).join(', ') : ''}). Do not edit; edit the sources and re-run.\n` +
    `(function () {\nwindow.__MOCK_DATA = window.__MOCK_DATA || {};\n${data}window.__prepMods = window.__prepMods || {};\n${body}window.Mock = Object.assign(window.Mock || {}, { ${pairs.join(', ')} });\n})();\n`;
  put(outPath, text, 'bundle rebuilt');
}

// ---------- Static check (what Lavish's sandbox will refuse) ----------
function analyse() {
  const issues = [];
  for (const page of listPages()) {
    const html = read(page), r = rel(page);
    for (const t of html.matchAll(/<script\b[^>]*>/gi)) if (isModuleTag(t[0])) issues.push(`${r}:${lineOf(html, t.index)}: module script`);
    for (const x of html.matchAll(/\s(?:src|href|poster|action|data-src)\s*=\s*(["']?)\/(?!\/)[^"'\s>]*\1/gi)) issues.push(`${r}:${lineOf(html, x.index)}: root-relative URL${x[0].trim()}`);
    for (const x of html.matchAll(/<(?:script|link)\b[^>]*>/gi)) { const u = attr(x[0], 'src') || attr(x[0], 'href'); if (hasAttr(x[0], 'crossorigin') && (isLocal(u) || isRootRel(u))) issues.push(`${r}:${lineOf(html, x.index)}: crossorigin on a local file`); }
    for (const x of html.matchAll(/<link\b[^>]*>/gi)) { if ((attr(x[0], 'rel') || '').toLowerCase() === 'stylesheet' && !isLocal(attr(x[0], 'href')) && remoteFontLink(attr(x[0], 'href'))) issues.push(`${r}: remote font stylesheet ${attr(x[0], 'href')}`); }
    const blocks = [[page, [...html.matchAll(/<style\b[^>]*>([\s\S]*?)<\/style>/gi)].map((x) => x[1]).join('\n')], ...cssFiles(page, html).map((p) => [p, read(p)])];
    for (const [f, css] of blocks) {
      for (const x of css.matchAll(/url\(\s*(['"]?)([^'")]+)\1\s*\)/g)) {
        const u = x[2]; if (u.startsWith('data:')) continue;
        const ext = (stripQuery(u).match(/\.([a-z0-9]+)$/i) || [])[1]?.toLowerCase();
        const remote = /^https?:|^\/\//.test(u);
        if (FONT_EXT[ext] && !remote) issues.push(`${rel(f)}: local font not embedded ${u}`);
        if (FONT_EXT[ext] && remote && !allowedRemote(u)) issues.push(`${rel(f)}: remote font ${u}`);
        if (isRootRel(u)) issues.push(`${rel(f)}: root-relative url(${u})`);
      }
      for (const x of css.matchAll(/@import\s+(?:url\(\s*)?(['"]?)(https?:\/\/[^'")\s;]+)/gi)) if (remoteFontLink(x[2])) issues.push(`${rel(f)}: remote font import ${x[2]}`);
    }
    for (const s of html.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/gi)) {
      const src = attr(`<script${s[1]}>`, 'src');
      const f = src ? resolveLocal(src, page) : page;
      const code = src ? (f && exists(f) ? read(f) : '') : s[2];
      const m = mask(code);
      for (const x of m.matchAll(/\bfetch\s*\(\s*(['"`])/g)) { const st = x.index + x[0].length; const u = code.slice(st, code.indexOf(x[1], st)); if (isLocal(u) || isRootRel(u)) issues.push(`${rel(f)}: local fetch('${u}')`); }
    }
  }
  return [...new Set(issues)];
}

// ---------- Save: all files fully written first, then renamed back to back ----------
function saveAll() {
  const tmp = [];
  try {
    for (const [p, c] of writes) { fs.mkdirSync(path.dirname(p), { recursive: true }); fs.writeFileSync(`${p}.prep-tmp`, c); tmp.push(p); }
  } catch (e) {
    for (const p of tmp) { try { fs.rmSync(`${p}.prep-tmp`); } catch {} }
    throw e;
  }
  tmp.sort((a, b) => (a.endsWith('.html') ? 1 : 0) - (b.endsWith('.html') ? 1 : 0)); // pages last
  const done = [];
  try { for (const p of tmp) { fs.renameSync(`${p}.prep-tmp`, p); done.push(p); } }
  catch (e) {
    console.error(`sandbox-prep: rename failed (${e.message}); already replaced: ${done.map(rel).join(', ') || 'none'}; re-run to finish`);
    for (const p of tmp) { try { fs.rmSync(`${p}.prep-tmp`); } catch {} }
    process.exit(2);
  }
}

// ---------- Portable export ----------
function portable(file) {
  const abs = path.resolve(file);
  if (!fs.existsSync(abs)) { console.error(`--portable: ${file} not found`); process.exit(2); }
  let html = fs.readFileSync(abs, 'utf8');
  const find = (u) => { for (const b of [path.dirname(abs), ROOT]) { const p = path.resolve(b, stripQuery(u).replace(/^\//, '')); if (fs.existsSync(p)) return p; } return null; };
  const inlined = [], deferred = [];
  html = html.replace(/<script\b([^>]*)><\/script>/gi, (m, a) => {
    const tag = `<script${a}>`, u = attr(tag, 'src');
    if (!u || !(isLocal(u) || isRootRel(u))) return m;
    const p = find(u);
    if (!p) { errors.push(`--portable: script ${u} not found beside the export or in the mocks folder`); return m; }
    const late = hasAttr(tag, 'defer') || isModuleTag(tag);
    const rest = a.replace(ATTR('src'), '').replace(/\s(defer|async)(?=[\s>/]|$)/gi, '').replace(/\s+crossorigin(?:\s*=\s*(?:"[^"]*"|'[^']*'|[^\s>]+))?/i, '').replace(ATTR('type'), '');
    const out = `<script${rest}>${fs.readFileSync(p, 'utf8').replace(/<\/script/gi, '<\\/script')}</script>`;
    inlined.push(u);
    if (late) { deferred.push(out); return ''; }
    return out;
  });
  const embedAssets = (css, from) => css.replace(/url\(\s*(['"]?)([^'")]+)\1\s*\)/g, (m, q, u) => {
    if (u.startsWith('data:') || !isLocal(u)) return m;
    const f = path.resolve(path.dirname(from), stripQuery(u));
    if (!fs.existsSync(f)) { errors.push(`--portable: ${u} (from ${path.basename(from)}) not found`); return m; }
    const ext = path.extname(f).slice(1).toLowerCase();
    return `url(data:${IMG_EXT[ext] || FONT_EXT[ext] || 'application/octet-stream'};base64,${fs.readFileSync(f).toString('base64')})`;
  });
  const inlineImports = (css, from, seen) => css.replace(/@import\s+(?:url\(\s*)?(['"]?)([^'")\s;]+)\1\s*\)?([^;]*);/gi, (m, q, iu, cond) => {
    if (!isLocal(iu)) return m;
    if (cond.trim()) { errors.push(`--portable: @import ${iu} carries a condition (${cond.trim()}); inlining would drop it. Inline that file by hand inside the matching @media/@supports/@layer block`); return m; }
    const f = path.resolve(path.dirname(from), stripQuery(iu));
    if (seen.has(f) || !fs.existsSync(f)) return seen.has(f) ? '' : (errors.push(`--portable: @import ${iu} not found`), m);
    seen.add(f);
    return embedAssets(inlineImports(processCss(fs.readFileSync(f, 'utf8'), f), f, seen), f);
  });
  html = html.replace(/<link\b[^>]*>/gi, (tag) => {
    if ((attr(tag, 'rel') || '').toLowerCase() !== 'stylesheet') return tag;
    const u = attr(tag, 'href');
    if (!(isLocal(u) || isRootRel(u))) return tag;
    const p = find(u);
    if (!p) { errors.push(`--portable: stylesheet ${u} not found`); return tag; }
    inlined.push(u);
    return `<style>${embedAssets(inlineImports(processCss(fs.readFileSync(p, 'utf8'), p), p, new Set([p])), p)}</style>`;
  });
  // Inline <style> blocks: their local @import chains are inlined the same way.
  html = html.replace(/(<style\b[^>]*>)([\s\S]*?)(<\/style>)/gi, (m, a, css, b) => a + embedAssets(inlineImports(css, abs, new Set()), abs) + b);
  if (deferred.length) html = /<\/body>/i.test(html) ? html.replace(/<\/body>(?![\s\S]*<\/body>)/i, deferred.join('\n') + '\n</body>') : html + deferred.join('\n');
  if (errors.length) { for (const e of errors) console.error('ERROR ' + e); process.exit(1); }
  fs.writeFileSync(abs + '.prep-tmp', html);
  fs.renameSync(abs + '.prep-tmp', abs);
  console.log(inlined.length ? `inlined: ${inlined.join(', ')}` : 'nothing to inline: the file already opens alone');
  process.exit(0);
}

// ---------- Main ----------
if (portableAt >= 0) portable(args[portableAt + 1] || '');
if (CHECK) {
  const issues = analyse();
  if (issues.length) { console.log(`not sandbox-safe (${issues.length}):`); for (const i of issues) console.log('  ' + i); process.exit(1); }
  console.log(`sandbox-safe: ${listPages().length} page(s) checked`);
  process.exit(0);
}
bundle();
const pages = listPages();
for (const p of pages) transformPage(p);
for (const p of pages) stampPage(p);
if (nextManifest.length || fs.existsSync(MANIFEST)) {
  put(MANIFEST, JSON.stringify({ note: 'Written by sandbox-prep.mjs: each converted script and the source it is rebuilt from on every run.', entries: nextManifest.sort((a, b) => a.page.localeCompare(b.page) || a.n - b.n) }, null, 2) + '\n', 'manifest of converted scripts');
}
if (errors.length) {
  console.error(`sandbox-prep: ${errors.length} problem(s); nothing was written.`);
  for (const e of errors) console.error('ERROR ' + e);
  process.exit(1);
}
const left = analyse();
if (left.length) {
  console.error('sandbox-prep: these would remain after prep; nothing was written:');
  for (const i of left) console.error('  ' + i);
  process.exit(1);
}
saveAll();
console.log(changes.length ? `changed ${changes.length} file(s):\n  ${changes.join('\n  ')}` : 'no changes: the folder is already prepared');
