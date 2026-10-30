# Optimisation — full reference

The deep version of Pillar 3. Priority order matters here: images and
JavaScript weight dwarf everything else in typical builds. Fix in the order
listed and stop when it's fast.

## Table of contents
- [Images & media weight](#images--media-weight)
- [JavaScript discipline](#javascript-discipline)
- [Loading & first paint](#loading--first-paint)
- [Fonts](#fonts)
- [Runtime & rendering performance](#runtime--rendering-performance)
- [React-specific](#react-specific)
- [Network & caching](#network--caching)
- [Core Web Vitals targets](#core-web-vitals-targets)
- [Measuring instead of guessing](#measuring-instead-of-guessing)

## Images & media weight

Images are usually most of the page. In descending impact:

1. **Right-size.** Serve dimensions near the display size (≤2× for retina).
   A 4000px photo in a 400px card wastes ~99% of its bytes.
2. **Modern formats.** WebP/AVIF at quality ~75–85 typically cuts JPEG weight
   30–70% with no visible loss. `<picture>` with fallbacks if legacy support
   matters.
3. **Lazy-load below the fold**: `loading="lazy"` on `<img>`/`<iframe>`.
   *Never* lazy-load the LCP/hero image — that delays the thing users are
   waiting for; give it `fetchpriority="high"` instead.
4. **Reserve layout space**: `width`/`height` attributes or `aspect-ratio` on
   every image — this is the single biggest CLS fix.
5. **SVG for icons and flat graphics** — tiny, sharp, styleable. Icon fonts
   are obsolete.
6. **Video**: never as ambient decoration on mobile; `preload="none"` +
   `poster` for player-style embeds; compress hero loops aggressively (a few
   MB max) and honor `prefers-reduced-motion`.

## JavaScript discipline

JS is the most expensive byte type: downloaded, parsed, compiled, executed —
all on the main thread that also handles the user's taps.

- **Question every dependency.** Date formatting (`Intl`), deep clone
  (`structuredClone`), debounce (5 lines), class toggling, simple fetches —
  the platform already does these. A utility library for one function is a
  bad trade.
- **Check before importing.** Confirm a package is in `package.json` (or
  otherwise installed) before writing an import; if it is missing, say so and
  give the install command instead of assuming it exists.
- **Import narrowly** when a dependency earns its place — named imports /
  submodule paths so tree-shaking can drop the rest.
- **Code-split on route/view boundaries** in app-scale builds (dynamic
  `import()`, `React.lazy`); a settings panel's code shouldn't tax the
  landing view.
- **Defer the non-essential**: analytics, chat widgets, and other third-party
  scripts load after the page is interactive. Third-party scripts are the
  most common cause of "why is my fast site slow".
- **Rough budget instinct**: a content page has little business shipping
  >100–200KB of compressed JS; an interactive app earns more, knowingly.

## Loading & first paint

- Scripts: `defer` (or `type="module"`, which defers by default) — never a
  blocking `<script>` in `<head>`.
- Critical, above-the-fold content is server-rendered or static wherever the
  stack allows; a blank div waiting for JS is the slowest possible start.
- Inline the small amount of critical CSS if styles are otherwise a large
  blocking file; load the rest normally.
- `<link rel="preconnect">` to critical third-party origins (fonts, APIs);
  `rel="preload"` for the one or two truly critical assets (hero image, main
  font) — sparingly, preloading everything preloads nothing.
- Show *something* meaningful fast: static shell, skeletons for known-shape
  content, then hydrate/fill.

## Fonts

- `font-display: swap` so text renders in a fallback immediately.
- Subset and limit: each weight/style is a file; 2 families × 2–3 weights is
  usually plenty. Variable fonts consolidate weights when you need many.
- Self-host with `preload` for the primary text font when you control the
  stack.
- System font stack is a legitimate zero-cost choice for utilitarian UIs.

## Runtime & rendering performance

- **Animate only `transform` and `opacity`** — they skip layout and paint.
  Animating `width`/`height`/`top`/`margin` forces layout every frame.
- **Batch DOM reads and writes.** Interleaving (read, write, read, write)
  forces synchronous reflows ("layout thrashing"). Read everything, then
  write everything, or use `requestAnimationFrame`.
- **Debounce/throttle** high-frequency handlers: input-driven search
  (~200–300ms debounce), `scroll`/`resize`/`pointermove` (throttle or rAF).
- **Passive listeners** for scroll/touch handlers that never call
  `preventDefault` (`{ passive: true }`) so scrolling never waits on your JS.
- **`content-visibility: auto`** on long below-fold sections defers their
  rendering cost nearly for free.
- **Long lists**: paginate, incremental render ("show more"), or virtualize
  past a few hundred rows. DOM node count is a real budget.
- **Web Workers** for genuinely heavy computation (parsing large files,
  crunching data) so the main thread stays responsive.

## React-specific

- **Keys**: stable IDs, never array index on reorderable/filterable lists —
  index keys cause state bleeding between rows and pointless re-renders.
- **State placement**: keep state as close to where it's used as possible;
  context that changes often re-renders every consumer — split hot and cold
  context.
- **Derive, don't duplicate**: computed values (`filteredItems`) belong in
  render (or `useMemo` if measured-expensive), not mirrored into state via
  effects. Redundant state desynchronizes.
- **Memoize surgically**: `React.memo` / `useMemo` / `useCallback` where a
  measured hot path justifies it. Blanket memoization adds overhead and
  noise while hiding the real problem (usually state placed too high).
- **Don't create heavy objects/functions in render** that defeat child
  memoization; don't spawn new arrays/objects as props unless children are
  cheap.
- **Effects discipline**: effects are for synchronizing with external systems,
  not for transforming state you already have. Effect-chains that set state
  in cascade are a re-render storm and a bug farm.
- **Uncontrolled inputs / form libraries** for large forms — a controlled
  50-field form re-rendering on every keystroke is felt lag.

## Network & caching

- Compression (gzip/brotli) and HTTP caching are usually platform defaults on
  modern hosts — but verify, don't assume, when you control the stack.
- Cache-busting via hashed filenames + long-lived immutable cache headers for
  static assets; short/no cache for HTML.
- Batch chatty API calls; avoid request waterfalls (fetch in parallel with
  `Promise.all` when calls are independent).
- Paginate/limit API payloads; don't fetch 10,000 records to show 20.
- Show cached/stale data immediately and refresh in background
  (stale-while-revalidate pattern) where freshness tolerances allow.

## Core Web Vitals targets

- **LCP (Largest Contentful Paint) < 2.5s** — the main content is visible.
  Usual fixes: hero image weight/priority, render-blocking scripts, server
  response time.
- **CLS (Cumulative Layout Shift) < 0.1** — nothing jumps. Usual fixes:
  image/embed dimensions, reserved space for ads/banners/dynamic content,
  `font-display` strategy.
- **INP (Interaction to Next Paint) < 200ms** — taps respond. Usual fixes:
  long tasks on the main thread, unthrottled handlers, oversized React
  re-renders.

## Measuring instead of guessing

When you can run tools: Lighthouse (lab overview), the browser Performance
panel (main-thread flame chart), the Network panel sorted by size (payload
truth), and a bundle analyzer when JS weight is the suspect. When you can't
(e.g. generating code in a chat), apply the budgets and defaults above — they
are exactly the things measurement almost always ends up pointing at — and
say which assumptions deserve a real measurement pass in the user's
environment.

Optimize in evidence order: weight (images, JS) → blocking (first paint) →
runtime (thrash, re-renders). Micro-optimizations (loop styles, string
concat) are noise until the big three are clean.
