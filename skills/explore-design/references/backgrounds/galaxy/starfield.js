// Galaxy background recipe (skills-workcycle, MIT; see the repository LICENSE).
// A dark sky on a <canvas>: drifting stars with parallax and a faint nebula. Every
// effect below is off by default, so the plain call gives a quiet sky; each effect is
// meant to sit behind a live switch while the owner reviews the mock (see README.md).
// Re-made from scratch; several effects were inspired by amicro.dev (MIT, nothing
// copied) and the shockwave by Kubai087's tip 013 (rules rewritten, no prompt used).
//
// Behaviour that is always on: one still frame under prefers-reduced-motion, Save-Data,
// prefers-reduced-data or `still: true` (no drift, twinkle, parallax, pointer or scroll effects); drawing
// paused while the tab is hidden; devicePixelRatio capped at 2; pointer and scroll
// state eased per frame, never drawn per event. Colours come only from CSS custom
// properties on the canvas, read once per build (see README.md for the list).
//
// Options (defaults in `DEFAULTS`):
//   density, drift, parallax, nebula, starBoost, twinkle (0-1), glints (share of near
//   stars that flare with a four-point glint), milky (a diagonal band of faint stars),
//   constellations (count), lineAlpha, nodeAlpha, node ('dot' | 'diamond' | 'none'),
//   interactive (+ base, sparse, radius): richer sky around the cursor and on the side
//   you scroll toward, tilt (depth tilt: near stars follow the cursor most),
//   pull (1 = stars lean toward the cursor, -1 = they bend around it like a lens),
//   horizons (function returning [{ apex, dir: 'in' | 'out' }] in viewport px: black-hole
//   rims at page markers), holeDark, crossing ('off' | 'sweep' | 'ripple' | 'both'),
//   chroma (warm/cool split on a rim), still (force the still frame).
// API: update(next) rebuilds the stars; set(next) changes options without a rebuild;
//   shockwave(x, y) sends one ring across the sky; focusIn() fades the sky in once;
//   redraw(); destroy() removes every listener.

const DEFAULTS = {
  density: 0.00022, drift: 0.012, parallax: 0.18, nebula: true, starBoost: 1, twinkle: 0.28,
  glints: 0, milky: false, constellations: 0, lineAlpha: 0.16, nodeAlpha: 0.55, node: 'dot',
  interactive: false, base: 0.3, sparse: 0.54, radius: 300, tilt: 0, pull: 0,
  horizons: null, holeDark: 0.72, crossing: 'off', chroma: false, still: false,
};

export function starfield(canvas, opts = {}) {
  let o = { ...DEFAULTS, ...opts };
  const ctx = canvas.getContext('2d');
  const reduce = matchMedia('(prefers-reduced-motion: reduce)');
  const saveData = navigator.connection?.saveData === true || matchMedia('(prefers-reduced-data: reduce)').matches;
  const still = () => o.still || reduce.matches || saveData;
  const ac = new AbortController(), on = { passive: true, signal: ac.signal };
  let w = 0, h = 0, stars = [], figs = [], raf = 0, t0 = performance.now(), rand = mulberry(7), focusAnim = null;
  const stopFocus = () => { focusAnim?.cancel(); focusAnim = null; };

  let pal = {};
  function readPalette() {
    const cs = getComputedStyle(canvas), v = (n, f) => cs.getPropertyValue(n).trim() || f;
    const rgb = (n, f) => v(n, f).split(/[\s,]+/).join(','); // "194 65 12" -> "194,65,12"
    pal = {
      white: v('--star', '#ffffff'), cool: v('--star-cool', '#9dbbe6'), warm: v('--star-warm', '#e7a35a'),
      n1: v('--neb-1', 'rgb(22 38 70 / .5)'), n2: v('--neb-2', 'rgb(74 111 165 / .15)'), n3: v('--neb-3', 'rgb(160 110 200 / .05)'),
      line: v('--constellation', v('--star-cool', '#9dbbe6')),
      rim: [rgb('--rim-1', '194 65 12'), rgb('--rim-2', '217 110 30'), rgb('--rim-3', '233 162 92'), rgb('--rim-4', '255 214 160'), rgb('--rim-5', '255 246 234')],
      sweep: rgb('--rim-sweep', '255 244 228'), ripple: rgb('--rim-ripple', '233 162 92'), rippleCore: rgb('--rim-ripple-core', '255 226 190'),
      emberHot: v('--ember-hot', '#ffe3be'), ember: v('--ember', '#e9a25c'),
      chromaWarm: rgb('--chroma-warm', '255 74 48'), chromaCool: rgb('--chroma-cool', '96 164 255'),
      shock: [rgb('--shock-1', '120 150 255'), rgb('--shock-2', '170 120 255'), rgb('--shock-3', '255 130 190'), rgb('--shock-4', '255 190 150')],
    };
  }

  function build() {
    rand = mulberry(7);
    readPalette();
    const dpr = Math.min(2, devicePixelRatio || 1);
    w = canvas.clientWidth; h = canvas.clientHeight;
    canvas.width = Math.round(w * dpr); canvas.height = Math.round(h * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    const n = Math.round(w * h * o.density) + 60;
    stars = Array.from({ length: n }, () => {
      const z = rand(), tint = rand();            // depth: 0 far, 1 near
      return {
        x: rand() * w, y: rand() * h * 1.6, z,
        r: 0.35 + z * z * 1.25, a: 0.25 + z * 0.6,
        tw: rand() * Math.PI * 2, ts: 0.5 + rand() * 2.3, amp: o.twinkle * (0.35 + 0.65 * rand()),
        glint: z > 0.45 && rand() < o.glints, q: rand(),
        c: tint > 0.93 ? 'warm' : tint > 0.78 ? 'cool' : 'white',
      };
    });
    if (o.milky) {                                // faint stars packed along a diagonal
      for (let i = 0, m = Math.round(n * 1.4); i < m; i++) {
        const u = rand(), spread = (rand() + rand() + rand() - 1.5) * h * 0.22;
        stars.push({ x: u * w, y: h * 1.25 - u * h * 0.9 + spread, z: rand() * 0.35, r: 0.3 + rand() * 0.45, a: 0.18 + rand() * 0.3,
          tw: rand() * 6.28, ts: 0.5 + rand(), amp: o.twinkle * 0.5, glint: false, q: rand(), c: rand() > 0.85 ? 'cool' : 'white' });
      }
    }
    figs = Array.from({ length: o.constellations }, (_, i) => {
      const cx = w * (0.08 + 0.84 * rand()), cy = h * (0.1 + 1.35 * (i + rand()) / Math.max(1, o.constellations));
      const pts = Array.from({ length: 4 + Math.floor(rand() * 3) }, () => ({ x: cx + (rand() - 0.5) * 300, y: cy + (rand() - 0.5) * 200 }));
      return { pts, cy, z: 0.35 + rand() * 0.4, phase: i * 1.7 };
    });
  }

  // Pointer and scroll state, eased in draw().
  const ptr = { x: -1e4, y: -1e4, tx: -1e4, ty: -1e4, on: 0, ton: 0 }, tl = { x: 0, y: 0 };
  let flow = 0, flowT = 0, lastSY = scrollY, lastMove = 0;
  addEventListener('pointermove', (e) => {
    if (e.pointerType !== 'mouse' && e.pointerType !== 'pen') return;
    ptr.tx = e.clientX; ptr.ty = e.clientY; ptr.ton = 1;
    if (ptr.x < -1e3) { ptr.x = ptr.tx; ptr.y = ptr.ty; }
  }, on);
  document.addEventListener('pointerleave', () => { ptr.ton = 0; }, on);
  addEventListener('blur', () => { ptr.ton = 0; }, on);
  addEventListener('scroll', () => {
    const d = scrollY - lastSY; lastSY = scrollY;
    if (Math.abs(d) > 1) { flowT = Math.sign(d); lastMove = performance.now(); }
    if (still() && o.horizons) schedule();        // still mode redraws only so rims follow their sections
  }, on);
  const smooth = (a) => (a <= 0 ? 0 : a >= 1 ? 1 : a * a * (3 - 2 * a));
  function richAt(x, y) {
    let L = o.base;
    if (flow) { const f = flow > 0 ? y / h : 1 - y / h; L += (f - L) * Math.abs(flow); }
    if (ptr.on > 0.01) L += (1 - L) * ptr.on * smooth(1 - Math.hypot(x - ptr.x, y - ptr.y) / o.radius);
    return Math.max(0, Math.min(1, L));
  }

  // Shockwaves (tip 013, canvas-only): a ring expands from a point, pushing stars outward
  // as a lens would, with a slight red/blue split and four soft colour rings that fade.
  let waves = [];
  function shockAt(px, py, t) {
    let dx = 0, dy = 0, k = 0;
    for (const s of waves) {
      const age = t - s.t0, D = 1.2; if (age < 0 || age > D) continue;
      const e = 1 - (1 - age / D) ** 3, r = e * s.R, ex = px - s.x, ey = py - s.y, d = Math.hypot(ex, ey) || 1;
      const f = Math.exp(-(((d - r) / 90) ** 2)) * (1 - age / D);
      if (f < 0.01) continue;
      dx += ex / d * 14 * f; dy += ey / d * 14 * f; k = Math.max(k, f);
    }
    return [dx, dy, k];
  }
  function shockRings(t) {
    waves = waves.filter((s) => t - s.t0 < 1.2);
    if (!waves.length) return;
    ctx.save(); ctx.globalCompositeOperation = 'screen';
    for (const s of waves) {
      const p = (t - s.t0) / 1.2, r = (1 - (1 - p) ** 3) * s.R, fade = (1 - p) ** 1.5;
      pal.shock.forEach((c, i) => {
        const ri = r - i * 16; if (ri <= 0) return;
        ctx.beginPath(); ctx.arc(s.x, s.y, ri, 0, Math.PI * 2);
        ctx.lineWidth = 10 - i * 1.5; ctx.strokeStyle = `rgba(${c},${0.16 * fade})`; ctx.stroke();
      });
    }
    ctx.restore();
  }

  function draw(now) {
    raf = 0;
    const frozen = still(), t = frozen ? 0 : (now - t0) / 1000;
    if (frozen) { tl.x = tl.y = 0; ptr.on = 0; flow = 0; waves = []; stopFocus(); }
    else {
      if (o.interactive) { if (performance.now() - lastMove > 900) flowT = 0; flow += (flowT - flow) * (flowT ? 0.08 : 0.03); }
      if (o.interactive || o.pull || o.tilt) { ptr.x += (ptr.tx - ptr.x) * 0.12; ptr.y += (ptr.ty - ptr.y) * 0.12; ptr.on += (ptr.ton - ptr.on) * 0.06; }
      const live = o.tilt && ptr.on > 0.01;
      tl.x += ((live ? (ptr.x / w - 0.5) * ptr.on : 0) - tl.x) * 0.06;
      tl.y += ((live ? (ptr.y / h - 0.5) * ptr.on : 0) - tl.y) * 0.06;
    }
    const sy = frozen ? 0 : scrollY, span = h * 1.6;
    ctx.clearRect(0, 0, w, h);
    if (o.nebula) nebula(-tl.x * 12, -tl.y * 8, sy);
    for (const s of stars) {
      const y = ((s.y - sy * o.parallax * (0.3 + s.z) + t * o.drift * 60 * s.z) % span + span) % span - h * 0.3;
      if (y < -40 || y > h + 40) continue;
      let px = s.x - tl.x * 30 * s.z, py = y - tl.y * 18 * s.z, lensK = 0;
      if (o.pull && !frozen && ptr.on > 0.01) {     // drawn position only; the star keeps its place
        const dx = px - ptr.x, dy = py - ptr.y, d = Math.hypot(dx, dy);
        if (d < 230 && d > 0.5) {
          const f = smooth(1 - d / 230) * ptr.on, a = 36 * f * (0.45 + s.z) * (o.pull > 0 ? -Math.min(1, d / 60) : 1);
          px += dx / d * a; py += dy / d * a; lensK = f;
        }
      }
      let sdx = 0, sdy = 0, sk = 0;
      if (waves.length) { [sdx, sdy, sk] = shockAt(px, py, t); px += sdx; py += sdy; }
      if (py < -4 || py > h + 4) continue;
      let k = 1;
      if (!frozen) { const wave = 0.5 + 0.5 * Math.sin(s.tw + t * s.ts); k = s.glint ? wave ** 4 : wave; }
      let lit = s.glint ? 0.35 + 0.65 * k : 1 - s.amp + s.amp * k, vis = 1, L = 1, boost = o.starBoost;
      if (o.interactive && !frozen) {
        L = richAt(px, py);
        vis = smooth((o.sparse + (1 - o.sparse) * L - s.q) / 0.12 + 0.5);
        if (vis <= 0.01) continue;
        boost = o.starBoost * (0.75 + L);
        if (!s.glint) lit = 1 - s.amp * (0.4 + 0.9 * L) * (1 - k);
      } else if (o.interactive) {
        vis = smooth((o.sparse + (1 - o.sparse) * o.base - s.q) / 0.12 + 0.5);
        if (vis <= 0.01) continue;
      }
      if (lensK) boost *= 1 + 0.7 * lensK;
      const alpha = Math.min(1, s.a * lit * boost * vis);
      if (sk > 0.05) {                              // channel split: red moves 8% further, blue 8% less
        ctx.globalCompositeOperation = 'lighter';
        for (const [m, c] of [[1, pal.chromaWarm], [-1, pal.chromaCool]]) {
          ctx.globalAlpha = alpha * 0.5 * sk; ctx.fillStyle = `rgb(${c})`;
          ctx.beginPath(); ctx.arc(px + m * 0.08 * sdx, py + m * 0.08 * sdy, s.r, 0, Math.PI * 2); ctx.fill();
        }
        ctx.globalCompositeOperation = 'source-over';
      }
      ctx.globalAlpha = alpha; ctx.fillStyle = pal[s.c];
      ctx.beginPath(); ctx.arc(px, py, s.r, 0, Math.PI * 2); ctx.fill();
      if (s.glint && k > 0.3 && (!o.interactive || L > 0.45)) {
        const g = (k - 0.3) / 0.7 * (o.interactive ? smooth((L - 0.45) / 0.35) : 1), len = s.r * (4 + 10 * g);
        ctx.strokeStyle = pal[s.c]; ctx.lineCap = 'round';
        for (const [lw, a, m] of [[0.7, 0.55, 1], [1.2, 0.8, 0.35]]) {
          ctx.lineWidth = lw; ctx.globalAlpha = a * g; ctx.beginPath();
          ctx.moveTo(px - len * m, py); ctx.lineTo(px + len * m, py); ctx.moveTo(px, py - len * m); ctx.lineTo(px, py + len * m); ctx.stroke();
        }
      }
    }
    if (figs.length) constellations(t, sy, frozen);
    ctx.globalAlpha = 1;
    if (o.horizons) blackHole(t, frozen);
    if (waves.length) shockRings(t);
    if (!frozen) schedule();
  }

  function constellations(t, sy, frozen) {
    ctx.lineWidth = 0.6;
    for (const f of figs) {
      const span = h * 1.6, off = f.cy - ((((f.cy - sy * o.parallax * f.z) % span) + span) % span - h * 0.3);
      const pulse = frozen ? 1 : 0.75 + 0.25 * Math.sin(t * 0.5 + f.phase);
      ctx.globalAlpha = o.lineAlpha * pulse; ctx.strokeStyle = pal.line; ctx.beginPath();
      f.pts.forEach((p, i) => (i ? ctx.lineTo(p.x, p.y - off) : ctx.moveTo(p.x, p.y - off)));
      ctx.closePath(); ctx.stroke();
      if (o.node === 'none') continue;
      ctx.globalAlpha = o.nodeAlpha * pulse; ctx.fillStyle = pal.line;
      for (const p of f.pts) {
        const x = p.x, y = p.y - off, s = 2.2; ctx.beginPath();
        if (o.node === 'diamond') { ctx.moveTo(x, y - s); ctx.lineTo(x + s, y); ctx.lineTo(x, y + s); ctx.lineTo(x - s, y); ctx.closePath(); }
        else ctx.arc(x, y, s * 0.7, 0, Math.PI * 2);
        ctx.fill();
      }
    }
  }

  // Black hole: o.horizons() gives the rims on screen. 'in' = the hole lies below the rim
  // (you fall in by scrolling down); 'out' = it lies above (you leave by scrolling down).
  // The interior is darkened over the stars; each rim is an accretion disk that blazes
  // as you approach and cross it.
  const heat = { in: 0.3, out: 0.3 }, lastP = { in: null, out: null }, ev = { in: null, out: null };
  let embers = [], lastT = 0, speed = 0, lastHY = scrollY;
  function arcPts(apex, dir) {
    const Rx = w * 0.95, Ry = Math.max(720, h * 1.05), pts = [];
    for (let i = 0; i <= 72; i++) {
      const x = -60 + (w + 120) * i / 72, dx = (x - w / 2) / Rx;
      pts.push([x, apex + (dir === 'in' ? 1 : -1) * Ry * (1 - Math.sqrt(Math.max(0, 1 - dx * dx)))]);
    }
    return pts;
  }
  function blackHole(t, frozen) {
    const list = o.horizons() || [];
    if (frozen) { embers = []; heat.in = heat.out = 0.3; }
    const dt = Math.min(0.05, Math.max(0.001, t - lastT)); lastT = t;
    const dy = scrollY - lastHY; lastHY = scrollY;
    speed += (Math.min(1, Math.abs(dy) / 28) - speed) * 0.12;
    const hin = list.find((x) => x.dir === 'in'), hout = list.find((x) => x.dir === 'out');
    if (!hin && !hout) { embers = []; return; }
    const top = hin ? arcPts(hin.apex, 'in') : null, bot = hout ? arcPts(hout.apex, 'out') : null;
    const yTop = top ? Math.min(...top.map((p) => p[1])) : -1e5, yBot = bot ? Math.max(...bot.map((p) => p[1])) : 1e5;
    if (yTop < h + 40 && yBot > -40) {
      ctx.save(); ctx.fillStyle = `rgba(0,0,0,${o.holeDark})`; ctx.beginPath();
      if (top) top.forEach(([x, y], i) => (i ? ctx.lineTo(x, y) : ctx.moveTo(x, y))); else { ctx.moveTo(-60, -60); ctx.lineTo(w + 60, -60); }
      if (bot) [...bot].reverse().forEach(([x, y]) => ctx.lineTo(x, y)); else { ctx.lineTo(w + 60, h + 60); ctx.lineTo(-60, h + 60); }
      ctx.closePath(); ctx.fill(); ctx.restore();
    }
    for (const [hz, pts] of [[hin, top], [hout, bot]]) {
      if (!hz) continue;
      const p = hz.apex / h, lp = lastP[hz.dir]; lastP[hz.dir] = p;
      if (lp !== null && o.crossing !== 'off' && !frozen && (lp - 0.5) * (p - 0.5) < 0) ev[hz.dir] = { t0: t, s: p < lp ? 1 : -1 };
      const prox = Math.exp(-(((hz.dir === 'in' ? p - 0.32 : p - 0.62) / 0.34) ** 2));
      heat[hz.dir] += ((frozen ? 0.3 : Math.min(1, 0.22 + 0.5 * prox + 0.55 * speed * prox)) - heat[hz.dir]) * 0.08;
      const H = heat[hz.dir];
      if (Math.max(...pts.map((q) => q[1])) < -140 || Math.min(...pts.map((q) => q[1])) > h + 140) continue;
      rim(pts, H, t, frozen, hz.dir);
      if (!frozen && H > 0.35 && embers.length < 90 && Math.random() < H * 0.9) {
        const [x, y] = pts[Math.floor(Math.random() * pts.length)];
        if (x > 0 && x < w) embers.push({ x, y, vx: (Math.random() - 0.5) * 40, vy: (hz.dir === 'in' ? -1 : 1) * (14 + Math.random() * 46) * H, life: 0, max: 0.8 + Math.random() * 1.2 });
      }
    }
    if (!embers.length) return;
    ctx.save(); ctx.globalCompositeOperation = 'lighter';
    embers = embers.filter((e) => (e.life += dt) < e.max);
    for (const e of embers) {
      e.x += e.vx * dt; e.y += e.vy * dt; const f = 1 - e.life / e.max;
      ctx.globalAlpha = 0.7 * f; ctx.fillStyle = f > 0.6 ? pal.emberHot : pal.ember;
      ctx.beginPath(); ctx.arc(e.x, e.y, 0.6 + 1.1 * f, 0, Math.PI * 2); ctx.fill();
    }
    ctx.restore();
  }
  const line = (pts, dy = 0) => { ctx.beginPath(); pts.forEach(([x, y], i) => (i ? ctx.lineTo(x, y + dy) : ctx.moveTo(x, y + dy))); };
  function rim(pts, H, t, frozen, dir) {
    // Brighter on one side (Doppler), with a slow swirl travelling along the disk.
    const g = (a) => {
      const gr = ctx.createLinearGradient(0, 0, w, 0);
      for (let i = 0; i <= 8; i++) { const u = i / 8, sw = frozen ? 1 : 0.72 + 0.28 * Math.sin(u * Math.PI * 3 - t * 0.9); gr.addColorStop(u, a(Math.max(0, (1.25 - 0.55 * u) * sw))); }
      return gr;
    };
    const layers = [[70 + 120 * H, 0.025 + 0.05 * H], [34 + 60 * H, 0.05 + 0.09 * H], [14 + 22 * H, 0.10 + 0.16 * H], [5 + 7 * H, 0.22 + 0.28 * H], [1.6 + 1.2 * H, 0.75 + 0.25 * H]];
    ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.lineCap = 'round'; ctx.lineJoin = 'round';
    line(pts);
    layers.forEach(([lw, a], i) => { ctx.lineWidth = lw; ctx.strokeStyle = g((k) => `rgba(${pal.rim[i]},${Math.min(1, a * k)})`); ctx.stroke(); });
    if (o.chroma && !frozen) {                      // the hot core splits warm above, cool below
      const off = 1.4 + 2.6 * H, a = 0.26 + 0.42 * H; ctx.lineWidth = 1.3 + 1.5 * H;
      for (const [dy, c] of [[-off, pal.chromaWarm], [off, pal.chromaCool]]) { line(pts, dy); ctx.strokeStyle = `rgba(${c},${a})`; ctx.stroke(); }
    }
    const e = ev[dir];
    if (e) {
      const age = t - e.t0;
      if (age > 1.6) ev[dir] = null;
      else {
        if (o.crossing === 'sweep' || o.crossing === 'both') sweep(pts, age, e.s);
        if (o.crossing === 'ripple' || o.crossing === 'both') ripple(pts, age, dir);
      }
    }
    ctx.restore();
  }
  function sweep(pts, age, s) {                    // one band of light runs along the disk
    const D = 0.95; if (age > D) return;
    const k = age / D, e = k < 0.5 ? 4 * k ** 3 : 1 - (-2 * k + 2) ** 3 / 2, uc = s > 0 ? -0.12 + 1.24 * e : 1.12 - 1.24 * e;
    const band = (alpha) => {
      const gr = ctx.createLinearGradient(0, 0, w, 0), add = (u, a) => { if (u >= 0 && u <= 1) gr.addColorStop(u, `rgba(${pal.sweep},${a})`); };
      gr.addColorStop(0, `rgba(${pal.sweep},0)`); add(uc - 0.1, 0); add(uc - 0.03, alpha * 0.6); add(uc, alpha); add(uc + 0.03, alpha * 0.6); add(uc + 0.1, 0); gr.addColorStop(1, `rgba(${pal.sweep},0)`);
      return gr;
    };
    line(pts);
    for (const [lw, a] of [[26, 0.22], [7, 0.6], [2.2, 1]]) { ctx.lineWidth = lw; ctx.strokeStyle = band(a); ctx.stroke(); }
  }
  function ripple(pts, age, dir) {                 // two faint rings move away from the hole
    for (const [k, s] of [[0, 1], [0.18, 0.55]]) {
      const b = (age - k) / 1.15; if (b <= 0 || b >= 1) continue;
      const f = s * (1 - b) ** 1.8;
      line(pts, (dir === 'in' ? -1 : 1) * (1 - (1 - b) ** 3) * 110);
      ctx.lineWidth = 7 * f + 1; ctx.strokeStyle = `rgba(${pal.ripple},${0.05 * f})`; ctx.stroke();
      ctx.lineWidth = 0.5 + 1.1 * f; ctx.strokeStyle = `rgba(${pal.rippleCore},${0.32 * f})`; ctx.stroke();
    }
  }

  function nebula(ox, oy, sy) {
    const y0 = sy * 0.06 - oy, R = Math.max(w, h);
    for (const [x, y, r, c] of [[w * 0.78, h * 0.18, 0.55, pal.n1], [w * 0.12, h * 0.85, 0.45, pal.n2], [w * 0.55, h * 0.62, 0.3, pal.n3]]) {
      const g = ctx.createRadialGradient(x + ox, y - y0, 0, x + ox, y - y0, R * r);
      g.addColorStop(0, c); g.addColorStop(1, 'rgba(0,0,0,0)');
      ctx.fillStyle = g; ctx.fillRect(0, 0, w, h);
    }
  }

  // One scheduler: at most one frame is ever pending.
  function schedule() { if (!raf && !document.hidden) raf = requestAnimationFrame(draw); }
  build(); schedule();
  addEventListener('resize', () => { build(); schedule(); }, on);
  reduce.addEventListener('change', () => { if (still()) stopFocus(); schedule(); }, on);
  document.addEventListener('visibilitychange', () => { if (document.hidden) { cancelAnimationFrame(raf); raf = 0; } else schedule(); }, on);

  return {
    redraw: schedule,
    update(next) { o = { ...o, ...next }; if (still()) stopFocus(); build(); schedule(); },
    set(next) { o = { ...o, ...next }; if (still()) stopFocus(); schedule(); },
    shockwave(x, y) {
      if (still()) return false;
      waves = waves.slice(-2);                      // at most three rings at once
      waves.push({ x, y, t0: (performance.now() - t0) / 1000, R: Math.hypot(Math.max(x, w - x), Math.max(y, h - y)) });
      schedule(); return true;
    },
    focusIn() {
      stopFocus();
      if (still() || !canvas.animate) return null;
      return focusAnim = canvas.animate([{ opacity: 0, transform: 'scale(1.04)' }, { opacity: 1, transform: 'none' }], { duration: 1400, easing: 'cubic-bezier(.16,1,.3,1)' });
    },
    destroy() { ac.abort(); cancelAnimationFrame(raf); raf = 0; stopFocus(); },
  };
}

function mulberry(a) {
  return () => { a |= 0; a = (a + 0x6d2b79f5) | 0; let t = Math.imul(a ^ (a >>> 15), 1 | a); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
}
