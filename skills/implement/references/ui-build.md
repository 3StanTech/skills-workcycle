# UI build quality

Read when the plan touches a UI. explore-design also builds its coded mocks on this floor (Pillars 1–4).

Apply responsive, usable, and fast defaults while writing UI code — quality gates baked into the build, not bolted on after.

**Decision points:** If an interactive question tool (e.g. `AskUserQuestion`) is available, use it with 2–4 prefilled options, recommended option first and labeled "(Recommended)". Otherwise, print the same options as a numbered list in chat, state the recommended number, and wait for a reply. Never proceed past a decision point on an assumption.

## Workflow

### 1. Establish the context

Before writing code, settle three things (from the conversation, or by a quick assumption you state out loud):

- **Devices & viewport range.** Assume mobile *and* desktop matter unless told otherwise. A dashboard for internal desktop users and a marketing page for phones have different centers of gravity — but both must not *break* at other sizes.
- **The primary user action.** What is the one thing a user most needs to do here? That action gets the best ergonomics, the fastest path, and the most care in every decision below.
- **The performance budget, roughly.** A static landing page should be nearly instant; a data-heavy app earns more weight. Know which one you're building so you notice when you're blowing the budget.

If device range or primary action is genuinely ambiguous, ask a decision-point question rather than guessing.

### 2. Build with the defaults below

The four pillar sections in this file are the working defaults — apply them automatically as you write. The `ui-build/` files hold the exhaustive versions; load them when the build is substantial or when you hit a domain that needs the full checklist:

- `ui-build/responsive.md` — layout systems, breakpoints, images, typography, touch ergonomics. Read when building multi-viewport layouts, complex grids, or mobile navigation.
- `ui-build/usability.md` — feedback, forms, navigation, accessibility, content. Read when building forms, multi-step flows, or anything with non-trivial interaction states.
- `ui-build/performance.md` — assets, JavaScript, rendering, Core Web Vitals, measurement. Read when payload, load time, or runtime jank is in scope.
- `ui-build/page-craft.md` — page composition, visual craft, motion safety, content honesty, theme, launch checklist. Read for any page or mock (landing, marketing, portfolio, app shell).

### 3. Audit before delivering

Never hand over a build you haven't actually resized and abused. Minimum pass, every time:

1. **Resize sweep.** Walk the layout at ~375px, ~768px, and ~1280px+. Look for horizontal scroll, overlapping elements, squashed images, unreadable text, and touch targets that shrank below usable.
2. **Interaction sweep.** Click/tap everything interactive. Does each control respond visibly? Do async actions show pending states? Can you complete the primary action with keyboard only?
3. **Abuse sweep.** Long text in every text slot, empty data, a failed request, a double-click on submit.
4. **Weight sweep.** Anything obviously heavy — uncompressed images, an imported library used for one function, render-blocking work before first paint?

5. **Visual bug fixes.** Measure before theorising (computed styles, every matched CSS rule, `scrollHeight` vs `clientHeight`), then apply the fix in the browser first (inject the CSS or DOM change) and screenshot before committing. A fix that was not reproduced in the browser is not done.

Fix what you find. If a fix is genuinely out of scope, say so explicitly in the handoff rather than leaving it as a silent landmine.

### 4. Report (when the task is a review, not a build)

If asked to audit or improve an existing build, run the four pillars as an inspection in this order: **usability breakage first** (things that stop or confuse users), **responsive breakage second** (things broken at real viewports), **performance third** (things that are slow), **page craft fourth** (composition, honesty and launch gaps). Report findings by severity with concrete fixes — file/line or selector-level specificity, not "consider improving performance." Quick wins (a missing viewport tag, an unoptimized hero image, a missing pending state) go at the top.

If you write a report file, and the working directory is a git repository, write outputs to the project folder outside the git tree, or to the session scratchpad — never commit process artifacts.

---

## Pillar 1: Responsiveness

**Mobile-first, fluid by default.** Write base styles for the small screen and enhance upward with `min-width` media queries. It's far easier to add columns as space appears than to cram a desktop layout down.

Working defaults:

- **Layout with flex and grid, not fixed widths.** Use `max-width` + `width: 100%` for containers, `minmax()` and `auto-fit`/`auto-fill` for grids, and let content wrap.
- **The 320–375px floor.** Everything must survive a 320px viewport without horizontal scroll. Watch fixed-width tables, long unbroken strings (`overflow-wrap: break-word`), side-by-side pairs that should stack, and absolute positioning.
- **Breakpoints from content, not devices.** Add a breakpoint where the layout starts to look wrong, not at a memorized "tablet" number.
- **Fluid type and spacing.** Use `rem` for type, `clamp()` for headings that should scale, and consistent spacing tokens. Never let body text drop below ~16px on mobile.
- **Touch ergonomics.** Interactive targets ≥44px, adequate spacing between adjacent targets, no hover-only reveals (pair hover with focus/tap), thumb-reachable primary actions on mobile.
- **Responsive media.** `max-width: 100%; height: auto` on images as a floor; `aspect-ratio` to reserve space; `srcset`/`sizes` when serving real photos.
- **Viewport meta** in raw HTML builds: `<meta name="viewport" content="width=device-width, initial-scale=1">`.

Full treatment: `ui-build/responsive.md`.

## Pillar 2: Usability

**Every action gets a reaction.** The single most common usability failure in generated builds is silence: a button that does something with no visible acknowledgment, a form that submits into the void, an error swallowed by the console.

Working defaults:

- **Visible interaction states** on everything clickable: hover, focus-visible, active, and disabled. Cursor changes. A pressed button should *look* pressed.
- **Async feedback trio**: pending (spinner/disabled button with "Saving…"), success (confirmation the user can't miss), failure (plain-language error *with a path forward* — retry, edit, contact). Disable the submit control while in flight to kill double-submits.
- **Forms that help.** Labels on every field (placeholders are not labels), correct input types, validation inline and near the field, errors that say how to fix it, fewest required fields possible.
- **Never rely on color alone** to convey state — pair it with an icon, text, or weight change.
- **Accessibility as a floor**: semantic elements (`button` for actions, `a` for navigation, real headings in order), alt text on meaningful images, keyboard operability, visible focus indicator, contrast that passes WCAG AA (~4.5:1 for body text), `prefers-reduced-motion` respected on any nontrivial animation.
- **Obvious empty and error states.** Empty states get a message and a call to action.
- **The primary action is unmissable** — one visually dominant action per screen/section; secondary actions visibly subordinate.

Full treatment: `ui-build/usability.md`.

## Pillar 3: Optimisation

**Performance is a feature users feel.** The biggest wins are almost always boring: smaller images, less JavaScript, and not blocking the first paint. Chase those before anything clever.

Working defaults:

- **Images are the #1 payload.** Right-size them, use modern formats (WebP/AVIF) where possible, `loading="lazy"` on everything below the fold, explicit `width`/`height` or `aspect-ratio` to avoid CLS.
- **Ship less JavaScript.** Don't import a library for something a few lines of vanilla code does. When a library earns its place, import the piece you need.
- **Don't block first paint.** Scripts get `defer` (or live at the end of `body`), critical content renders without waiting on JS, fonts use `font-display: swap`.
- **Respect the render loop.** Debounce input-driven work, animate `transform`/`opacity` instead of layout properties, batch DOM reads/writes.
- **Long lists get help.** Past a few hundred rows, paginate, lazy-render, or virtualize.
- **React specifics** (when applicable): key lists properly, keep state local, derive rather than duplicate state, memoize only measured hot spots.
- **Know the vitals** as targets: LCP under ~2.5s, CLS under 0.1, INP under 200ms.

Full treatment: `ui-build/performance.md`.

## Pillar 4: Page craft

**Taste-neutral, every direction.** A visual direction changes how a page looks, never whether these hold.

Working defaults:

- **The first viewport sells**: headline, support line and primary action visible on a small laptop and a phone; one label per action intent; navigation on one line.
- **One shape system**: one radius scale; nested radius = outer − gap; elevation from a border or a shadow, not both.
- **Contrast everywhere it hides**: button labels on fills, ghost buttons over photos, form placeholders and helper text; themed selection, caret, scrollbars and focus rings.
- **Motion safety**: `transform`/`opacity` by default, no per-frame scroll work, reduced motion honoured, content visible without scroll or JS.
- **Honest content**: nothing invented shown as real; placeholders tagged "Confirm with <owner>"; every visible string re-read.
- **One theme per page**, and a launch checklist (title, meta, social tags, favicon, alt text, skip link, 404, legal links) before anything goes live.

Full treatment: `ui-build/page-craft.md`.

### Redesigns

When a build changes an existing site, these never change silently (only with the owner's approval):

- URL structure and route slugs, anchor IDs, primary navigation labels.
- Form field names and order, and the button, form and section IDs analytics depend on.
- The logo or wordmark, and legal, consent and cookie copy.
- Existing accessibility wins: focus states, alt text, keyboard operation and contrast never regress.

Record the SEO baseline (ranking pages, titles, structured data, social cards) before touching anything; SEO migration is the biggest redesign risk.

## Right-sizing

A tiny artifact (a single chart, a one-card widget) doesn't need a formal four-sweep audit narrated at the user — silently apply the defaults and move on. A full landing page, dashboard, or multi-view app deserves the explicit audit pass; tell the user what you checked in one or two sentences. This reference makes builds better, not ceremonies longer.

## Guardrails

- Do not invent aesthetic direction, brand systems, or decorative redesigns — defer those to installed design skills.
- Do not expand into a full screen-by-screen visual polish pass unless asked — then follow Polish guardrails below.
- Do not skip the abuse and resize sweeps on multi-viewport UI work of real size.
- Do not leave known breakage silent; if out of scope, state it in the handoff.
- Do not quietly omit coverage limits (no browser, no runtime) — name them in the report.

## Polish guardrails

For a final look-and-feel pass on a UI that already works. Make it look intentional with the smallest diffs; never redesign it or degrade performance or responsiveness.

**Fixed budget (never break):**

- No new runtime dependencies, UI/animation libraries, icon packs, or CSS frameworks for a visual fix.
- No new blocking resources: no extra CDN font families, large images, or external stylesheets. A new font needs `font-display: swap`, subsetting, and the owner's sign-off.
- CSS over JS; no scroll/resize listeners or layout-reading JS for cosmetic effects. Animate only `transform` and `opacity` in a polish pass (stricter than the build floor in `ui-build/page-craft.md`, on purpose: a polish pass adds no new effect types); respect `prefers-reduced-motion`.
- Keep fluid units and existing breakpoints. Re-check every change at ~360px, ~768px, and ~1280px: no horizontal scroll, touch targets ≥44×44px.
- No layout thrash: images keep dimensions or aspect-ratio; placeholders keep the loaded footprint.
- Don't break behavior: never rename classes/IDs that JS or tests hook into, change DOM that handlers depend on, or alter form semantics. Flag any markup restructure and its risk first.
- Accessibility floor: visible focus, contrast ≥4.5:1 body / ≥3:1 large text, headings in order.

If an improvement would break the budget, propose the constrained version or skip it and say why.

**Smallest diffs, no new direction:** change values and classes, not structure. Follow an existing brand or design system exactly; on subjective calls, match what most of the UI already does. Consolidate tokens only in touched files. Remove noise rather than add decoration.

**Screen-by-screen inventory (when asked for a polish pass):** read the stack, styling approach and tokens actually in use; walk each target screen through hierarchy, spacing, typography, color, consistency, states, responsiveness and copy; report concrete findings with file/line and High / Medium / Low impact before changing anything, unless told "just fix it". Default scope: fix High and Medium, list Low.

**Critique with a point of view, redesign or new direction:** use impeccable, or `~/.agents/skills/explore-design/` for new direction and mocks, then return here for the final pass.
