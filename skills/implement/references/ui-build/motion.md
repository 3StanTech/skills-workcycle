# Motion — skill map and house rules

Which motion skill runs at which moment, and the house rules that apply whenever that skill is not installed. Safety rules (transform and opacity, no per-frame scroll work, reduced motion, motivated motion, one engine per tree) live in [page-craft → Motion safety](page-craft.md#motion-safety) and are not repeated here. Where every rule came from: [sources](../../../explore-design/references/sources.md).

## Table of contents
- [Skill map](#skill-map)
- [Easing by role](#easing-by-role)
- [Continuity](#continuity)
- [Exits and closing the gap](#exits-and-closing-the-gap)
- [Stagger and press feedback](#stagger-and-press-feedback)
- [Micro-transition shortlist](#micro-transition-shortlist)
- [Fallbacks](#fallbacks)

## Skill map

The motion skills are Emil Kowalski's (`emilkowalski/skills`, installed separately). Three of them cannot be invoked as skills; read their `SKILL.md` by path and follow it.

| Moment | Skill | How to call |
|---|---|---|
| explore-design: comparing variants of one element (a header, a background, a motion pass) | `prototype` | read `~/.agents/skills/prototype/SKILL.md` and follow it, inside explore-design's limits: build the variants in the mocks folder (outside product repos), carry the pick into the winning mock only, show the variants as one option in the live viewer's sheet (`explore-design/references/live-viewer.md`), keep the variant files in the mocks folder as resumable evidence (prototype's keep-on-request case; skip its delete-the-surface step), and leave production integration to `/implement` |
| explore-design G4: motion pass on the winning mock | `find-animation-opportunities` | invoke; show its shortlist as options in the mock's docked Options sheet (`explore-design/references/live-viewer.md`) |
| implement: adding one animation | `animate` | invoke |
| implement: several elements moving together | `choreograph` | invoke |
| implement: drag, swipe or sheet | `gestures` | invoke |
| any stage: the direction is liquid glass or an Apple feel | `apple-design` | invoke |
| implement audit ([ui-build.md](../ui-build.md) §3) and work-audit, when the change touches motion | `animation-performance`, then `review-animations` | invoke the first; read `~/.agents/skills/review-animations/SKILL.md` and follow it |
| review of an existing UI's motion ([ui-build.md](../ui-build.md) §4) | `remove-animations` → `improve-animations` → `animation-performance` | invoke in that order; in a report-only review, record `remove-animations`' cuts as findings and apply none unless the task is a build or the owner approves the edits |
| explore-design G4 close and `/end`, when the session held design corrections | `learn-taste` | read `~/.agents/skills/learn-taste/SKILL.md` and follow it; it proposes, the owner approves each rule |

- **Fallback, said once and used everywhere:** if the skill is installed, use it; otherwise apply the house rules below and say so.
- **learn-taste target:** approved rules go to the project's `DESIGN.md` by default. A correction that is not project-specific is proposed instead as an edit to this floor or to a direction, and written only with the owner's approval.
- **impeccable boundary:** building motion and reviewing motion go to the skills above; impeccable stays the general critique and polish step.
- This map is about which skill runs, and has nothing to do with model tiers.

## Easing by role

Pick the curve by what the motion does, not one ease-out everywhere.

| Role | Curve | Example |
|---|---|---|
| Something running (progress, loader) | linear | progress bar |
| Overlay entrance | ease-out | menu, toast, popover, drawer |
| Tiny element snapping in after a click | strong ease-out | selected pill, icon swap |
| Exit | ease-out by default; ease-in only for short exits (≤150 ms) where the element leaves the screen | dialog close, toast dismiss |
| Swap in place | ease-in-out | tab indicator, carousel page |
| Small playful confirmation | overshoot (~10%) | checkmark, like; never a large panel |
| Snap back after release | spring | drawer rebound, reorder drop |

Our tokens (copy into the project's motion tokens):

```css
:root {
  --ease-out: cubic-bezier(.22, 1, .36, 1);
  --ease-out-strong: cubic-bezier(.16, 1, .3, 1);
  --ease-in: cubic-bezier(.55, 0, 1, .45);
  --ease-in-out: cubic-bezier(.65, 0, .35, 1);
  --overshoot: cubic-bezier(.34, 1.56, .64, 1);
  /* a light spring: one small overshoot, settles in ~0.5 s */
  --spring: linear(0, .35 8%, .78 18%, 1.02 30%, 1.05 38%, 1.01 52%, .995 70%, 1);
}
```

Durations grow with distance and size: about 150–250 ms for small elements and presses, 250–400 ms for menus and popovers, 400–600 ms for large surfaces and page-level moves. Exits run faster than the matching entrance.

## Continuity

When the interface changes state, the element the user touched carries into the next state instead of vanishing and being replaced, so the user always sees where they came from. Morph or move; a cross-fade alone is not continuity. Elements that are not part of the change stay still.

The seven common cases:

1. **Navigation:** the tapped row's title becomes the page title, and the old title shrinks into the back button; on scroll the title tucks into the top bar.
2. **Card to detail:** the card grows into the page and its image becomes the header; dismissing runs the same path back.
3. **Mini player to full player:** cover, title and controls each travel to their place.
4. **Search:** the box moves to the top, matching results move up as the user types, the rest fade out.
5. **Chart card to chart:** the card's small bars become the chart's bars.
6. **Menu from its button:** the menu grows out of the control that opened it; a new item drops into place and the rest shift in sequence.
7. **Tab bar:** the selected pill stretches toward the new tab first, then settles.

## Exits and closing the gap

- The exit is a picture of leaving; it never blocks input or delays a change that is already authorized. When a change counts as authorized (confirmation, server acknowledgement, rollback) stays with [usability](usability.md#destructive--irreversible-actions); the animation never adds a wait of its own.
- Capture what is leaving (its rectangle and appearance) before the state changes, then hide the real element; virtualised lists drop it on the next update.
- Draw the effect on one layer above the list that ignores pointer input; the first frame must match the real element exactly.
- Close the gap with a transform spring, never by animating height or margin, and start it before the exit effect finishes so the list never waits.
- Cap concurrent heavy exits (about three) and fall back to a plain fade beyond that; undo stops the effect at once and brings the item back the product's usual way.

## Stagger and press feedback

- **Decay with distance:** in a group reaction (neighbours making room, pages fanning, items cascading), each step away from the source moves less and starts later: amount × 0.7ⁿ, delay ≈ 24–28 ms × n. Close or settle in reverse order.
- **Transforms only:** neighbours lean with `transform`; the gap opens and closes without layout animation.
- **Never animate a blur radius or a box-shadow ring:** pre-blur two shadow states and cross-fade their opacity.
- **Hit-test on the resting footprint:** hover listeners sit on a static outer element and moving layers take `pointer-events: none`, so a moving card never flickers at its edge.
- **Press feedback:** about 1px down with `transform`, while a pre-rendered pressed layer (lighting flipped, outer shadow collapsed) cross-fades in over the rest layer; ~120 ms for the transform, ~140 ms for the cross-fade, ~160 ms for colour. Micro presses: hover scale ≈1.02, press ≈0.97.

## Micro-transition shortlist

Reach for these by behaviour, each rebuilt in the project's own CSS or JS on the tokens above (amicro was studied for them; nothing is copied):

- **Controls:** a glare that crosses a primary button on hover; icon morph (copy → check, play ↔ pause); label that rolls up to a copy; a magnetic pull of a few px toward the cursor.
- **Cards and lists:** a cursor spotlight on glass or cards; focus-blur on a list so the hovered row stays sharp; a small fan or spread on hover.
- **Text:** blur-up word reveal; a one-time colour sweep across a headline; count-up for a real number; a short decode on mono labels.
- **Headline:** a slight tilt toward the cursor (about ±2°), spring-damped.

Use at most a few per page, each with a one-sentence reason (page-craft: motion is motivated).

## Fallbacks

- **Reduced motion:** follow page-craft; where a movement carries meaning (an item moved, a panel opened), replace it with a short opacity cross-fade so the state change stays visible. Drag-to-reorder keeps only its insertion line.
- **Save-Data and low power:** when `navigator.connection?.saveData` is true or `prefers-reduced-data: reduce` matches, decorative loops and canvases render one still frame.
- **Decorative canvases and shaders:** one animation loop, paused while the tab is hidden; devicePixelRatio capped at 2; pointer and scroll only set targets that the frame eases toward. Without JS or when the context fails (no WebGL), the page shows a flat colour from the direction's tokens and reads the same.
- **No outside skills installed:** everything above still applies; say that the house rules were used instead of the skill.
