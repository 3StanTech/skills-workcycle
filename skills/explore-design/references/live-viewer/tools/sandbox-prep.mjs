// sandbox-prep.mjs (explore-design live-viewer template; Node 22+, built-ins only).
// Makes a mocks folder safe for Lavish's sandbox IN PLACE, so the folder Lavish opens is the only
// copy (never build a second, Lavish-only copy). Lavish frames every page without
// allow-same-origin: the page runs at an opaque origin, where module scripts, fetch() of local
// files, font files and crossorigin requests fail, and root-relative paths leave the served folder.
//
//   node tools/sandbox-prep.mjs            prepare the folder above tools/
//   node tools/sandbox-prep.mjs --check    change nothing; exit 1 and list what is not sandbox-safe
//   node tools/sandbox-prep.mjs --portable <exported.html>
//                                          finish a `lavish-axi export`: inline the local scripts
//                                          and stylesheets it left as references
//
// What a run does:
//  - bundle (tools/prep.config.json "bundle": src, mods, data, expose, out): the listed ES modules
//    become one classic script exposing window.Mock, JSON files embedded as window.__MOCK_DATA[name];
//  - every page (*.html at the root and one level down, or config "pages"): module scripts become
//    classic defer scripts in classic/ (same order; each module in its own function scope, imports
//    and exports rewired, a module shared by several entries emitted once and first); module and
//    font preloads removed; crossorigin removed from local tags; root-relative src/href/url() made
//    relative; local fonts embedded as data URIs; a ?v=<content hash> stamp on local scripts and
//    stylesheets;
//  - stops with the file and line on what it cannot convert (default exports, import *, re-exports,
//    dynamic import(), import.meta, bare imports), on a local fetch(), and on a remote font
//    stylesheet unless config "allowRemoteFonts" lists it. Nothing is written when anything fails;
//    otherwise every file is written to a temp name and renamed over its target in one pass, so a
//    page open in Lavish never loads a half-written folder. Idempotent: a second run changes nothing.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { fileURLToPath } from 'node:url';

const TOOLS = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.dirname(TOOLS);
const args = process.argv.slice(2);
const CHECK = args.includes('--check');
const portableAt = args.indexOf('--portable');
const rel = (p) => path.relative(ROOT, p) || '.';
const cfgPath = path.join(TOOLS, 'prep.config.json');
let cfg = {};
try { if (fs.existsSync(cfgPath)) cfg = JSON.parse(fs.readFileSync(cfgPath, 'utf8')); }
catch (e) { console.error(`tools/prep.config.json: ${e.message}`); process.exit(2); }

const writes = new Map(); // path -> new content (pending)
const changes = [];
const errors = [];
const read = (p) => (writes.has(p) ? writes.get(p) : fs.readFileSync(p, 'utf8'));
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
const stripQuery = (u) => u.split(/[?#]/)[0];
const FONT_EXT = { woff2: 'font/woff2', woff: 'font/woff', ttf: 'font/ttf', otf: 'font/otf' };
const FONT_HOSTS = /fonts\.googleapis\.com|fonts\.gstatic\.com|use\.typekit\.net|fonts\.bunny\.net|fast\.fonts\.net|fonts\.cdnfonts\.com/i;
const allowedRemote = (u) => (cfg.allowRemoteFonts || []).some((a) => u.includes(a));
const REMOTE_FONT_FIX = 'remote fonts fail at Lavish\'s opaque origin. Fix: download the font files into the mocks folder and reference them locally (prep embeds them), or use a named system fallback; list the URL under "allowRemoteFonts" in tools/prep.config.json only to accept fallback type in review';
const FETCH_FIX = 'fetch() of a local file fails at Lavish\'s opaque origin. Embed the data instead: for a bundled module add it to "bundle.data" in tools/prep.config.json and read window.__MOCK_DATA[name]; otherwise inline it as <script>window.__MOCK_DATA = {...}</script> before the scripts that read it';

// Resolve a URL or import specifier written in `fromFile` to a path inside ROOT (or null).
function resolveLocal(spec, fromFile) {
  const clean = stripQuery(spec);
  if (!clean) return null;
  if (clean.startsWith('/') && !clean.startsWith('//')) return path.join(ROOT, clean);
  if (!isLocal(clean)) return null;
  return path.resolve(path.dirname(fromFile), clean);
}
const relUrl = (target, fromFile) => {
  let r = path.relative(path.dirname(fromFile), target).split(path.sep).join('/');
  if (!r) r = path.basename(target);
  return r;
};

// ---------- ES module -> function-scoped classic code ----------
const UNSUPPORTED = [
  [/\bexport\s+default\b/g, 'export default'],
  [/\bexport\s*\*/g, 'export * (re-export)'],
  [/\bexport\s*\{[^}]*\}\s*from\b/g, 'export { … } from (re-export)'],
  [/\bimport\s*\*\s*as\b/g, 'import * as'],
  [/\bimport\s+[A-Za-z_$][\w$]*\s*(?:,|\bfrom\b)/g, 'default import'],
  [/\bimport\s*\(/g, 'dynamic import()'],
  [/\bimport\.meta\b/g, 'import.meta'],
];
function convertModule(code, file, key) {
  const deps = [];
  let bad = false;
  for (const [re, what] of UNSUPPORTED) {
    for (const m of code.matchAll(re)) { fail(file, code, m.index, `cannot convert ${what}; rewrite it as a named export/import (supported: side-effect imports, import { a, b as c } from './x.js', export function|class|const|let|var, a trailing export { … })`); bad = true; }
  }
  if (bad) return null;
  const depKey = (spec, idx) => {
    const p = resolveLocal(spec, file);
    if (!p) { fail(file, code, idx, `cannot bundle the bare or remote import '${spec}': vendor the file into the mocks folder and import it by a relative path`); return null; }
    if (!fs.existsSync(p)) { fail(file, code, idx, `import '${spec}' not found (${rel(p)})`); return null; }
    deps.push(p);
    return rel(p);
  };
  let out = code.replace(/\bimport\s*\{([^}]*)\}\s*from\s*(['"])([^'"]+)\2\s*;?/g, (m, names, q, spec, idx) => {
    const k = depKey(spec, idx);
    const binds = names.split(',').map((s) => s.trim()).filter(Boolean).map((s) => s.replace(/\s+as\s+/, ': '));
    return k ? `const { ${binds.join(', ')} } = window.__prepMods[${JSON.stringify(k)}];` : m;
  });
  out = out.replace(/\bimport\s*(['"])([^'"]+)\1\s*;?/g, (m, q, spec, idx) => (depKey(spec, idx) ? '' : m));
  const exported = [];
  for (const m of out.matchAll(/\bexport\s+(?:async\s+)?(?:function\s*\*?|class|const|let|var)\s*([A-Za-z_$][\w$]*)/g)) exported.push([m[1], m[1]]);
  out = out.replace(/\bexport\s+(?=(?:async\s+)?function|class\b|const\b|let\b|var\b)/g, '');
  out = out.replace(/\bexport\s*\{([^}]*)\}\s*;?/g, (m, names) => {
    for (const n of names.split(',').map((s) => s.trim()).filter(Boolean)) { const [local, as] = n.split(/\s+as\s+/); exported.push([local.trim(), (as || local).trim()]); }
    return '';
  });
  const exp = exported.map(([local, name]) => `${JSON.stringify(name)}: ${local}`).join(', ');
  const body = `// ${key}\n(function () {\n${out}\nwindow.__prepMods[${JSON.stringify(key)}] = { ${exp} };\n})();\n`;
  return { body, deps, exports: exported.map(([, n]) => n) };
}

// Emit a module and its dependencies (dependencies first, each once per output).
function emitGraph(file, emitted, visiting = new Set(), inlineCode = null, inlineKey = null) {
  const key = inlineKey || rel(file);
  if (emitted.has(key)) return '';
  if (visiting.has(key)) { errors.push(`${key}: import cycle; break the cycle or merge the files`); return ''; }
  visiting.add(key);
  const code = inlineCode ?? read(file);
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
  for (const m of code.matchAll(/\bfetch\(\s*(['"`])([^'"`]*)\1/g)) {
    if (isLocal(m[2]) || (m[2].startsWith('/') && !m[2].startsWith('//'))) fail(file, code, m.index, `local fetch('${m[2]}'): ${FETCH_FIX}`);
  }
}

// ---------- CSS: root-relative urls, local fonts embedded, remote fonts refused ----------
function processCss(css, file, ownerForUrls) {
  let out = css.replace(/@import\s+(?:url\()?\s*(['"]?)(https?:\/\/[^'")\s]+)\1\s*\)?[^;]*;/g, (m, q, u, idx) => {
    if ((FONT_HOSTS.test(u) || /font/i.test(u)) && !allowedRemote(u)) fail(file, css, idx, `remote font import ${u}: ${REMOTE_FONT_FIX}`);
    return m;
  });
  out = out.replace(/url\(\s*(['"]?)([^'")]+)\1\s*\)/g, (m, q, u, idx) => {
    if (u.startsWith('data:')) return m;
    const ext = (stripQuery(u).match(/\.([a-z0-9]+)$/i) || [])[1]?.toLowerCase();
    if (/^https?:|^\/\//.test(u)) {
      if (FONT_EXT[ext] && !allowedRemote(u)) fail(file, css, idx, `remote font file ${u}: ${REMOTE_FONT_FIX}`);
      return m;
    }
    const p = resolveLocal(u, ownerForUrls);
    if (!p) return m;
    if (FONT_EXT[ext]) {
      if (!fs.existsSync(p)) { fail(file, css, idx, `font ${u} not found (${rel(p)})`); return m; }
      return `url(data:${FONT_EXT[ext]};base64,${fs.readFileSync(p).toString('base64')})`;
    }
    if (u.startsWith('/')) return `url(${q}${relUrl(p, ownerForUrls)}${u.slice(stripQuery(u).length)}${q})`;
    return m;
  });
  return out;
}

// ---------- Pages ----------
function listPages() {
  const pats = cfg.pages;
  const found = [];
  const skip = new Set(['tools', 'node_modules', 'classic', '.git']);
  for (const e of fs.readdirSync(ROOT, { withFileTypes: true })) {
    if (e.isFile() && e.name.endsWith('.html')) found.push(path.join(ROOT, e.name));
    else if (e.isDirectory() && !skip.has(e.name) && !e.name.startsWith('.')) {
      for (const f of fs.readdirSync(path.join(ROOT, e.name))) if (f.endsWith('.html')) found.push(path.join(ROOT, e.name, f));
    }
  }
  if (!pats) return found;
  const res = pats.map((g) => new RegExp('^' + g.split('*').map((s) => s.replace(/[.+?^${}()|[\]\\]/g, '\\$&')).join('[^/]*') + '$'));
  return found.filter((p) => res.some((r) => r.test(rel(p).split(path.sep).join('/'))));
}
const attr = (tag, name) => { const m = tag.match(new RegExp(`\\s${name}\\s*=\\s*(["'])([^"']*)\\1`, 'i')); return m ? m[2] : null; };
const hasAttr = (tag, name) => new RegExp(`\\s${name}(\\s|=|>|/)`, 'i').test(tag);

function transformPage(page) {
  let html = read(page);
  const base = path.basename(page, '.html');
  const emitted = new Set();
  let n = 0;
  // 1. Module scripts -> classic defer scripts.
  html = html.replace(/<script\b([^>]*)>([\s\S]*?)<\/script>/gi, (m, attrs, code) => {
    if (!/\btype\s*=\s*["']module["']/i.test(attrs)) return m;
    const src = attr(m.slice(0, m.indexOf('>') + 1), 'src');
    let body;
    if (src) {
      const p = resolveLocal(src, page);
      if (!p) { fail(page, html, html.indexOf(m), `remote module script ${src}: vendor it into the mocks folder`); return m; }
      if (!fs.existsSync(p)) { fail(page, html, html.indexOf(m), `module script ${src} not found`); return m; }
      body = emitGraph(p, emitted);
    } else {
      body = emitGraph(page, emitted, new Set(), code, `${rel(page)}#inline-${n + 1}`);
    }
    const out = path.join(path.dirname(page), 'classic', `${base}.${++n}.js`);
    put(out, `// GENERATED by tools/sandbox-prep.mjs from ${src || 'an inline module'} in ${path.basename(page)}. Do not edit.\nwindow.__prepMods = window.__prepMods || {};\n${body}`, 'module script converted');
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
    if (!hasAttr(tag, 'crossorigin') || !(isLocal(u) || (u && u.startsWith('/') && !u.startsWith('//')))) return tag;
    return tag.replace(/\s+crossorigin(?:\s*=\s*(["'])[^"']*\1)?/i, '');
  });
  // 3. Root-relative URLs made relative.
  html = html.replace(/(\s(?:src|href|poster|action|data-src)\s*=\s*)(["'])\/(?!\/)([^"']*)\2/gi, (m, pre, q, u) => {
    let target = path.join(ROOT, stripQuery(u));
    const tail = u.slice(stripQuery(u).length);
    if (u === '' || stripQuery(u).endsWith('/')) target = path.join(target, 'index.html');
    return `${pre}${q}${relUrl(target, page)}${tail}${q}`;
  });
  // 4. Stylesheets: linked local ones rewritten in place; inline <style> blocks too.
  html = html.replace(/<link\b[^>]*>/gi, (tag) => {
    if ((attr(tag, 'rel') || '').toLowerCase() !== 'stylesheet') return tag;
    const href = attr(tag, 'href');
    if (!isLocal(href)) {
      if (href && (FONT_HOSTS.test(href) || /font/i.test(href)) && !allowedRemote(href)) fail(page, html, html.indexOf(tag), `remote font stylesheet ${href}: ${REMOTE_FONT_FIX}`);
      return tag;
    }
    const p = resolveLocal(href, page);
    if (p && fs.existsSync(p)) put(p, processCss(read(p), p, p), 'fonts embedded / urls made relative');
    else fail(page, html, html.indexOf(tag), `stylesheet ${href} not found`);
    return tag;
  });
  html = html.replace(/(<style\b[^>]*>)([\s\S]*?)(<\/style>)/gi, (m, a, css, b) => a + processCss(css, page, page) + b);
  // 5. Local fetch() in classic scripts (inline and local files).
  for (const m of html.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/gi)) {
    const src = attr(`<script${m[1]}>`, 'src');
    if (!src) { checkFetch(m[2], page); continue; }
    const p = resolveLocal(src, page);
    if (p && fs.existsSync(p) && !/\.generated\b|mock\.bundle\.js$/.test(p)) checkFetch(read(p), p);
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
    if (!p || !(writes.has(p) || fs.existsSync(p))) return tag;
    const v = hash(read(p));
    const clean = stripQuery(u) + `?v=${v}`;
    return tag.replace(new RegExp(`(\\s${name}\\s*=\\s*)(["'])[^"']*\\2`, 'i'), `$1$2${clean}$2`);
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
  const expose = b.expose || [...all.keys()];
  const pairs = [];
  for (const n of expose) {
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
    if (/<script\b[^>]*\btype\s*=\s*["']module["']/i.test(html)) issues.push(`${r}: module script`);
    for (const m of html.matchAll(/\s(?:src|href|poster|action)\s*=\s*(["'])\/(?!\/)[^"']*\1/gi)) issues.push(`${r}:${lineOf(html, m.index)}: root-relative URL${m[0].trim()}`);
    for (const m of html.matchAll(/<(?:script|link)\b[^>]*\scrossorigin\b[^>]*>/gi)) { const u = attr(m[0], 'src') || attr(m[0], 'href'); if (isLocal(u)) issues.push(`${r}:${lineOf(html, m.index)}: crossorigin on a local file`); }
    const cssBlocks = [[page, [...html.matchAll(/<style\b[^>]*>([\s\S]*?)<\/style>/gi)].map((x) => x[1]).join('\n')]];
    for (const m of html.matchAll(/<link\b[^>]*>/gi)) {
      if ((attr(m[0], 'rel') || '').toLowerCase() !== 'stylesheet') continue;
      const href = attr(m[0], 'href');
      if (!isLocal(href)) { if (href && (FONT_HOSTS.test(href) || /font/i.test(href)) && !allowedRemote(href)) issues.push(`${r}: remote font stylesheet ${href}`); continue; }
      const p = resolveLocal(href, page);
      if (p && fs.existsSync(p)) cssBlocks.push([p, read(p)]);
    }
    for (const [f, css] of cssBlocks) {
      for (const m of css.matchAll(/url\(\s*(['"]?)([^'")]+)\1\s*\)/g)) {
        const u = m[2]; if (u.startsWith('data:')) continue;
        const ext = (stripQuery(u).match(/\.([a-z0-9]+)$/i) || [])[1]?.toLowerCase();
        if (FONT_EXT[ext] && !/^https?:|^\/\//.test(u)) issues.push(`${rel(f)}: local font not embedded ${u}`);
        if (FONT_EXT[ext] && /^https?:|^\/\//.test(u) && !allowedRemote(u)) issues.push(`${rel(f)}: remote font ${u}`);
        if (u.startsWith('/') && !u.startsWith('//')) issues.push(`${rel(f)}: root-relative url(${u})`);
      }
    }
    for (const m of html.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/gi)) {
      const src = attr(`<script${m[1]}>`, 'src');
      const [f, code] = src ? [resolveLocal(src, page), null] : [page, m[2]];
      const text = code ?? (f && fs.existsSync(f) ? read(f) : '');
      for (const x of text.matchAll(/\bfetch\(\s*(['"`])([^'"`]*)\1/g)) if (isLocal(x[2]) || (x[2].startsWith('/') && !x[2].startsWith('//'))) issues.push(`${rel(f)}: local fetch('${x[2]}')`);
    }
  }
  return [...new Set(issues)];
}

// ---------- Save all at once ----------
function saveAll() {
  const tmp = [];
  try {
    for (const [p, c] of writes) {
      fs.mkdirSync(path.dirname(p), { recursive: true });
      const t = `${p}.prep-tmp`;
      fs.writeFileSync(t, c);
      tmp.push([t, p]);
    }
  } catch (e) {
    for (const [t] of tmp) { try { fs.rmSync(t); } catch {} }
    throw e;
  }
  for (const [t, p] of tmp) fs.renameSync(t, p);
}

// ---------- Portable export ----------
function portable(file) {
  const abs = path.resolve(file);
  if (!fs.existsSync(abs)) { console.error(`--portable: ${file} not found`); process.exit(2); }
  let html = fs.readFileSync(abs, 'utf8');
  const find = (u) => { for (const b of [path.dirname(abs), ROOT]) { const p = path.resolve(b, stripQuery(u).replace(/^\//, '')); if (fs.existsSync(p)) return p; } return null; };
  const inlined = [], deferred = [];
  html = html.replace(/<script\b([^>]*)\bsrc\s*=\s*(["'])([^"']+)\2([^>]*)><\/script>/gi, (m, a, q, u, b) => {
    if (!isLocal(u) && !(u.startsWith('/') && !u.startsWith('//'))) return m;
    const p = find(u);
    if (!p) { errors.push(`--portable: script ${u} not found beside the export or in the mocks folder`); return m; }
    const rest = (a + b).replace(/\s(defer|async|crossorigin)(?:\s*=\s*(["'])[^"']*\2)?/gi, '').replace(/\stype\s*=\s*["']module["']/i, '');
    const tag = `<script${rest}>${fs.readFileSync(p, 'utf8').replace(/<\/script/gi, '<\\/script')}</script>`;
    inlined.push(u);
    if (/\sdefer\b|type\s*=\s*["']module/i.test(a + b)) { deferred.push(tag); return ''; }
    return tag;
  });
  html = html.replace(/<link\b[^>]*>/gi, (tag) => {
    if ((attr(tag, 'rel') || '').toLowerCase() !== 'stylesheet') return tag;
    const u = attr(tag, 'href');
    if (!isLocal(u)) return tag;
    const p = find(u);
    if (!p) { errors.push(`--portable: stylesheet ${u} not found`); return tag; }
    inlined.push(u);
    return `<style>${processCss(fs.readFileSync(p, 'utf8'), p, p)}</style>`;
  });
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
