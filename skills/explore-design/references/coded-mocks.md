# Coded mocks

Use for page or section mocks built as HTML/CSS (plus SVG and, where needed, image-model
photography). Aesthetic direction lives in [web](web.md). Scope, routing and approval
live in [medium and providers](medium-and-providers.md).

## Folder

One mocks folder per round, outside every git tree:

```
<mocks>/
  README.md              gate log: each decision, date, and who made it
  content.md             the only copy source for every mock
  owner-questions.md     unconfirmed facts to ask the client
  generation-prompts.md  exact prompt per generated image (when images are used)
  ASSET-LICENSES.md      per asset: source/model, effort, license boundary
  deck-ref/              renders of the brand source (e.g. pdftoppm pages)
  assets/{brand,img,masters}/
  shared/                tokens.css, components.css, sprites/SVG shared by all directions
  type-test.html         specimen page for the type gate
  mock-a.html mock-b.html mock-c.html
```

Add a preview server entry (e.g. `.claude/launch.json`, port not in use) for the folder.

## Build rules

- **Same content, different language.** All directions use `content.md` word for word,
  so the user compares visual language, not copy. Directions may differ in headline
  only when the explore doc says so.
- **Shared base first.** Tokens, the brand's signature components (e.g. nameplate cards,
  sticky chat bar, tier tabs), and SVG line art go in `shared/` once; directions
  restyle them through tokens rather than forking markup.
- **Real brand material.** Real logo file, exact palette values, real prices and names.
  Never AI-generate a logo, a real person's likeness, or readable text.
- **Honest placeholders.** Unconfirmed facts carry a visible "Confirm with <owner>" tag;
  placeholder reviews are labelled as placeholders. Never invent testimonials.
- **Production-ready structure.** Semantic HTML, the project's CSS approach, no build
  step unless the project has one, relative asset paths (Lavish serves the folder).
- **Respect project hard rules** (e.g. text on panels, demo banner, noindex) in mocks
  too; a redesign may reinterpret how a rule looks, not drop it.

## Type gate

Build `type-test.html` with each candidate on the real brand colours, set in a hero
headline, a price, and the signature component. Offer candidates along feeling axes
(premium/sophisticated · comfort/warmth · modern) as complete pairings (display + text +
accent), plus closest matches to the brand source only if the user wants fidelity.
Directions may use different pairings; the user maps them at the gate.

## Review

1. Render each mock at 390px and 1440px; check horizontal overflow, page height (in
   phone screens), and that the primary action stays reachable.
2. Show screenshots in chat (phone + desktop per direction).
3. Open Lavish per [Lavish review](lavish-review.md) on the mock files for element-level annotation; for the pick, a
   review page using the Lavish `input` playbook (radio per question) returns an exact
   choice.
4. Apply annotations as targeted edits to the named element; re-screenshot only what
   changed.
5. Record the pick in README. The approved mock is the spec for `/implement`
   ([mock to code](../../implement/references/mock-to-code.md)).
