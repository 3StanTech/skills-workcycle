# Medium and providers

Read at Stage 2 (medium choice) and before any image batch. It owns scope, the choice of medium,
provider routing, approval, and handoff rules. Individual references own the
aesthetic and implementation detail.

1. Identify the actual deliverable: a brand board, website concept, mobile flow, or
   implementation. Follow the user's brief and existing project design system before
   defaults in a style reference. A targeted fix does not become a redesign.
2. Inspect the existing framework, packages, tokens, assets, hosting, and relevant
   project budget before choosing a provider or installing a dependency. Check existing
   supported capabilities first; use the selected provider's reference only. Confirm
   current official APIs before applying version-specific examples. Do not replace a
   project's stack to satisfy a design preset or trigger automatic package installation.
3. For meaningful visual changes, prepare mocks before implementation. Choose the medium
   (below) per asset, not per project. Reuse supplied or approved references when they
   already define the design; generate new references when direction is missing. Set
   image count, format, and viewport to the agreed output. A section count is not
   automatically an image count. If scope is unclear, propose a concrete small set
   before generating; preserve any user-specified count.
4. Inspect every generated image or rendered mock yourself, and preview every one offered
   for selection or approval inline in chat (a contact sheet is fine for sets). Do not ask
   users to approve filenames. Obtain mock approval before implementation. Regenerate
   unreadable details when necessary without silently expanding the deliverable; do not
   substitute a crop that loses layout information.
5. Extract layout, typography, spacing, colors, and component behavior from approved
   references. Preserve tokens, responsive structure, semantics, keyboard operation,
   contrast, and reduced-motion support. Do not invent testimonials or product facts;
   unconfirmed content is visibly tagged in mocks and listed for the owner.
6. Verify the changed visual scope at relevant viewports and states. Layout-sensitive
   delivered artifacts require rendered inspection. Do not add unrelated tests, new
   themes, or redesign passes to a small edit. Report missing evidence or deviations.

## Imagery question

The single owner of the imagery choice. explore-design asks it at Stage 2 and landing-page asks it before a standalone build; both cite this section.

Ask once, as a decision-point question: where do the pictures come from?

- **AI image generation** (an image worker; costs a delegated run per batch)
- **Claude-made visuals:** code, SVG, CSS or canvas (illustration, patterns, diagrams, product framing)
- **The owner's or licensed photos** (supplied files or open-license sources)
- **A mix**, chosen per asset

The three sources are equal choices. Recommend one only from the brief (for example the owner's photos when they exist, or AI when photoreal scenes are needed and none exist); otherwise mark none as recommended. Ask the image-worker model and effort only when AI is in the answer. Record the answer in the mocks README gate log (or the page plan's Start here), and generate nothing the answer does not cover. A source that cannot supply an asset gets a labelled placeholder slot and a line in `owner-questions.md`, never a substitute from another source.

## Medium: code or image model

| Asset | Medium | Why |
|---|---|---|
| Page and section mocks when the brand is set (palette, logo, prices, tone known) | **Coded HTML/CSS**, rendered and screenshotted | Exact type, colors, logo and copy; annotate per element in Lavish; responsive in one file; the winner carries into the build |
| Logos, icons, line art, patterns, badges, simple illustration | **SVG** (Claude-drawn) | Exact, scalable, editable. Complex illustrative marks may start from an image model, then get redrawn as SVG |
| Generative textures, backgrounds, motion studies | **Canvas / p5.js / CSS** | Code-native; see `algorithmic-art` |
| Photography (food, places, products, scenes), painterly illustration | **Image model** | Code cannot produce photoreal or painterly raster |
| Loose moodboards when the direction is wide open (new brand, no references) and AI imagery was chosen | **Image model**, few frames (G2, optional) | Fastest way to explore feel; recode after approval. Otherwise the coded sample mocks compare the directions |

Image models garble text and cannot reproduce a real logo: keep readable text, prices,
and logos out of generated images and layer them in code.

## Image-model providers

Every image worker is a delegated launch: obtain an explicit model and effort per
AGENTS.md → Delegation, launch through the `headless` wrappers, and never substitute a
family after a failure.

| Route | Status | Notes |
|---|---|---|
| Codex (GPT) via `run-codex.sh` | Proven 2026-09-29 (`gpt-6-sol` medium, 10 images, ~45 s each) | Lane B; output lands in `~/.codex/generated_images/<thread-id>/`; resume the same thread for more images |
| Grok `image_gen` via `run-grok.sh` | Proven 2026-07-31 (Beholden) | See `headless/references/engine-grok.md` |
| Figma Weave (`weave_find_model` / `weave_run_model`) | Available in Claude sessions with the Figma connector | Runs named models (e.g. nano banana) without a headless worker; spends Weave credits; quote the cost and get approval before every run |

Image-batch discipline: generate one probe image first and preview it before the batch; keep
one image worker at a time to protect session limits; log each exact prompt in
`generation-prompts.md` as it is generated; map outputs to names by generation time and
aspect ratio; record each image's model, effort, and license boundary per the project's
asset rules.

Examples and numeric presets in specialized references are options for the agreed
brief, not requirements to enlarge it. Image-only routes stop after image delivery;
implementation routes continue only through the approved implementation scope.
