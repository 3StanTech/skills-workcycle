# Backgrounds

The optional background step of the mock round: what sits behind the page (a canvas, a shader, a textured backdrop) and how it moves. It runs only when Stage 2 put the background in scope, on the winning mock, after Compare and before G4. Universal motion rules live in the [motion floor](../../implement/references/ui-build/motion.md); this file holds the step. Where each rule came from: [sources](sources.md); rules with no link of their own come from the owner's design rounds listed there.

## Table of contents
- [When to offer](#when-to-offer)
- [Type menu](#type-menu)
- [Comparing types](#comparing-types)
- [Live-switch review](#live-switch-review)
- [Tuning by measurement](#tuning-by-measurement)
- [Fallbacks and budget](#fallbacks-and-budget)
- [Hand-off](#hand-off)

## When to offer

- Ask in Stage 2, beside the imagery question: is the background in scope? A yes is for briefs where the backdrop carries the mood (a night, a material, a signal of craft); a plain colour or the direction's own texture is a no.
- Run the step on the Compare winner. If the owner said no, skip it with one line in the gate log.
- One background per page. It sits behind content, never competes with it, and never carries information a visitor needs.

## Type menu

Offer two or three that fit the direction; "none" is always on the list.

| Type | Fits | Cost | Still frame | Source |
|---|---|---|---|---|
| **Galaxy** (canvas starfield) | Dark directions; night, space, depth, "premium tech" | One 2D canvas; light CPU at default density | Built in | [Galaxy recipe](backgrounds/galaxy/README.md) (worked, coded) |
| **WebGL wallpaper** (a live shader image, e.g. light-thread letters) | A hero or brand moment that should feel alive but abstract | One WebGL 2 context; GPU per frame; cap the frame rate | Freeze at one time value | [pro-threads](https://github.com/kubai087/pro-threads) (MIT): fetch per project from its repo, never copied in |
| **Shader** (gradient, noise, grain field) | Soft colour on light or dark directions | One fragment shader; GPU per frame | Render one frame | No rule source read yet; build from the floor rules only |
| **Dither or ASCII** (an image or video rendered as a dot pattern or glyph ramp) | Editorial, retro, brutalist directions | Per-frame image processing; heavy on video | The processed still image | [Kubai087 tip 003](https://x.com/Kubai087/status/2115091203465290087): luminance mapped to a glyph ramp or an ordered 4×4 Bayer dither, with strength, cell size, spacing and a palette map exposed as switches |
| **Pointer-responsive line art** (lines or a grid that bend toward the cursor) | Quiet, technical directions | One canvas or SVG; light | Lines at rest | No rule source read yet; build from the floor rules only |
| **None** | Most pages | Nothing | — | — |

Third-party code for any type is fetched per project from its own repository with its licence kept, never added to these skills.

## Comparing types

When more than one type fits, build them as variants of one element on the winning mock: `prototype` per the [skill map](../../implement/references/ui-build/motion.md#skill-map). If the skill is installed, use it; otherwise apply the house rules in `motion.md` and say so. One type per variant, the same content in front, switching instant.

## Live-switch review

Effects are chosen in context, not described.

- **One switch per effect**, grouped (sky, cursor, scroll, events), each with its label, where it shows on the page, its source, and a recommended value. Every switch starts **off**; the recommended set is one button away, never the default.
- **Review links** carry the state so the owner can share or reopen a view: `?bg=rec`, `?bg=all-on`, `?bg=all-off`, or `?bg=key:value,key:value`.
- **Still-frame switch**: one switch shows what reduced-motion and Save-Data visitors get. Under reduced motion every motion switch is inert.
- Open the mock in Lavish per [Lavish review](lavish-review.md); the owner flips switches, annotates, and queues the pick. Each pick is written to the README gate log with the date, including the switches left off.
- The switch sheet is review chrome, not design: it never ships.

## Tuning by measurement

- Measure what the eye judges. For a canvas, count lit pixels in fixed sample areas (near and far from the cursor, top and bottom of the screen while scrolling); for anything heavy, also frame time.
- Take a reading before and after every tuning change, at the same seed and viewport, and record both in the gate log with the change.
- The galaxy's `sky-measure.mjs` is the worked tool; it reads any canvas background.
- When a reading and the owner's eye disagree, the eye wins and the measure is fixed to match it.

## Fallbacks and budget

- Reduced motion, Save-Data and `prefers-reduced-data`: one still frame ([motion fallbacks](../../implement/references/ui-build/motion.md#fallbacks)). The page reads the same without the background (no JS, failed WebGL): a flat colour from the direction's tokens.
- One animation loop, paused when the tab is hidden; devicePixelRatio capped at 2; pointer and scroll set targets that the frame eases toward. Budget per [performance](../../implement/references/ui-build/performance.md#runtime--rendering-performance).
- Body text never sits on moving detail without a scrim or a calm zone; check contrast at the background's brightest frame ([page craft](../../implement/references/ui-build/page-craft.md#visual-craft)).
- When the background moves, the motion skills audit it at `/implement` like any other motion ([skill map](../../implement/references/ui-build/motion.md#skill-map)).

## Hand-off

The gate log lists the type, the options and colours picked, the switches left off, and the last measurements. `/implement` ports those into the build, removes the switch sheet, keeps the still frame, and measures once more on the built page.
