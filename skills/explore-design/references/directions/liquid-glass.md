# Liquid glass: layered translucent material

Direction reference for explore-design Stage 2. A starting point for a named direction, never a requirement to enlarge the brief.

Offer it when the owner asks for glass, an Apple, iOS or visionOS feel, or translucent layered UI over rich imagery. Glass is for the controls and navigation layer (bars, menus, sheets, players, search, cards over media), not for long reading text. Its craft rules live in the floor ([ui-build](../../../implement/references/ui-build.md) Pillars 1–4, [page craft](../../../implement/references/ui-build/page-craft.md) and [motion](../../../implement/references/ui-build/motion.md)); this file holds only the look. Where it is stricter than the floor, the stricter rule applies; it is never looser. When `apple-design` is installed, call it per the [skill map](../../../implement/references/ui-build/motion.md#skill-map); otherwise apply the house rules there and say so. Sources: [register](../sources.md).

## 1. Material

Glass is six layers on one surface, so the scene behind gives it its colour:

1. **Shadow:** a soft volumetric drop shadow under the slab.
2. **Blur and lift:** a light blur of what is behind (about 2px), with saturation and brightness raised so the glass reads clear rather than milky.
3. **Rim refraction:** near the edge the background is pushed inward (strongest at the rim, flat in the middle), with a slight colour split; see §3 for where it renders.
4. **Tint:** a translucent wash whose strength rises with how busy the background is.
5. **Rim light:** a highlight at the top-left and bottom-right edges plus a fainter inset one, giving the slab thickness.
6. **Ink:** text blends with the glass (multiply on light glass, a light overlay on dark glass) so it carries a hint of the scene's colour while keeping contrast.

Starting numbers:

| | Light glass (dark ink) | Dark glass (light ink) |
|---|---|---|
| Tint | white, 6–22% | rgb(20 20 24), 16–38% |
| Blur | 2px | 2px |
| Saturation | 180% | 160% |
| Brightness | 1.06 | 0.8 |
| Rim | 40–44px wide, offset 1.1×, dispersion ±15% | same |

Switch a surface to dark glass when the average brightness sampled under it falls below 0.5, whatever the page theme.

## 2. Tiers

Three thicknesses, chosen by what sits behind the surface, one per surface role:

- **Clear:** only over rich media (a photo, video, artwork), with a dimming layer of about 35% when that content is bright.
- **Regular:** the default for bars, menus and cards, and for anything with text.
- **Thick:** sheets and dialogs that must hold long text or forms, and any menu or popover that can open over another glass surface. Thick glass raises both tint (about 70–80%) and blur (about 12px) so text beneath it no longer shows through; it must never read as glass on glass.

Glass over a flat colour only looks grey: leave those surfaces solid.

**Never nest glass in the DOM.** An element with `backdrop-filter` is a backdrop root, so a glass menu placed inside a glass bar blurs only the bar's own contents and lets the page behind show through sharp. Mount menus, popovers and sheets outside every glass ancestor (a portal or a sibling layer) and position them against their trigger.

## 3. Glass code

Fetch [Glasswork](https://github.com/kubai087/glasswork) per project and follow its `INSTALL.md`: bring `glass.css` into the project's styles beside its colour tokens, add `lens.js` for the rim, and keep its MIT notice when shipping. Never reuse its bundled wallpapers (they are Apple's). Nothing from it is copied into these skills.

Rim refraction support: `lens.js` bends the rim in Chromium browsers only. When the background is an image, a video or a canvas the page draws itself, Glasswork's `refract.js` draws the same refraction in WebGL for Safari, iOS and Firefox (checked on an iPhone in Safari, 2026-11-14). Over ordinary page content those browsers show the glass without the bend, which reads almost the same, so treat the bend as a bonus and never as something the design depends on.

Everything else (blur, tint, rim light, ink) renders in every current browser.

## 4. Corners

- **Concentric:** nested radii follow page craft's [nested-radius rule](../../../implement/references/ui-build/page-craft.md#visual-craft); on top of it, boxes on the same level share one radius, never below 4px, pills and circles stay round, and radii and padding sit on a 4px grid.
- **Continuous corners** as a progressive enhancement: `@supports (corner-shape: superellipse(1.25)) { .glass { corner-shape: superellipse(1.25); } }`, with `corner-shape: round` on pills and circles.
- **Safari and iOS:** give every surface that has `backdrop-filter` `corner-shape: round` there; iOS 27 leaves an element with both a backdrop filter and a superellipse corner undrawn on real devices (the simulator hides the bug).

## 5. Solid surfaces beside the glass

Opaque cards that sit next to glass (bento grids, panels on a plain section) take the same light model: a faint inner glow along the top edge (a highlight, not elevation) and one elevation treatment, as page craft requires: either two or three stacked soft shadows, or a 1px stroke with no shadow. Hover keeps that treatment: stacked shadows spread and drop lower as the card lifts; a stroked card deepens its stroke slightly while the face brightens.

## 6. Scroll edge fade

Under a fixed glass bar, content fades to the page background as it scrolls beneath, so the bar's labels stay legible over the brightest content.

## 7. Contrast

Stricter than the floor: check glass text against the brightest content that can sit or scroll beneath it, not the average. Dim secondary labels on dark glass need at least about 46% white to pass AA on black. Page craft's solid fallback under `prefers-reduced-transparency` applies to every glass surface.

## 8. Motion

Glass surfaces move on springs: menus and sheets grow out of the control that opened them (continuity), presses squash slightly. Easing, continuity and fallbacks follow [motion](../../../implement/references/ui-build/motion.md).

## Overrides of web.md

- §8 "stacked glassmorphism": allows one glass layer per surface stack (a bar, a menu, a sheet, a card) over content; never glass on glass, and never glass over a flat colour.
