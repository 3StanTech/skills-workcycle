# Clean geist: crisp single-typeface conversion UI

Direction reference for explore-design Stage 2. A starting point for a named direction, never a requirement to enlarge the brief.

Adapted from the visual system (Part B) of Elaya's landing-page-design (MIT; see `../../NOTICE`). Its craft rules live in the floor ([ui-build](../../../implement/references/ui-build.md) Pillars 1–4 and [page craft](../../../implement/references/ui-build/page-craft.md)); this file holds only the look. Where it is stricter than the floor, the stricter rule applies; it is never looser.

## 1. Typeface

- **Use:** Geist, Manrope or Poppins as the one typeface; Geist Mono only where a monospace is functionally needed (code, data, tabular numbers).
- **Never:** Inter, Roboto, Arial, Open Sans, Helvetica.
- **One typeface per site.** No display + text pairing unless the owner asks. At the type gate, offer this direction single-face candidates, not pairings.
- **No italics** anywhere in the interface.
- **No ultra-bold:** cap at semibold or bold, never 900 / black.

## 2. Copy style

- **No hyphens in copy:** headings, body and labels avoid `-`; rewrite the phrase ("in house", "two week"), and write ranges with "to" ("2018 to 2026"). Stricter than the floor's range rule.
- **Sentence case** for headings and buttons.
- Wrapping and line breaks follow the floor (`text-wrap: balance` on headings, `pretty` on body); no `<br>` splits.

## 3. Type scale

Every font size resolves to a Tailwind default step, with that step's line height. An off-scale size snaps to the closest step **below**; tracking and line height are tuned only within the step.

| Class | Size | Line height |
|---|---|---|
| `text-xs` | 12px | 16px |
| `text-sm` | 14px | 20px |
| `text-base` | 16px | 24px |
| `text-lg` | 18px | 28px |
| `text-xl` | 20px | 28px |
| `text-2xl` | 24px | 32px |
| `text-3xl` | 30px | 36px |
| `text-4xl` | 36px | 40px |
| `text-5xl` | 48px | 1 |
| `text-6xl` | 60px | 1 |
| `text-7xl` | 72px | 1 |
| `text-8xl` | 96px | 1 |
| `text-9xl` | 128px | 1 |

Buttons: main `text-base` semibold; small header buttons `text-sm` semibold.

## 4. Spacing

Only these values: 0, 2, 4, 8, 12, 16, 24, 32, 40, 48, 64, 80, 96px. Main buttons: 8px vertical, 12px horizontal padding.

## 5. Corner radius

Tailwind radius values only. Nested shapes follow the floor's nested-radius rule.

## 6. Borders and backgrounds

- A card border goes all the way round or not at all; never one side only.
- Backgrounds are flat: no background gradients.
- Dark theme surfaces only from: `#181818`, `#1F1F1F`, `#272727`, `#313131`, `#131209`.

## 7. Hero

- **Heading colour:** a left-to-right gradient on the heading text only: dark theme `#FAFAFA` → `#9B9B9B`, light theme `#111111` → `#666666` (no pure `#000`/`#fff`, per the floor). The one place a gradient appears; contrast of the lightest end stays within the floor's text-contrast rule at the heading's size.
- Heading and subheading both capped at a **680px** max width, so lines break where the thought breaks.

## 8. Icons

Phosphor, Solar or Iconamoon. Never Material Icons or Material Symbols.

## 9. Motion

- **Base curve:** `cubic-bezier(0.22, 1, 0.36, 1)`, 500ms for layout and position changes; opacity hovers 300ms, never under 200ms; a colour change on hover is instant or expressed through opacity. No browser default curves (`ease`, `linear`, `ease-in-out`).
- Animate **only** `transform` and `opacity` (stricter than the floor).
- **Navigation:** a compact bar floating off the top edge, centred and sized to its content, on a translucent surface with background blur. The menu icon morphs between open and closed on the base curve. On phones the menu opens as a full-height panel (base surface at high opacity, strong blur); its links enter one after another in reading order, each rising 24px while fading in, 60ms apart, the whole sequence capped at 400ms.
- **Scroll reveals:** a section entering the viewport rises 32px and fades in over 600–800ms on the base curve, once only, triggered by `IntersectionObserver` or a motion library's in-view primitive.
- Reduced motion follows the floor: reveals and entrances are off; other state changes may use a plain opacity change.

## 10. Tagline reveal section (mandatory in this direction)

One large-type section stating the core benefit or tagline, separate from the hero and further down the page, as its own moment.

- **Copy:** at least two lines; a benefit statement from the page plan (`content.md`), not a generic heading.
- **Type:** `text-4xl` to `text-6xl` by line count, capped at the hero's max width.
- **Animation:** words start in a muted tone (about 45% of the base text colour's opacity, never below the floor's 3:1 large-text contrast on the surface) and, as the section scrolls into view, each word turns full colour in reading order as it crosses a trigger line, on the base curve. Use `IntersectionObserver` per word or one `requestAnimationFrame`-throttled scroll handler. Under reduced motion the text shows at full colour.

## Overrides of web.md

- §6 "gradient text": allows the hero heading's two-stop greyscale gradient (§7 above), on the heading text only, never on backgrounds or other text.
