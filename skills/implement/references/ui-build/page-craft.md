# Page craft — full reference

The deep version of Pillar 4. Read when building any page: explore-design sample mocks,
landing pages, and implement builds. These rules hold in every visual direction. A
direction changes how a rule looks, never whether it applies; only the brief or the
brand can waive one, and only explicitly.

## Table of contents
- [Page composition](#page-composition)
- [Visual craft](#visual-craft)
- [Motion safety](#motion-safety)
- [Content honesty](#content-honesty)
- [Theme and dark mode](#theme-and-dark-mode)
- [Launch checklist](#launch-checklist)
- [Sources](#sources)

## Page composition

- **The first viewport sells.** On a small laptop and a phone the headline, the support
  line and the primary action are visible without scrolling. Plan the headline size and
  the hero visual together: a headline over two lines at desktop is a size error, support
  copy stays near 20 words, and the hero holds at most four text elements (one small label
  or brand strip, headline, support, actions). Trust strips, pricing teasers and feature
  bullets go in the section below.
- **Hero spacing is deliberate.** Top padding stays modest (about 6rem at desktop at most);
  more room comes from type or visual scale, not empty space above the content.
- **Navigation fits one line at desktop** and stays about 64–80px tall. When items don't
  fit, shorten labels, drop secondary items, or collapse to a menu.
- **No dead links.** A control pointing at `#` is either linked or visibly disabled. The
  current page is marked in the navigation.
- **One label per intent.** Every action with the same intent uses the same words across
  the page ("Book a table" everywhere, not also "Reserve" and "Get in touch").
- **Action labels fit one line at desktop.** Shorten the label or widen the button; never
  constrain a CTA's width until it wraps.
- **Grids hold exactly their content.** N items get N cells; no empty or filler tiles.
- **Vary the layout.** A layout family (three image cards, split text/image, full-width
  quote) appears once per page; no more than two image/text zigzag sections in a row.
- **Small labels are rationed.** At most one small uppercase label above a heading per three
  sections (the hero counts). The heading usually carries the section alone.
- **No data dumps on marketing pages.** Show the top 3–5 items and link to the full list;
  long lists get a grouped or card layout, not 20 ruled rows.

## Visual craft

- **One shape system.** Pick one corner-radius scale for the page (or write down a mixed
  rule, such as pill buttons with 16px cards) and follow it everywhere.
- **Nested radius.** When a rounded shape sits inside another with less than 32px between
  them, inner radius = outer radius − gap. Apply it only when the result is over 2px.
- **Elevation is declared once.** A surface uses a border or a shadow, not both. Shadows
  are tinted toward the background hue; no pure-black drop shadows on light surfaces.
- **Contrast is checked, not assumed.** Body text ≥ 4.5:1, large text ≥ 3:1, including
  button labels on their fill, ghost buttons over photos (add a scrim or stroke), and form
  inputs, placeholders, focus rings, helper and error text against their section. On a
  coloured surface, tint secondary text from that hue instead of grey.
- **Theme the browser surfaces.** Text selection, the caret, scrollbars, focus rings,
  link underline offset and tabular numerals in data all take the palette; browser
  defaults belong to no design.
- **Text wraps well.** Headings use `text-wrap: balance`, body copy `text-wrap: pretty`, so
  no single word sits alone on a last line.
- **Layers are systemic.** `z-index` only for real layers (sticky header, overlay, modal,
  grain), from one documented scale.
- **Real illustration or none.** No sketch-style SVG scenes or doodle grain imitating
  pictures. SVG for geometry, diagrams, icons and linework stays welcome.

## Motion safety

- **Animate `transform` and `opacity` by default.** `filter`, `clip-path`, `mask` and
  `backdrop-filter` are fine when they stay smooth on a mid-range phone. Never animate
  layout properties (`top`, `left`, `width`, `height`). Use `will-change` only on elements
  that actually animate.
- **No per-frame scroll work.** No unthrottled `scroll` listeners and no scroll position
  kept in component state. Use `IntersectionObserver`, CSS scroll-driven animation, or a
  motion library's scroll primitives.
- **Reduced motion is honoured.** Under `prefers-reduced-motion: reduce`, loops, parallax,
  scroll-linked effects and physics collapse to static or a plain fade.
- **Grain and noise** sit on a fixed, `pointer-events: none` layer, never on a scrolling
  container.

## Content honesty

- **Nothing invented is shown as real.** No made-up testimonials, names, client logos,
  metrics or prices. Missing content gets a visible placeholder tagged
  "Confirm with <owner>" and a line in the owner-questions list.
- **Numbers come from supplied truth.** Precise-looking figures (92%, 4.1×, 5.8 mm) either
  come from the brief or the brand, or are labelled as sample data.
- **Quotes are attributed** with name and role (and company when relevant), never a first
  name alone.
- **No fake product UI.** Never fake a screenshot, dashboard or terminal out of styled
  boxes. Use a real screenshot, an approved image, a real component preview, or nothing.
- **Re-read every visible string** before showing the page: headings, labels, buttons,
  captions, alt text, errors. Rewrite anything grammatically broken, vague, or cute in a
  way that doesn't track. Plain beats clever.
- **No em-dash or en-dash in visible text.** Use a period, comma, colon or parentheses;
  ranges take a hyphen (2018-2026).
- **Banned filler words** live in one list: `../../../explore-design/references/web.md` §8.
- **Common generated-page tells** stay out unless the brief asks for them: version labels
  in the hero (V0.6, BETA), numbered section labels (001 · Capabilities), scroll cues,
  decorative status dots, pills or credits laid over photos, version strings in marketing
  footers, decorative locale/time/weather strips.

## Theme and dark mode

- **One theme per page.** Sections don't flip between light and dark; tints within the
  same theme family are fine. One deliberate theme switch is allowed only when the brief
  asks for it.
- When dark mode is in scope: pick one token strategy (utility variants or CSS variables)
  and keep it; keep the brand colour recognisable; keep the hierarchy that works in light
  working in dark; avoid pure `#000`/`#fff`; respect `prefers-color-scheme` unless the
  brand insists on one mode. Test every supported mode the change touches; don't add a
  mode the brief didn't ask for.

## Launch checklist

Every page that will go live, and every mock meant to become one, shows or reserves:

- [ ] `<title>` and meta description
- [ ] Open Graph / social tags with an `og:image`
- [ ] A branded favicon
- [ ] Alt text on every meaningful image (empty `alt` on decorative ones)
- [ ] Landmarks: `header`, `nav`, `main`, `footer`; headings in order
- [ ] A "skip to content" link
- [ ] Client-side validation on forms (required fields, email format) with inline errors
- [ ] A custom 404 page
- [ ] Privacy and terms links in the footer
- [ ] A cookie-consent notice where the audience's jurisdiction requires one
- [ ] A way back from every page

## Sources

Adapted from several open-source skills; attribution and licence texts are in
`../../NOTICE`.
