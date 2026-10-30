# Redesign preservation and quality checks

Use only for the relevant phase of the agreed brief. Scope and approval are owned by
[medium and providers](../../medium-and-providers.md). Examples are not extra deliverables.

## 9. AI TELLS (Forbidden Patterns)

Avoid these signatures unless the brief explicitly asks for them. Production-test tells, dashes and invented content are floor rules ([page craft → Content honesty](../../../../implement/references/ui-build/page-craft.md#content-honesty)).

### 9.A Visual & CSS
* **NO neon / outer glows** by default. Use inner borders or subtle tinted shadows.
* **NO pure black (`#000000`).** Off-black, zinc-950, or charcoal.
* **NO oversaturated accents.** Desaturate to blend with neutrals.
* **NO excessive gradient text** for large headers.
* **NO custom mouse cursors.** Outdated, accessibility-hostile, perf-hostile.

### 9.B Typography
* **AVOID Inter as default.** See Section 4.1. Override path exists.
* **NO oversized H1s** that just scream. Control hierarchy with weight + color, not raw scale.
* **Serif constraints:** Serif for editorial / luxury / publication. Not for dashboards.

### 9.C Layout & Spacing
* **NO 3-column equal feature cards.** The generic "three identical cards horizontally" feature row is banned. Use 2-column zig-zag, asymmetric grid, scroll-pinned, or horizontal-scroll alternative.

### 9.D Content & Data ("Jane Doe" Effect)
* Names, numbers, brand names and filler words: never invented as real. Rules live in the floor: [page-craft.md → Content honesty](../../../../implement/references/ui-build/page-craft.md#content-honesty); banned words in [web.md §8](../../web.md).
* **NO generic avatars.** No SVG "egg" or Lucide user icons → use believable photo placeholders or specific styling.

### 9.E External Resources & Components
* **NO hand-rolled SVG icons.** Use Phosphor / HugeIcons / Radix / Tabler. Lucide on explicit request only.
* **Hand-rolled decorative SVGs strongly discouraged** as default, unless the owner chose Claude-made visuals (see Section 4.8).
* **Placeholder photos:** `https://picsum.photos/seed/{descriptive-string}/{w}/{h}` or actual assets, not hotlinked Unsplash URLs (broken images are a floor launch-checklist item).
* **shadcn/ui customization:** Allowed, but NEVER in default state. Customize radii, colors, shadows, typography to the project aesthetic.

---

## 11. REDESIGN PROTOCOL

This skill handles **greenfield builds AND redesigns**. Misclassifying the mode is the single biggest source of bad redesign output.

### 11.A Detect the Mode (first action)
* **Greenfield** - no existing site, or full overhaul approved. Dial baseline from Section 1.
* **Redesign - Preserve** - modernise without breaking the brand. Audit first, extract brand tokens, evolve gradually.
* **Redesign - Overhaul** - new visual language on top of existing content. Treat as greenfield for visuals; preserve content and IA.

If ambiguous, ask **once**: *"Should this redesign preserve the existing brand, or are we starting visually from scratch?"*

### 11.B Audit Before Touching
Document the current state before proposing changes:
* **Brand tokens** - primary / accent colors, type stack, logo treatment, radii.
* **Information architecture** - page tree, primary nav, key conversion paths.
* **Content blocks** - what exists, what's doing work, what's filler.
* **Patterns to preserve** - signature interactions, recognisable hero, copy voice.
* **Patterns to retire** - AI-slop tells, broken layouts, dead links, generic stock imagery, perf traps.
* **Dial reading of the existing site** - infer current `DESIGN_VARIANCE` / `MOTION_INTENSITY` / `VISUAL_DENSITY`. That's your starting point, not the baseline.
* **SEO baseline** - current ranking pages, meta titles, structured data, OG cards (a floor rule: [ui-build → Redesigns](../../../../implement/references/ui-build.md#redesigns)).

### 11.C Preservation Rules
What a redesign never changes silently (IA, slugs, anchor IDs, nav labels, form fields, analytics hooks, logo, legal copy, accessibility wins) is a floor rule: [ui-build → Redesigns](../../../../implement/references/ui-build.md#redesigns). Taste adds:
* **Extract brand colors before applying Section 4.2.** A brand that is already purple stays purple - apply the LILA RULE's override.
* **Preserve copy voice** unless asked for a rewrite. Visual modernisation ≠ content rewrite.

### 11.D Modernisation Levers (priority order)
Apply in order - stop when the brief is satisfied:
1. **Typography refresh** - biggest visual lift per unit of risk.
2. **Spacing & rhythm** - increase section padding, fix vertical rhythm.
3. **Color recalibration** - desaturate, unify neutrals, keep brand accent.
4. **Motion layer** - add `MOTION_INTENSITY`-appropriate micro-interactions to existing components.
5. **Hero & key-section recomposition** - restructure top-of-funnel using Section 10 vocabulary.
6. **Full block replacement** - only when the existing block is unsalvageable.

### 11.E Decision Tree: Targeted Evolution vs Full Redesign
* IA, content, and SEO sound → **targeted evolution** (Levers 1-4). ~70% of value at ~40% of risk.
* Visual debt is structural (broken IA, no design system, broken mobile) → **full redesign** with strict content preservation.
* Brand itself is changing → **greenfield**.

---

## 13. OUT OF SCOPE

Taste is for landing pages, portfolios and marketing redesigns. Dashboards, dense product UI, data tables, multi-step forms, code editors, native mobile and realtime collaboration UIs are not its job: say so, point to a fitting design system (Section 2.A), and apply taste only to the marketing surfaces. Lanes: explore-design chooses a look, landing-page plans and builds one page, impeccable polishes an existing UI.

---

## 14. FINAL PRE-FLIGHT CHECK

Run this matrix before outputting code. This is the last filter.

**THIS IS NOT OPTIONAL. Run every box. If any box fails, the output is not done.**

- [ ] **Floor checks pass**: every section of [page-craft.md](../../../../implement/references/ui-build/page-craft.md) (composition, visual craft, motion safety, content honesty, theme, launch checklist) and the [ui-build.md](../../../../implement/references/ui-build.md) pillars. Taste's own boxes follow.
- [ ] **Brief inference** declared (Section 0.B one-liner)?
- [ ] **Dial values** explicit and reasoned from the brief, not silently using baseline?
- [ ] **Design system** chosen from Section 2 if applicable, or aesthetic labeled honestly?
- [ ] **Redesign mode** detected and audit performed (if applicable, Section 11)?
- [ ] **Color Consistency Lock**: one accent color used identically across all sections (Section 4.2)?
- [ ] **Serif discipline**: if a serif is used, it is NOT Fraunces or Instrument_Serif (or it is, with explicit brand justification)? Different serif from your previous project?
- [ ] **Premium-consumer palette check**: if the brief is premium-consumer (cookware / wellness / artisan / luxury), the palette is NOT the AI-default beige+brass+oxblood+espresso family? Different family from your previous premium-consumer project?
- [ ] **Split-Header Ban**: no "left big headline + right small explainer paragraph" pattern as a section header (vertical stack instead)?
- [ ] **Logo wall = logo only**: no industry / category labels printed below logos?
- [ ] **Bento Background Diversity**: at least 2-3 bento cells have real visual variation (image, gradient, pattern), not all white-on-white text cards?
- [ ] **"Used by / Trusted by" logo wall** lives UNDER the hero, not inside it, uses REAL SVG logos (Simple Icons / devicon) or a tagged placeholder mark, NOT plain text wordmarks?
- [ ] **Marquee max-one-per-page**: no two horizontal marquees on the same page?
- [ ] **Bento has rhythm** (exact cell count is a floor check)?
- [ ] **Long lists use the right UI component** (not default `<ul>` with `divide-y` for > 5 items - see Section 4.9 alternatives)?
- [ ] **Imagery from the owner's chosen medium** (Section 4.8), explicit placeholder slots where assets are missing - NO hand-rolled decorative SVGs unless Claude-made visuals were chosen, NO pure-text minimalism unless the brief is typographic?
- [ ] **Content density** sane: ≤ 25-word sub-paragraphs by default, long lists in the right component (Section 4.9)?
- [ ] **Quotes ≤ 3 lines** of body?
- [ ] **Motion claimed = motion shown**: if `MOTION_INTENSITY > 4`, page actually animates, not just claimed?
- [ ] **GSAP sticky-stack / horizontal-pan** implemented per the [motion skeletons](motion-skeletons.md) (`start: "top top"`, `pin: true`, correct scrub)?
- [ ] **`useEffect` animations** have strict cleanup functions?
- [ ] **Cards omitted** in favor of spacing where possible?
- [ ] **Icons** from an allowed library only (Phosphor / HugeIcons / Radix / Tabler), no hand-rolled SVG paths?
- [ ] **Motion** isolated in client-leaf components with `'use client'` at the top, memoized?
- [ ] **No AI Tells** from Section 9 (Inter as default, AI-purple, three-equal cards, Jane Doe, Acme, "Quietly in use at")?
- [ ] **One design system** per project (no Material + shadcn mixed)?

If a single checkbox cannot be honestly ticked, the page is not done. Fix it before delivering.

---
