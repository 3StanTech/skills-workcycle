# Responsiveness — full reference

The deep version of Pillar 1. Skim what's relevant; skip what isn't.

## Table of contents
- [Layout systems](#layout-systems)
- [Breakpoint strategy](#breakpoint-strategy)
- [Typography & spacing](#typography--spacing)
- [Images & media](#images--media)
- [Touch & input ergonomics](#touch--input-ergonomics)
- [Hard cases](#hard-cases)
- [Testing matrix](#testing-matrix)

## Layout systems

- **Grid for two-dimensional layout, flex for one-dimensional.** Page and
  card-grid structure → CSS grid; toolbars, nav rows, form rows → flex.
- **The self-adjusting grid**:
  `grid-template-columns: repeat(auto-fit, minmax(min(250px, 100%), 1fr))` —
  columns appear and disappear with available space, no media queries needed.
  The inner `min()` prevents overflow below 250px.
- **Containers**: `max-width` + `margin-inline: auto` + side padding. Fixed
  `width` on a container is almost always a bug.
- **Prefer intrinsic sizing** (`min-content`, `max-content`, `fit-content`,
  wrapping) over pixel measurements. The layout should be *derived from
  content*, so unexpected content can't break it.
- **Avoid absolute positioning for layout.** Reserve it for overlays, badges,
  and decorations anchored to a relative parent. Absolutely-positioned layout
  is the #1 source of overlap at untested sizes.
- **Container queries** (`@container`) when a component must adapt to its
  *slot* rather than the viewport — e.g. the same card in a sidebar and a main
  column. Support is broadly good; use them when component reuse demands it.

## Breakpoint strategy

- Base styles = smallest screen. Enhance with `@media (min-width: …)`.
- Add breakpoints **where the content breaks**, not at device folklore. Resize
  until it looks wrong; that's your breakpoint.
- Common working set (adjust to content): ~640px (stack → pairs), ~1024px
  (bring in sidebars / multi-column), ~1280px (cap line lengths, widen gutters).
- Keep breakpoints few and consistent across the build. Six bespoke
  breakpoints per component is unmaintainable.
- Don't forget **the range above your largest breakpoint** — ultrawide
  monitors. Cap content width; don't let text lines run 300 characters.

## Typography & spacing

- `rem` for font sizes (respects user's browser settings); `em` or unitless
  for line-height.
- Body text: 16px minimum on mobile. Inputs specifically ≥16px, or iOS Safari
  zooms the page on focus.
- Fluid headings: `clamp(min, preferred-vw, max)` — e.g.
  `clamp(1.75rem, 5vw, 3rem)`. Body text usually shouldn't be fluid; it should
  just be readable.
- Line length: ~45–75 characters. `max-width: 65ch` on prose containers is a
  one-line fix for readability on wide screens.
- Line height: ~1.5 for body, tighter (~1.1–1.2) for large headings.
- Spacing scale: pick a token scale (4/8px steps or a rem scale) and stick to
  it. Ad-hoc spacing values are how layouts drift out of alignment.
- `overflow-wrap: break-word` on user-generated text slots; `text-overflow:
  ellipsis` + `white-space: nowrap` + `overflow: hidden` where single-line
  truncation is the design.

## Images & media

- Floor for all images: `max-width: 100%; height: auto; display: block`.
- Reserve space: explicit `width`/`height` attributes or CSS `aspect-ratio`,
  so nothing shifts when the image loads.
- Real photography → `srcset` + `sizes` so phones don't download desktop
  images. Icons and simple graphics → inline SVG (crisp at every size,
  styleable, no request).
- `object-fit: cover` for images filling a fixed frame (cards, avatars,
  heroes); `contain` when cropping is unacceptable (logos, diagrams).
- Background images used as content are an accessibility and responsiveness
  liability — prefer `<img>` with alt text.
- Video: constrain with `aspect-ratio: 16/9` wrappers; never autoplay with
  sound; provide `poster`.

## Touch & input ergonomics

- Targets ≥ 44×44px (Apple) / 48×48dp (Android). Padding counts — grow the
  hit area, not necessarily the visual.
- ≥ 8px gap between adjacent targets; misclicks on cramped controls are a top
  mobile frustration.
- No hover-dependent functionality. Anything revealed on hover must also be
  reachable by tap and by keyboard focus.
- Primary actions in thumb range on mobile (bottom of viewport beats top for
  one-handed use); destructive actions *out* of casual thumb range.
- Sticky/fixed bars: account for on-screen keyboards and browser chrome;
  `100dvh` (dynamic viewport height) instead of `100vh` to avoid the
  mobile-browser toolbar overlap bug.
- Disable double-tap-zoom surprises: correctly-sized text and the viewport
  meta tag solve most of it; don't reach for `user-scalable=no` (it's an
  accessibility failure).

## Hard cases

- **Tables.** Under ~600px, real tables need a strategy: horizontal scroll in
  a wrapper (`overflow-x: auto` — fine for data-dense admin views), collapse
  to stacked cards (better for browsing), or hide secondary columns. Choose
  deliberately; default table rendering on mobile is unusable.
- **Navigation.** 5+ items rarely fit on mobile. Options: collapse to a menu
  button, bottom tab bar (apps), or priority+overflow ("More"). Whatever the
  pattern, it must be operable by keyboard and screen reader (real buttons,
  `aria-expanded`).
- **Modals & overlays.** Full-screen on small viewports, centered card on
  large. Always scrollable internally; never taller than the viewport with no
  scroll. Close affordance reachable without scrolling.
- **Multi-column forms.** Collapse to single column on mobile; two-column
  forms with tab-order weirdness are a classic desktop-first bug.
- **Charts & visualizations.** Either redraw responsively (preferred), allow
  horizontal pan, or swap in a simplified mobile variant. A desktop chart
  scaled to 350px wide is decoration, not information.
- **Fixed sidebars.** Off-canvas drawer on mobile; visible panel from your
  wide breakpoint up.

## Testing matrix

Minimum honest pass: **~375px** (modern phone), **~768px** (tablet /
half-window), **~1280px+** (laptop). Plus: 320px survival check (no horizontal
scroll), and if the audience skews mobile, test the layout with the on-screen
keyboard open on any screen with inputs.

What to look for at each size: horizontal scrollbars, overlap, images
distorting, text below 16px, touch targets collapsing, hidden or truncated
primary actions, orphaned hover-only functionality.
