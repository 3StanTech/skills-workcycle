---
name: explore
description: >-
  Five-stage interactive discovery for a new feature, system, capability, or
  visual/UI direction; writes plans/explore-YYYY-MM-DD-<slug>.md. Trigger:
  /explore, $explore, "explore this idea", "let's discover". For durable,
  cross-session, cross-harness plan files (alongside Claude Code plan mode; is
  the plan mode in Codex/grok-build). Use when an idea still needs shaping
  before create-plan or implement. For UI, brand or image work, use
  explore-design.
---

# Explore

Interactive five-stage discovery that shapes an idea into a clear, well-scoped concept and writes an exploration doc.

## Purpose

Explore exists so the user and the agent **share one confirmed picture before anyone plans**:

1. **The goal:** what the user wants to be true afterwards, in their words.
2. **The problem:** what is wrong or missing today, for whom, and why it matters now.
3. **The finish line:** what "done" looks like, and what is deliberately out.
4. **The direction:** the chosen approach, with its trade-offs, costs, and risks known.

Explore succeeds when the user reads the restatement and says "yes, that's it", and when create-plan (or implement) can start from the doc without asking discovery questions again. Every stage serves one of those four. Drop any step that doesn't.

**Decision points:** If an interactive question tool (e.g. `AskUserQuestion`) is available, use it with 2–4 prefilled options, recommended option first and labeled "(Recommended)". Otherwise, print the same options as a numbered list in chat, state the recommended number, and wait for a reply. Never proceed past a decision point on an assumption.

**Explain before re-asking.** Some answers signal uncertainty: "correct me if I'm wrong", "not sure", "which is better?", or picking several conflicting options. For these, don't just re-ask. Give a short side-by-side table of the options: what each one is like in practice, its cost, and when it is the right choice. Then give a recommendation with the reason, and ask again.

**Read free text inside answers.** When the user types their own answer instead of picking an option, treat it as the real answer even if it contradicts the options. Act on what it says, including requests for clarification.

**Input:** The idea or arguments describing the feature, system, capability, or design change to explore.

**Tone:** Friendly and encouraging. Explain concepts in plain English. Celebrate progress. Break complexity down.

Do **not** run all stages autonomously. Present findings at each stage, ask decision-point questions, and wait for responses before proceeding. The only exception is an explicit opt-out in the request ("no questions", "just plan it"). Then compress the stages, write the doc, and list every assumption you made under Discovery Notes.

**Plan-only.** Explore never edits product source. It does not launch implementer delegates or build mocks. If the request names an implementer ("implement using <model> <effort> <supersoldiers|vibin|chillin>", "orchestrate to …"), record it verbatim under **Implementer roster** in the doc, so create-plan can build the Orchestration section. Naming an implementer does not start any work.

---

## 1. Discovery: understand the vision

**Goal:** Reach a restatement the user confirms.

0. **Visual idea?** If the idea is a visual design, UI, brand or image request, ask: switch to `/explore-design` (Recommended) / stay in explore. On switch, follow `~/.agents/skills/explore-design/SKILL.md` from its Stage 1.
1. Read the idea or arguments provided.
2. Read the workspace context relevant to it:
   - Project instruction files (`CLAUDE.md`, `master.md`, or equivalent) for structure and existing systems.
   - Context files those docs point at that relate to this idea.
   - Existing scripts, commands, skills, or tools that touch the same area.
3. **Thin brief?** If the request is a few words or names only a topic ("/explore the dashboard"), do the context sweep below before asking anything.
4. **Show the current state** when the idea changes something that already exists. Look at it the way a user would: run it, open it, or render it. Report measured facts rather than impressions (for UI, explore-design measures at phone and desktop width).
5. Summarize your understanding of the idea in 2–3 sentences.
6. Ask 2–4 clarifying questions. Use decision-point questions where options exist and free text in chat when the question is open-ended. Ask only what would change the direction:
   - What problem does this solve? (What is painful or slow right now?)
   - Who uses this, and when? (The user personally? Their clients' customers? A team? Something automatic?)
   - What does "done" look like?
   - What is explicitly out of scope?
7. **Restate.** After the answers, write the restatement (format below) and ask whether it matches. Options: "Matches", "Mostly, with corrections", "Off". If it isn't a clean match, revise it and ask again. Do not move to Stage 2 until the user confirms.

**STOP** and wait at step 6 and at step 7.

### Thin-brief context sweep

When the request carries little context, gather what the workspace already knows. That way, your questions offer real choices instead of blank prompts:

- `master.md` status for the project, any open roadmap or handoff, and due reminders.
- Recent work: git log and status, recently changed files, and the latest session or plan that touched the area.
- The thing itself: open, run, or render it.

Then make the first question **"Which of these is closest to what you're after?"**, with 2–3 concrete readings of the request drawn from the sweep. Follow with "What made you think of this now?" The trigger usually reveals the real problem. A wrong guess the user corrects beats a blank question they have to answer from scratch. Never act on a guess until it has been confirmed.

### Restatement format

```markdown
## Your goals
1. <goal in the user's terms; what should be true afterwards>
2. ...

## The problem you're solving
<One paragraph from the affected person's point of view: what happens today, what that costs them, why now.>

## Done looks like
- <observable outcome>

## Not doing
- <explicit exclusions>

## What I'm assuming
- <claim> (evidence: <file, measurement or source>) | (guess, to be confirmed)

## Inputs I still need
- <links, numbers, assets, or owner answers only the user can supply>
```

Keep it short enough to check at a glance. Mark every claim as **evidence** or **guess**. The guesses are where corrections come from.

**Drift check.** If a later answer changes a goal, the audience, or the finish line, update the restatement and show what changed. Don't just carry on.

---

## 2. Research: explore what is possible

**Goal:** Understand what exists, what is possible, and what constraints apply.

1. Search the workspace for relevant existing systems, commands, scripts, skills, or patterns. Earlier projects with the same shape are often the best precedent.
2. If the idea involves external tools or APIs:
   - Check whether the workspace already has credentials configured (`.env` or `.env.example`).
   - Research candidate services. Search the web via WebSearch or the harness's equivalent; if none is available, say so rather than guessing.
   - Note what is free and what is paid.
3. If the idea touches data, inspect the workspace database (if one exists) for the data available.
4. Present findings:
   - **What already exists** that is relevant (do not rebuild what is there).
   - **What options are available**, with pros and cons for each.
   - **Constraints or dependencies** found.
   - **Rough complexity:** Simple (an afternoon) / Medium (a focused session) / Large (multi-session).

**STOP** and wait for input on which direction to take before proceeding.

---

## 3. Shape: define the feature

**Goal:** Converge on a clear feature definition.

1. From discovery, research, and the user's input, define:
   - **What it does:** a plain-English description.
   - **How it works:** the step-by-step user flow or interaction model.
   - **What it produces:** outputs, artifacts, or changes.
   - **How it connects:** its relationship to existing workspace systems.
2. Tie each part to a confirmed goal. A part that serves no goal is scope creep: flag it or drop it.
3. If there are meaningful design choices, present 2–3 options with trade-offs and a clear recommendation (as a decision-point question).
4. Flag anything risky, complex, or uncertain honestly. That includes content the user's sources don't confirm, which belongs on an owner-question list rather than being invented.

**STOP** and wait for confirmation or adjustments before proceeding.

---

## 4. Scope: break it down

**Goal:** Turn the shaped concept into a scoped breakdown with a clear build path.

1. Break the feature into logical components or phases.
2. For each component, note:
   - What it involves (in plain terms).
   - Dependencies.
   - Rough effort: Small / Medium / Large.
3. If it's large, recommend phasing:
   - **Start here:** the minimum viable version.
   - **Then add:** the nice-to-haves.
   - **Later:** the full vision.
4. Separate core (must have) from extras (can wait).

**STOP** and present the breakdown for review.

---

## 5. Output: write the exploration doc

**Goal:** Capture everything in a structured document ready for `create-plan` or `implement`.

1. Compile and save to:

   `plans/explore-YYYY-MM-DD-<slug>.md`

   Use today's date and a short kebab-case slug.

   If the working directory is a git repository, write outputs to the project folder outside the git tree, or to the session scratchpad. Never commit AI-process artifacts.

2. Use this format:

```markdown
# Explore: {Feature Name}

**Created:** YYYY-MM-DD
**Status:** Explored
**Origin:** {One-line description of the original idea}

---

## Start here (cold start)

- **Goal and where this sits:** {the broader goal; initiative and phase if any}
- **Verified YYYY-MM-DD HH:MM:** {repo, branch, HEAD SHA, or "not a git repo"}
- **Read first:** {paths and why; "this doc only" when it carries everything}
- **Next:** {the `/create-plan` command; never `/implement`, since an explore doc is not a plan}

---

## Confirmed restatement

{The restatement the user confirmed, verbatim: goals, problem, done looks like, not doing}

## Vision

{2–3 sentences on what this is and why it matters}

## Proposed Solution

### What It Does
{Clear description in plain English}

### How It Works
{Step-by-step user flow or interaction model}

### What It Produces
{Outputs, artifacts, changes}

## Scope

### Minimum Viable Version
{Smallest useful version, to build first}

### Full Vision
{Complete version with all features}

### Components

| Component | Description | Effort | Dependencies |
|-----------|-------------|--------|--------------|
| {name}    | {what it does} | S / M / L | {what it needs} |

### Out of Scope
{What this explicitly does NOT include, yet}

## Technical Considerations

{APIs, credentials, external services, data changes, scheduling, cost estimates}

## Design decisions (explore-design only)

{Directions, chosen medium, approved mock file(s), mocks folder, gate decisions}

## Open questions for the owner

{Unconfirmed content or facts only the user or their client can answer, or "None"}

## Connections

{How this relates to other workspace systems}

## Implementer roster

{Verbatim implementer/tier/stance the user named, or "None named"}

## Next Steps

{Recommended path, plus the ready-to-paste prompt}

## Discovery Notes

{Key decisions, alternatives considered, user preferences, assumptions still standing}
```

   The doc must be cold-start ready (`~/AGENTS.md` → Resumable outputs). When the owner says the next step happens in a new session, run the `handoff` skill (pause mode) on the explore doc before reporting. With 4+ open decisions or a doc over ~15 KB, also build a decision page (`~/.agents/skills/explore-design/references/decision-page.md`).

3. Report the file path and recommend `/create-plan`, feeding this explore doc as context. That is the only next step: explore never recommends `/implement`, however well-defined the idea, because an explore doc is not a plan and implementing from it skips the plan the owner approves.

4. **Ready-to-paste prompt.** End with the exact next prompt in a code block, **trimmed to what the doc does not already say**:
   - Always: the command and the explore doc path, plus the output plan path if it matters.
   - Only if needed: which components or phases are in this round (when the doc lists more), decisions made after the doc was written, and any gate the user wants that the doc doesn't define.
   - A last line `implement using <model-id> <effort> <chillin|vibin|supersoldiers>` for the user to fill in, or the roster they already named, verbatim. Never pre-fill a tier: a filled value counts as the user naming it. It is the roster create-plan records in Orchestration, not a go to implement.
   - Directly under the code block, print a short **roster guide**: (a) the model IDs installed on this machine with their efforts, read from `~/.agents/skills/headless/data/claude-models.json`, `grok-models.json` (only if Grok is active in the routing table) and `codex debug models --bundled` (only if `codex` is installed), skipping families that are not installed; without the orchestration bundle (no headless catalogs) say "the session implements itself (Chillin)" instead; (b) one line per stance: chillin = the session works alone, vibin = up to 3 helpers, supersoldiers = one helper per independent task; (c) "Delete the last line to fall back to your routing table, or to be asked."
   - Never repeat constraints, links, headlines, or rules already recorded in the doc or the project's instruction files. The next agent reads those itself.

   Good: `/create-plan plans/explore-2026-09-29-bakery-redesign.md, production rebuild from mock-b.html only.` then, on its own line, `implement using <model-id> medium vibin` (shape only; the user fills the model).
   Too long: re-listing the doc's constraints, links, and component steps inside the prompt.

**Artifact chain:** explore or explore-design writes `plans/explore-YYYY-MM-DD-<slug>.md` → create-plan writes `plans/YYYY-MM-DD-<slug>.md` → implement reads the plan path. Implement never takes an explore doc.

---

## Guardrails

- **Interactive only:** never complete all stages autonomously. The best results come from the conversation.
- **Restatement before research:** don't research or shape until the restatement is confirmed.
- **Plain English:** no unexplained jargon.
- **Evidence over impression:** mark guesses as guesses, and measure what can be measured.
- **Honest about complexity:** do not underestimate effort.
- **Workspace-aware:** ground recommendations in what already exists; do not rebuild existing systems.
- **Not a plan:** this doc captures the "what" and "why". Detailed implementation steps belong in create-plan or implement.
- **Respect decisions:** once the user has chosen, move forward. Do not relitigate without a strong reason.
- **No git commits** of exploration artifacts into client-facing trees.
- **Never invent scope** the user did not confirm, or facts their sources do not support.
