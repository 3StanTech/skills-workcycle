# Web direction

Aesthetic guidance for website mocks in any medium (coded, image model) and for
[mock to code](../../implement/references/mock-to-code.md).
The brief and the project's brand always override these defaults. Scope, count and
approval belong to [medium and providers](medium-and-providers.md). These are direction
defaults; the quality floor every direction keeps lives in implement's
[ui-build](../../implement/references/ui-build.md) and
[page craft](../../implement/references/ui-build/page-craft.md).

## 1. Read the brief into a direction

| Brief says | Hero scale | Backgrounds | Composition |
|---|---|---|---|
| minimalist, clean, swiss, typography-only | Mini | Solid, subtle texture, at most one color-blocked diptych; skip gradients | Stacked center, generous negative space |
| editorial, magazine, art-directed | Mid or Giant | Editorial side-image, duotone, graded photo | Off-grid offsets, strong type contrast |
| cinematic, premium, luxury, bold | Giant | Full-bleed image + tonal overlay, vignette, micro-noise | Bottom-left over image, centered low |
| SaaS, product, fintech, infra | Mid | Solid + inline asset, flat block + detail crop | Clear product framing, trust anchors |
| agency, studio, portfolio | Giant or Mini (decisive) | Bold variety | Off-grid, poster-like |
| shop, product page | Mid, product-led | Full-bleed product, vignette + crop | Product first; unmistakable CTAs |
| local business, food, family brand | Mid | Warm photography, tactile paper/material | Image-led, chat/call action always reachable |

Silent brief: pick one hero scale decisively; do not split the difference. Match the
industry and region's temperament instead of a default neutral startup look.

## 2. Commit to one combination

Choose one of each and execute it consistently; do not mash options together.

- **Theme:** pristine light · deep dark · bold studio solid · quiet premium neutral.
- **Type character:** clean grotesk · refined grotesk · expressive display · compressed
  statement · editorial serif + sans · Swiss rational sans.
- **Hero architecture:** centered minimalist · asymmetric split · editorial offset ·
  typography behemoth · image-first with restrained text.
- **Section system:** modular bento · alternating editorial · poster storytelling ·
  gallery cadence · Swiss grid.
- **Narrative spine (optional):** artifact · journey · precision tool · living system ·
  stage · archive. Let it thread through visuals and short copy.
- **One second-read moment:** a single deliberate motif (asymmetric bleed, oversized
  numeral, material switch, side-rail note, macro crop) that aids scan order or recall.

## 3. Hero

- Short, strong headline (about 5–10 words), concise support, one obvious action.
- Left-text/right-image is allowed but is the most overused default; reach for it only
  when it is the best fit.
- No pills, fake stats, badges, or tiny logos crowding the first viewport. A small
  laptop and a phone must both see headline, support, CTA, and a focal visual.

## 4. Composition and rhythm

- Each section has a job (hook, proof, educate, convert) and an anchor: centered
  statement, top-left lead, bottom-left over image, right-third caption, centered low,
  off-grid offset, stacked center, image-as-canvas.
- Vary anchors and background modes across sections; do not repeat the same anchor more
  than twice in a row. Minimalist briefs are exempt: restraint is the design.
- Vary density and intensity (lighter → richer → calmer), but keep section spacing even
  and generous; smaller sections still get breathing room.
- One unmistakable primary action per viewport tier; secondary actions look secondary.
  Vary CTA style (pill, outline, inline arrow, banner) without hiding the primary.

## 5. Imagery

- Images are design material: hero media, framed panels, editorial crops, full-bleed
  backgrounds with overlays where the brief allows.
- Use fixed, repeatable aspect ratios and one image treatment (grade, framing) across
  the site; mix at least two crop types (macro + context).
- Images match the palette; overlays keep text readable. No irrelevant scenery, stock
  clichés, or tiny decorative thumbnails.

## 6. Color and material

- One palette: primary, secondary, one sparing accent, neutral scale. Section mood
  shifts reuse it; no theme swap per section.
- Gradients only when low-chroma and palette-matched (tonal grades, vignettes,
  noise-textured depth). Banned: rainbow/mesh blobs, purple-to-blue AI defaults,
  neon glows, gradient text.
- Don't retreat to plain white by default when the brand wants atmosphere; don't add
  atmosphere where the brief asks for restraint.

## 7. Typography

Typography is a primary material: clear size contrast, obvious reading order, short
controlled headlines, readable support text. Avoid shouting extra-bold everywhere,
awkward wraps, lazy all-caps, too many font moods.

## 8. Avoid (AI tells)

- **Layout:** endless centered sections, identical card rows, cloned split blocks,
  box-in-box-in-box containers, dashboard compartments without purpose.
- **Micro-clutter:** filler pills, chips, badges, pseudo-system labels ("00 orchestration
  layer"), meaningless metadata rows.
- **Visual:** glow edges, blobs, stacked glassmorphism, noise that hides layout.
- **Copy:** unleash, elevate, revolutionize, seamless, next-gen, transformative, supercharge,
  cutting edge, effortless, world class, game-changer, delve, "transform your workflow", "take it to the next
  level", "harness the power"; fake brands (Acme, Nexus, NovaCore). This is the single
  banned-word list. Write short, plain copy, or use the client's own.
- **Data:** identical KPI triplets, fake charts, unreadable logo marquees, unless asked.

## 9. Image-model frames (web images mode)

- Frame count and aspect follow the agreed deliverable: separate readable section frames
  when detail matters; never automatically one image per section.
- Lock one brand world across frames: type scale, spacing, CTA family, image treatment,
  palette. Composition and background mode may vary.
- Keep readable text, logos and prices out of generated frames when they will be coded.

## 10. Check before showing

1. Hierarchy obvious; hero clean; one primary action per viewport.
2. Distinctive, not template-like; no AI tells from §8.
3. Composition and background varied; spacing even and generous.
4. One palette and image treatment throughout.
5. Works at phone width: stacking order sane, tap targets and captions readable.
6. Someone could build it faithfully from this.
