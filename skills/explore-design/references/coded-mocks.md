# Coded mocks

Use for page or section mocks built as HTML/CSS (plus SVG and, where needed, image-model
photography). Aesthetic direction lives in [web](web.md). Scope, routing and approval
live in [medium and providers](medium-and-providers.md).

## Folder

One mocks folder per round, outside every git tree:

```
<mocks>/
  README.md              gate log: each decision, date, and who made it
  restatement.md         the confirmed restatement, verbatim and dated (Stage 1)
  content.md             the only copy source for every mock
  owner-questions.md     unconfirmed facts to ask the client
  generation-prompts.md  exact prompt per generated image (when images are used)
  ASSET-LICENSES.md      per asset: source/model, effort, license boundary
  deck-ref/              renders of the brand source (e.g. pdftoppm pages)
  assets/{brand,img,masters}/
  shared/                tokens.css, components.css, sprites/SVG shared by all directions;
                         viewer-config.js, options-sheet.js, mock-live.js (from live-viewer/)
  type-test.html         specimen page for the type gate
  mock-a.html mock-b.html mock-c.html   one sample per direction
  mock-b2.html …         extra samples of a direction, on request
  compare.html           the live viewer (from live-viewer/)
  tools/                 sandbox-prep.mjs, sandbox-test.html, sandbox-e2e.mjs, lavish-warnings.mjs
                         (from live-viewer/)
  background/            optional: copied background recipe files
  approved/              the exported winner
```

Add a preview server entry (e.g. `.claude/launch.json`, port not in use) for the folder.

## Build rules

- **Build on the floor.** Every mock follows [ui-build](../../implement/references/ui-build.md)
  Pillars 1–4 and [page craft](../../implement/references/ui-build/page-craft.md). A
  direction changes the look, never the floor.
- **Same content, different language.** All directions use `content.md` word for word,
  so the user compares visual language, not copy. Directions may differ in headline
  only when the explore doc says so.
- **Shared base first.** Tokens, the brand's signature components (e.g. nameplate cards,
  sticky chat bar, tier tabs), and SVG line art go in `shared/` once; directions
  restyle them through tokens rather than forking markup. Keyframe names are unique
  across shared stylesheets; a clash silently replaces one animation with another and
  shows only with motion on.
- **Real brand material.** Real logo file, exact palette values, real prices and names.
  Never AI-generate a logo, a real person's likeness, or readable text.
- **Honest placeholders.** Unconfirmed facts carry a visible "Confirm with <owner>" tag;
  placeholder reviews are labelled as placeholders. Never invent testimonials.
- **Production-ready structure.** Semantic HTML, the project's CSS approach, no build
  step unless the project has one (`tools/sandbox-prep.mjs` is the exception when a mock
  keeps ES modules, local JSON or font files), relative asset paths (Lavish serves the folder).
- **Sandbox-safe, one copy.** Classic scripts only (no `type="module"`), no runtime
  `fetch()` of local files (embed data), fonts embedded or system, every linked page
  inside the mocks folder, every storage call in try/catch. Each mock loads the three
  shared review scripts and takes its options from URL params and `mock-set` messages.
  A mock made from a site build is converted in place with `tools/sandbox-prep.mjs`,
  never copied a second time for Lavish. See [live viewer](live-viewer.md).
- **Layout that passes Lavish first time** ([known fixes](lavish-review.md#before-the-owner-sees-it)):
  a skip link is hidden in place (clipped to 1px, shown on focus), never off-screen;
  folded content is `display: none`, never clipped by height or `visibility`.
- **Page colour on `<html>`**, not `<body>`, when a fixed canvas sits at a negative
  `z-index`; a body background covers it.
- **Respect project hard rules** (e.g. text on panels, demo banner, noindex) in mocks
  too; a redesign may reinterpret how a rule looks, not drop it.

## Sample round

- **One coded sample per chosen direction** (`mock-a/b/c.html`), all built from `content.md`
  word for word, on the shared base and the floor.
- **More on request:** extra samples of a direction are numbered (`mock-b2.html`,
  `mock-b3.html`) and differ in layout or treatment, not copy.
- **Count and cost first:** state the number of pages before building. Past **6 mocks per
  round**, re-confirm the count and cost with the owner.
- **Compare:** `compare.html` is the [live viewer](live-viewer.md): every sample, page and
  option switchable in place at desktop and phone width, each sample with a one-line why.
  The sandbox test and the layout pre-flight pass before it opens. The owner queues a
  winner or a named mix; only the winner goes to G4. A contact sheet in chat is a
  preview, not the pick.

## Type gate

Build `type-test.html` with each candidate on the real brand colours, set in a hero
headline, a price, and the signature component. Offer candidates along feeling axes
(premium/sophisticated · comfort/warmth · modern) as complete pairings (display + text +
accent), plus closest matches to the brand source only if the user wants fidelity.
A single-typeface direction (e.g. clean-geist) is offered single faces instead of
pairings. Directions may use different pairings; the user maps them at the gate.

## Review

1. Render each mock at 390px and 1440px; check horizontal overflow, page height (in
   phone screens), and that the primary action stays reachable. Run the
   [page craft](../../implement/references/ui-build/page-craft.md) checks, launch
   checklist included.
2. Show screenshots in chat (phone + desktop per sample). Full-page shots of a page with
   a fixed background are stitched viewport by viewport (a single tall capture shows the
   fixed layer only at the top); check the captured page height and re-shoot a short
   capture; fine detail (stars, hairlines, grain) is shown live or at 1:1, never judged
   from a small crop.
3. Compare the samples in the viewer (`compare.html`, above) and record the owner's pick;
   a one-mock review is the mock with the docked sheet. The sandbox test and the
   pre-flight run first. When Stage 2 put
   the background in scope, run the Background step on the winner next
   ([backgrounds](backgrounds.md)).
4. Open Lavish per [Lavish review](lavish-review.md) on the winner for element-level
   annotation, with the docked sheet for its options and the final pick. The `input`
   playbook is for non-visual choices; visual ones go through the viewer.
5. Apply annotations as targeted edits to the named element; re-screenshot only what
   changed.
6. Record the pick in README. The approved mock is the spec for `/implement`
   ([mock to code](../../implement/references/mock-to-code.md)).
