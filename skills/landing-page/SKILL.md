---
name: landing-page
description: >-
  Plan and build one conversion-focused page (client one-pager, promo page,
  product or service page, own site): intake, page plan, approval, one
  direction, a section-by-section build on the shared quality floor, and a
  launch checklist. Also runs as explore-design's page-plan step. Trigger:
  /landing-page, $landing-page, "build a landing page", "write a sales page",
  "plan a one-pager", "promo page", "conversion copy for this page". Not for
  comparing looks or mock rounds (explore-design), polishing an existing UI
  (impeccable), or redesigning a whole existing site.
---

# Landing page

A landing page wins one intent: **one offer → one audience → one primary action.** This skill decides what the page says and how it is structured, then builds it on the shared floor. How it looks comes from a direction; how well it is built comes from the floor.

**Decision points:** If an interactive question tool (e.g. `AskUserQuestion`) is available, use it with 2–4 prefilled options, recommended option first and labeled "(Recommended)". Otherwise, print the same options as a numbered list in chat, state the recommended number, and wait for a reply. Never proceed past a decision point on an assumption.

## Two ways in

| Run | Steps | Output |
|---|---|---|
| Standalone (`/landing-page`) | 1 Intake → 2 Page plan → approval → 3 Direction and imagery → 4 Build → 5 Launch | An approved page plan file, then the built page |
| Inside explore-design (page-plan step) | 1 Intake → 2 Page plan → approval, then return | The mocks folder's `content.md`; explore-design builds the mocks |

## Boundary

- **Honest content.** Follow the floor's [content honesty](../implement/references/ui-build/page-craft.md#content-honesty) rules: no invented testimonials, names, client logos, numbers, prices or guarantees. A fact the owner has not given is asked; if it stays unanswered it becomes a visible "Confirm with <owner>" placeholder and a line in an owner-questions list. Never "assume and continue".
- **Plan before build.** Nothing is built until the owner approves the page plan.
- **Project first.** The build follows the project's stack, components and brand. With no project, build a static page in a folder the owner names, outside every git tree unless the owner says otherwise.
- **The floor is not repeated here.** States, accessibility, motion safety, the launch checklist and the banned-word list live in [ui-build](../implement/references/ui-build.md), [page craft](../implement/references/ui-build/page-craft.md) and [web](../explore-design/references/web.md) §8.

---

## 1. Intake

Gather what is missing, in **one batch**, as a short list the owner can answer inline. Skip anything the brief or project already answers, and say what you took from where.

- **Purpose:** the one primary action (call, booking, inquiry, purchase, sign-up, download, waitlist); the offer, exactly what they get; what counts as a conversion.
- **Audience and context:** who the page is for; the problem they are solving; the **top three objections** (why they do not act today); where traffic comes from (ads, search, social, email, referrals, a QR code); what visitors already know when they land.
- **Proof and assets:** real proof points (clients, testimonials with permission, numbers, case studies, portfolio); screenshots, photos, video; guarantees, refund, cancellation or revision terms.
- **Constraints:** voice (casual or professional), language, mobile priority, existing brand, legal must-haves (privacy, cookie consent, regulated claims).

**STOP** for answers. Unanswered facts go to the owner-questions list; the plan shows them as tagged placeholders.

## 2. Page plan

Decide the structure, the layout and the copy, then present them in this order:

1. **Page outline:** sections in order.
2. **Hero copy:** headline, subheadline, primary CTA, one proof line.
3. **Benefits:** three to five, outcome first.
4. **How it works:** three steps.
5. **FAQ:** six to twelve real questions and answers, built from the objections.
6. **SEO / AEO:** index or noindex, with the reason; title and meta description when indexed.
7. **Layout:** A, B, C or D, and why.

### Structure

- **Above the fold:** headline (outcome + audience), subheadline (how, and for whom), primary CTA (a verb plus what they get), one proof signal (client strip, a real number, a short attributed quote), a hero visual (real product, work sample, photo or an honest illustration).
- **The argument:** problem to solution (one section), benefits, how it works, proof (testimonials or a case study, placed beside the claim it supports).
- **Objection handling:** FAQ, risk reversal (trial, guarantee, revision terms, cancel anytime: only terms the owner confirms), final CTA identical to the top one.

### Layout

| Type | Use when |
|---|---|
| **A. Classic hero plus sections** | The offer is clear from one hero visual. Most common |
| **B. Long-form story** | Visitors need educating, or skepticism is high |
| **C. Minimal conversion page** | High-intent traffic (email to known contacts), or a short offer such as a download, booking or waitlist |
| **D. Comparison page** | Search intent names alternatives ("X vs Y", "best for") |

### Conversion rules

- **Match message to source.** Ad traffic sees the ad's promise and tone in the hero.
- **One next step.** One primary CTA; nothing competing above the fold.
- **Benefit first.** Features say what it does; benefits say what that means for the visitor.
- **Be specific.** Not "save time and streamline", but "your site live in 10 working days" (only with the owner's real figure).
- **Reduce risk** with at least one term the owner confirms.
- **Objections are a section, not a footnote.** Move the FAQ earlier for high-friction offers.

### Copy

- Headline patterns: "{Outcome} without {pain}", "The {category} for {audience}", "{Result} in {time}".
- Subheadline: one or two sentences on what it is and who it is for.
- CTA: a verb plus what they get ("Book a call", "Get the quote", "Start free trial"); never "Learn more" or "Submit".
- Benefit bullets: the benefit in bold, then the proof or detail.
- Plain, specific words; no banned filler ([web](../explore-design/references/web.md) §8).

### SEO and AEO

- **noindex** ad-only campaign pages and short-lived offers.
- **Index** evergreen offers whose search intent matches the promise: a clear title and meta description, internal links from the home and related pages, the FAQ in plain question-and-answer form, FAQ schema when it fits.

### Pitfalls

Too many CTAs above the fold; a vague promise ("streamline", "optimize"); a feature list with no outcomes; proof buried at the bottom; a phone layout that hurts reading; no clear next step.

### Where the plan goes

- **Standalone:** save it to `plans/page-plan-YYYY-MM-DD-<slug>.md` in the project folder, outside the git tree (a git project uses its handoffs folder, as explore does). Give it a Start here block and run the cold-start gate (`~/.agents/skills/handoff/references/cold-start-gate.md`), so the build can resume in a new session with `/landing-page <plan path>`.
- **Inside explore-design:** write the same content to the mocks folder's `content.md`, the only copy source for every mock, and the open facts to `owner-questions.md`. Then return to explore-design.

**STOP** for approval of the plan. Apply corrections and show what changed.

## 3. Direction and imagery (standalone only)

1. **Direction:** the project's existing brand comes first ("re-align"). Without one, offer 2–3 directions from the [direction library](../explore-design/references/directions/README.md) with a one-line idea each and take one pick. Comparing several looks as built pages is explore-design's job; offer `/explore-design` if the owner wants that.
2. **Imagery:** ask the imagery question per [medium and providers](../explore-design/references/medium-and-providers.md#imagery-question). Model and effort are asked only when AI images are chosen.

**STOP** for the picks.

## 4. Build

- Build **section by section** in this order: hero, benefits, how it works, proof, FAQ, final CTA, then the remaining sections from the plan. Never regenerate the whole page on an iteration; edit the section concerned.
- Build on the floor ([ui-build](../implement/references/ui-build.md) Pillars 1–4 and [page craft](../implement/references/ui-build/page-craft.md)) plus the chosen direction file. A direction changes the look, never the floor.
- Use the approved plan's copy word for word; tagged placeholders stay visible.
- Render at phone (390px) and desktop (1440px) after each section that changes layout; fix overflow and reading problems before the next section.

## 5. Launch

1. Run the floor's [launch checklist](../implement/references/ui-build/page-craft.md#launch-checklist).
2. Check the strategy: one offer, one audience, one primary action; no competing CTAs above the fold; specific claims backed by owner facts; at least one confirmed risk reversal; proof beside its claim; the layout type chosen on purpose; index or noindex set as planned.
3. Show phone and desktop screenshots and list the open owner questions.

## Resumability

The page plan file is the resume point. After approval, record the direction, imagery answer and the last built section in its Start here, and rerun the gate at each stop.

## Guardrails

- Never invent facts, people, quotes, logos, numbers or terms; tag and ask.
- Never build before the plan is approved.
- Never generate images unless the owner chose AI imagery and approved model, effort and count.
- Never take over another lane: mock rounds belong to explore-design, polish to impeccable.

## Origin

Part A (strategy and structure) of Elaya's `landing-page-design` skill, adapted (MIT; see `NOTICE`). Its visual system was split: craft rules went to implement's floor, the look became explore-design's `clean-geist` direction.
