---
name: explore-design
description: >-
  Explore a UI, brand or image idea and turn it into an approved mock:
  discovery, 2–3 directions, image moods, a coded mock refined in Lavish, then a
  cold-start explore doc for create-plan. Trigger: /explore-design,
  $explore-design, "design exploration", "mock this up", "mock round", "design
  concepts", "website/landing page mocks", "app screen concepts", "brand board",
  "logo system". Not for polishing or critiquing an existing UI (impeccable),
  building from an approved mock (implement), or non-visual ideas (explore).
---

# Explore design

Shape a visual idea with the owner, show it as mocks, refine the chosen one in Lavish, and write an explore doc whose spec is the approved mock.

## Purpose

The same four aims as [explore](../explore/SKILL.md) (the goal, the problem, the finish line, the direction), plus a fifth: **an approved mock** that `/implement` can apply instead of redesigning. Explore-design succeeds when the owner picks a mock in Lavish and create-plan can start from the doc without asking discovery questions again.

**Decision points:** If an interactive question tool (e.g. `AskUserQuestion`) is available, use it with 2–4 prefilled options, recommended option first and labeled "(Recommended)". Otherwise, print the same options as a numbered list in chat, state the recommended number, and wait for a reply. Never proceed past a decision point on an assumption. Follow explore's rules for explaining before re-asking and for reading free text inside answers.

**Tone:** friendly, plain English, one decision at a time. Interactive only: never run the stages autonomously unless the request says "no questions" or "just plan it".

## Boundary

- **No product source.** Mocks, images, specimens and Lavish pages live only in a mocks folder outside every git tree: `<project>/<slug>-mocks/` for a non-git project folder, `<project-parent>/<project>-handoffs/<slug>-mocks/` for a git repo, or the mocks rule in `~/.agents/local/workcycle.md` when it has one for this work. The plan-only hook enforces this for headless launches.
- **Image workers** need an explicit model and effort from the owner (`~/AGENTS.md` → Delegation) and launch through the `headless` wrappers with `--cwd` set to the mocks folder. One worker at a time.
- **Never AI-generate** a logo, a real person's likeness, or readable text. Layer text, prices and logos in code.
- **Honest content.** Unconfirmed facts carry a visible "Confirm with <owner>" tag and go in `owner-questions.md`. Never invent testimonials or product facts.
- A named implementer ("implement using …") is recorded verbatim in the doc and starts nothing.

---

## 1. Discover

**Goal:** a restatement the owner confirms, grounded in how the thing looks today.

1. Read the request and the project context (instruction files, `master.md`, brand sources, existing tokens).
2. **Render the current state** at phone (390px) and desktop (1366–1440px). Measure what matters: page height in phone screens, where the primary action sits and whether it stays reachable, text sitting on bare backgrounds, horizontal overflow.
3. **Check the brand with evidence,** not by eye: embedded fonts (`pdffonts` on a deck), exact palette values, the real logo file.
4. Ask 2–4 clarifying questions, always including **"Stay faithful to the current brand, evolve it, or explore new feels?"** That answer sets the directions, the type candidates and how far colour may move.
5. Write the restatement in explore's format and ask: Matches / Mostly, with corrections / Off.

**STOP** at the questions and at the restatement.

## 2. Directions and medium

**Goal:** 2–3 named directions, the medium for each asset, and the cost, agreed before anything is generated.

1. Propose 2–3 directions with a one-line idea each. One is always **"re-align and fix"** (the current brand, corrected). Seed the others from the [direction library](references/directions/README.md) when a feel matches; it is a starting point, never a requirement to enlarge the brief.
2. Choose the **medium per asset** with [medium and providers](references/medium-and-providers.md): image-model moods to pick a direction, coded HTML for the chosen page, SVG for marks and icons, an image model for photography.
3. State the cost: number of images, likely sessions. Ask the **image-worker model and effort** now (two questions, no "(Recommended)" label on a tier).
4. Create the mocks folder (layout in [coded mocks](references/coded-mocks.md)) with `README.md` (a Start here block plus the gate log), `content.md`, `owner-questions.md`, `generation-prompts.md`, `ASSET-LICENSES.md`.

**STOP** for the pick of directions and medium.

## 3. Mock round

Run the gates in order. Skip any gate the brief already settles and say so. Preview every gate inline in chat (a contact sheet is fine for sets). Record each decision in the README gate log the moment it is made, with the date.

| Gate | What happens | Reference |
|---|---|---|
| **G1 Type** | A specimen page with complete pairings along feeling axes, set on the real brand colours. Only when type is still open | [coded mocks → Type gate](references/coded-mocks.md) |
| **G2 Moods** | One probe image first, then one mood frame per direction as a contact sheet. The owner picks a direction (or a named mix) | [medium and providers](references/medium-and-providers.md), [web](references/web.md) |
| **G3 Mocks** | Coded HTML of the picked direction on the production stack's conventions; phone and desktop screenshots in chat | [coded mocks](references/coded-mocks.md), [web](references/web.md) |
| **G4 Refine** | Lavish opens on the mock; the owner annotates; each note becomes a targeted edit; the final pick comes back through an in-page form; the approved mock is exported | [Lavish review](references/lavish-review.md) |

**Modes** (from the deliverable the owner asked for):

| Mode | Gates | Reference |
|---|---|---|
| Web and app UI | G1–G4 | [web](references/web.md), [coded mocks](references/coded-mocks.md) |
| Mobile screens | G1, G2 (screen concepts as images), G4 only if HTML is built | [mobile](references/mobile.md) |
| Brand and logos | G1, G2 boards, marks redrawn as SVG, G4 on an HTML board | [brand](references/brand.md) |
| Image-only | G2, then stop and deliver; no doc unless asked | [medium and providers](references/medium-and-providers.md) |

A technical fix never triggers a new image set. Regenerate unreadable details without silently expanding the deliverable.

## 4. Scope

Follow explore's Stage 4: components with effort and dependencies, minimum version first. If the build needs 2 or more phases that each need their own plan, ask: create a roadmap with the `roadmap` skill (Recommended) / keep one plan.

**STOP** for review.

## 5. Write the explore doc

1. Write `plans/explore-YYYY-MM-DD-<slug>.md` in **explore's §5 format** (outside git), including its Start here block. Fill **Design decisions** with the approved mock file, its export, the mocks folder and every gate decision. The approved mock is the spec for `/implement` (`~/.agents/skills/implement/references/mock-to-code.md`).
2. When decisions remain open, build a [decision page](references/decision-page.md) beside the doc and open it in Lavish.
3. End with the ready-to-paste prompt, trimmed to what the doc does not already say:

```
/create-plan plans/explore-YYYY-MM-DD-<slug>.md
implement using <model-id> <effort> <chillin|vibin|supersoldiers>
```

Then print the roster guide (installed model IDs and efforts, the stance lines, the fallback note) per [explore](../explore/SKILL.md) §5 item 4. Carry a roster the user already named verbatim; never pre-fill a tier.

## Resumability

The mocks folder must survive a session limit with nothing lost (`~/AGENTS.md` → Resumable outputs). Rewrite the README's Start here at every gate: the goal, the gate reached, decisions so far, files to open, and the next action. A fresh session given only the README path continues the round. When the owner says the next step happens in a new session (or the round ends with the explore doc), run the `handoff` skill (pause mode) on the README and the explore doc before reporting.

## Guardrails

- Never touch product source; never write mocks into a git tree.
- Never generate images without an owner-approved model, effort and count; probe first.
- Never ask the owner to approve a filename; show the image or screenshot.
- Never run `lavish-axi share` or publish mocks.
- Never invent scope, facts, testimonials or prices; tag placeholders.
- Log every image prompt in `generation-prompts.md` and every asset's source and licence in `ASSET-LICENSES.md`.

## Origin

Merged 2026-10-09 from design-mocks, design-workflow.md, design-taste-frontend, minimalist-ui and industrial-brutalist-ui. Mock-to-code moved to `implement/references/mock-to-code.md`.
