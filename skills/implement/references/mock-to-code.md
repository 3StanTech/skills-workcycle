# Mock to code: faithful implementation from an approved mock

Read when the plan builds from an approved mock or image.

Use after approval. For a coded mock, the mock is already most of the build: port it
onto the production stack and fill the gaps. For an image reference, extract first, then
build. Direction rules live in
[web](../../explore-design/references/web.md); verification in
[the shared workflow](../../explore-design/references/medium-and-providers.md).

## 1. Analyze before coding

Treat each approved image or mock as a specification. For every section record:

- **Text:** headline, support, CTA labels, section titles, nav and footer labels, prices.
  If an image's text is too small to read, generate a closer render of that section
  (a fresh render, not an upscaled crop) or ask; never guess copy.
- **Typography:** size and weight relationships, line count, line height and tracking
  feel, serif vs sans, display vs body contrast.
- **Spacing:** headline↔support↔button gaps, card gaps and padding, gutters, section
  top/bottom spacing, overall cadence. Faithful logic, not pixel OCR.
- **Components:** button size, shape, radius, fill vs outline, hierarchy; card
  structure, borders, dividers, shadows; input styling.
- **Color:** backgrounds, panels, accents, button fills, text hierarchy, borders, image
  grade, gradient intensity.
- **Media:** fixed aspect ratios, crop behavior, radius logic, repeatable modules.
- **Layout:** grid, alignment, section order and density, repeated motifs.

## 2. Build faithfully

- Follow the reference closely: layout logic, spacing rhythm, section order,
  text/image balance, type mood, component style. The result should be the same site,
  not one "inspired by" it.
- Do not drift into templates: no generic rows replacing distinctive sections, no
  compressed spacing, no flattened type hierarchy, no reintroduced nested boxes or
  micro-clutter the reference avoided.
- Put tokens (color, type, spacing, radius) in the project's existing system; reuse its
  components and conventions.
- Responsive first view: on a small laptop and a phone the headline, support, CTA and
  focal visual stay visible and uncluttered.
- Preserve semantics, keyboard operation, contrast, and reduced-motion support.

## 3. Resolve missing detail in this order

1. Preserve the visible design language.
2. Preserve layout and spacing logic.
3. Preserve the component family and polish level.
4. Ask, or (for images) render a focused detail view of that section.
5. Only then choose the most buildable faithful version, and report it as a deviation.

## 4. Verify

Render at the agreed viewports next to the reference; compare section by section; list
any deviation and why. A technical fix never triggers a new image set.
