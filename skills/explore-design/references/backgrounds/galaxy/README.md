# Galaxy recipe

The first worked type in the [background menu](../../backgrounds.md): a dark sky of drifting stars on one canvas, with optional effects for an interactive or cinematic page. Plain JavaScript, no dependencies. Offer it only on a dark direction or a dark section; the sky is meant to sit on near-black.

## Files

| File | What it is |
|---|---|
| `starfield.js` | The sky (ES module, `starfield(canvas, options)`) |
| `sky-measure.mjs` | Measuring tool for any viewport-sized 2D canvas background (Node 22+, headless Chrome) |

Copy both into the mocks folder's `background/` folder. Never edit them in place in the skills; a project's tuning lives in its mock and later its build.

## Mount

```html
<canvas class="sky" aria-hidden="true"></canvas>
<style>
  .sky { position: fixed; inset: 0; width: 100%; height: 100%; z-index: 0; pointer-events: none; }
  main { position: relative; z-index: 1; }
</style>
<script type="module">
  import { starfield } from './background/starfield.js';
  const sky = starfield(document.querySelector('.sky'), { interactive: true });
  sky.focusIn();
</script>
```

**In Lavish (and any sandboxed review):** module scripts do not load. Bundle `starfield.js` with the mocks folder's `tools/sandbox-prep.mjs` (add it to `bundle.mods` and `starfield` to `bundle.expose` in `tools/prep.config.json`, with the file in `shared/src/`), then call it from a classic script after the bundle:

```html
<script src="shared/mock.bundle.js"></script>
<script>Mock.starfield(document.querySelector('.sky'), { interactive: true }).focusIn();</script>
```

`starfield.js` itself is unchanged. See [live viewer](../../live-viewer.md).

The canvas is decoration: `aria-hidden`, no pointer input, and nothing on the page depends on it. Pointer and scroll are read from the window.

## Options

Every effect is off by default; the plain call gives stars, nebula, parallax and twinkle.

| Option | Default | What it does | Live switch |
|---|---|---|---|
| `density` | 0.00022 | Stars per square pixel (plus 60) | Density (rebuild) |
| `drift`, `parallax` | 0.012, 0.18 | Slow drift; how far near stars move against scroll | — |
| `nebula` | true | Three soft colour clouds | Nebula |
| `starBoost`, `twinkle` | 1, 0.28 | Brightness; how deep each star's light dips (0–1) | Brightness |
| `glints` | 0 | Share of near stars that flare with a four-point glint | Glints |
| `milky` | false | A diagonal band of faint stars | Milky band (rebuild) |
| `constellations`, `node` | 0, `'dot'` | Hairline figures that wrap with scroll; node shape `'dot'`, `'diamond'` or `'none'` | Constellations (rebuild) |
| `lineAlpha`, `nodeAlpha` | 0.16, 0.55 | Constellation strength | — |
| `interactive` | false | Richer sky around the cursor and on the side you scroll toward; `base` (rest richness 0–1), `sparse` (share shown at rest), `radius` (cursor reach, px) | Interactive sky |
| `tilt` | 0 | Depth tilt: near stars follow the cursor most | Depth tilt |
| `pull` | 0 | `1` stars lean toward the cursor; `-1` they bend around it like a lens | Cursor gravity: off / pull / lens |
| `horizons` | null | Function returning `[{ apex, dir }]` in viewport px; draws black-hole rims at page markers (`'in'`: hole below, `'out'`: hole above) and darkens the interior by `holeDark` | Black hole |
| `crossing` | `'off'` | When a rim crosses mid-screen: `'sweep'` (a band of light runs along it), `'ripple'` (two rings move away), `'both'` | Horizon crossing |
| `chroma` | false | The rim's hot core splits warm above, cool below | Chromatic rim |
| `still` | false | Force the still frame (review switch for "what reduced-motion visitors see") | Still frame |

Methods: `set(next)` changes options without rebuilding; `update(next)` rebuilds the stars (density, milky, constellations, glints, twinkle); `shockwave(x, y)` sends one ring across the sky from a point; tie it to one rare, deliberate moment (the first focus of the main input, a sent form), never to every click or a keyboard action (at most three at once); `focusIn()` fades and settles the sky once on load; `destroy()` removes every listener (use it when a variant picker swaps backgrounds).

A horizons helper for markers in the page:

```js
horizons: () => [...document.querySelectorAll('[data-horizon]')]
  .map((el) => ({ apex: el.getBoundingClientRect().top, dir: el.dataset.horizon }))
```

## Colours

Set these custom properties on the canvas (or a parent) to retint the sky for a direction. Channel tokens are space-separated RGB (`194 65 12`), the rest are any CSS colour.

- Stars: `--star`, `--star-cool`, `--star-warm`; constellations `--constellation` (defaults to `--star-cool`).
- Nebula: `--neb-1`, `--neb-2`, `--neb-3` (keep them faint: alpha .05–.5).
- Black hole, as channels: `--rim-1` (outer glow) … `--rim-5` (hot core), `--rim-sweep`, `--rim-ripple`, `--rim-ripple-core`; embers `--ember-hot`, `--ember` (colours).
- Splits, as channels: `--chroma-warm`, `--chroma-cool`; shockwave rings `--shock-1` … `--shock-4`.

The palette is read once per build; call `update({})` after changing tokens live.

## Effects as switches

Put each option above as one option in the docked Options sheet (pattern: [backgrounds → Live-switch review](../../backgrounds.md#live-switch-review)). A good first set to show, all still off until the owner turns them on: interactive sky, focus in, depth tilt, cursor gravity (lens), and, when the page has a natural "threshold" section, the black hole with a sweep crossing. The design round that produced this recipe kept exactly that set.

Focus-in animates opacity and scale only, never a blur radius ([motion house rules](../../../../implement/references/ui-build/motion.md#stagger-and-press-feedback)).

## Still frame and performance

- Reduced motion, Save-Data or `still: true`: one frame, no drift, twinkle, parallax, pointer, scroll or shockwave effects; with horizons, the frame is redrawn on scroll only so the rims stay attached to their sections. `focusIn()` and `shockwave()` do nothing.
- Hidden tab: no frames. devicePixelRatio is capped at 2.
- One canvas, one `requestAnimationFrame` loop; pointer and scroll only set targets that the frame eases toward.
- Budget and checks: [performance](../../../../implement/references/ui-build/performance.md), [motion fallbacks](../../../../implement/references/ui-build/motion.md#fallbacks). Text over the sky is checked at its brightest frame (nebula, glints, a blazing rim), per [page craft](../../../../implement/references/ui-build/page-craft.md).

## Measuring

```bash
node background/sky-measure.mjs http://localhost:<port>/<mock>.html .sky
```

It prints lit-pixel counts (a 320 px square, bright pixels only):

| Reading | Means | Expect with `interactive` |
|---|---|---|
| `rest near/far` | Right and left of centre, no cursor | about equal |
| `hover near/far` | After the cursor rests on the right point | near clearly above rest near; far unchanged |
| `scroll down top/bottom` | While scrolling down | bottom above top |
| `scroll up top/bottom` | While scrolling up | top above bottom |

Measure with `horizons` off (a rim passing the sample squares swamps the star counts), at the same density and seed each time, and record before and after numbers in the gate log for every tuning change. The tool reads any viewport-sized 2D canvas (it exits with an error on a WebGL canvas); for other 2D types, change what "lit" means only if the readings stop matching what the eye sees.

## At /implement

Port the picked options and colours into the build, drop the review scripts, keep the still-frame behaviour, and re-run the measure once on the built page.
