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

When more than one type fits, build them as variants of one element on the winning mock: `prototype` per the [skill map](../../implement/references/ui-build/motion.md#skill-map). If the skill is installed, use it; otherwise apply the house rules in `motion.md` and say so. One type per variant, the same content in front, shown as one option in the docked sheet ("Background: none / A / B"), switching instant.

## Live-switch review

Effects are chosen in context, not described. They are options in the winner's docked Options sheet: the [live viewer](live-viewer.md)'s sheet, inside the mock, so the owner annotates, switches and approves on one page.

- **One option per effect**, grouped (sky, cursor, scroll, events), each with its label, where it shows on the page, its source, and a recommended value. Every effect starts **off** (the option's `start` value) and "Recommended set" is one control away (a preset with `values: 'rec'`; an "All on" preset lists its values). This is the one exception to the viewer's "recommended pre-selected" rule.
- **Review links** carry the state so the owner can share or reopen a view: the mock reads `?bg=<preset id>` (for example `rec`, `all-on`, `all-off`, each a preset in the config) or `?bg=key:value,key:value`, and the sheet's own links carry each option's value as its own param.
- **Still frame** is a preview state with `reload: true`: it shows what reduced-motion and Save-Data visitors get. Under reduced motion every motion option is inert.
- Open the mock in Lavish per [Lavish review](lavish-review.md); the owner flips options, annotates, and queues the pick. Each pick is written to the README gate log with the date, including what was left off.
- The sheet and its scripts are review chrome, not design: they never ship.

## Tuning by measurement

- Measure what the eye judges. For a canvas, count lit pixels in fixed sample areas (near and far from the cursor, top and bottom of the screen while scrolling); for anything heavy, also frame time.
- Take a reading before and after every tuning change, at the same seed and viewport, and record both in the gate log with the change.
- The galaxy's `sky-measure.mjs` is the worked tool; it reads any viewport-sized 2D canvas. A WebGL or shader background needs its own read-back (or frame-time numbers only).
- When a reading and the owner's eye disagree, the eye wins and the measure is fixed to match it.

## Fallbacks and budget

- Still frame, loop and context-failure rules: [motion fallbacks](../../implement/references/ui-build/motion.md#fallbacks). Budget: [performance](../../implement/references/ui-build/performance.md#runtime--rendering-performance). Text over the background: [page craft contrast](../../implement/references/ui-build/page-craft.md#visual-craft).
- In the review, the still-frame switch is how the owner sees what reduced-motion and Save-Data visitors get.
- When the background moves, the motion skills audit it at `/implement` like any other motion ([skill map](../../implement/references/ui-build/motion.md#skill-map)).

## Hand-off

The gate log lists the type, the options and colours picked, the switches left off, and the last measurements. `/implement` ports those into the build, drops the review scripts (`viewer-config.js`, `options-sheet.js`, `mock-live.js`) and any review-only params, keeps the still frame, and measures once more on the built page.
