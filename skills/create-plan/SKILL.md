---
name: create-plan
description: >-
  Write a detailed implementation plan before coding; saves
  plans/YYYY-MM-DD-<slug>.md. Trigger: /create-plan, $create-plan, "plan this",
  "write an implementation plan". For durable, cross-session, cross-harness plan
  files (alongside Claude Code plan mode; is the plan mode in Codex/grok-build).
  Use after explore or when the change is clear enough to plan; feeds implement.
---

# Create Plan

Create a detailed implementation plan that captures full context, rationale, and step-by-step tasks so a change can be executed without ambiguity.

**Decision points:** If an interactive question tool (e.g. `AskUserQuestion`) is available, use it with 2–4 prefilled options, recommended option first and labeled "(Recommended)". Otherwise, print the same options as a numbered list in chat, state the recommended number, and wait for a reply. Never proceed past a decision point on an assumption.

**Input:** The requirement to plan — a new command, workflow, structural change, template update, explore doc path, etc. If an explore doc exists at `plans/explore-YYYY-MM-DD-<slug>.md`, read it first and plan from it. An explore doc path is the resume point: start from its Start here and Read first, with no `/prime` or `/handoff`, and re-check its Verified line cheaply (HEAD, `git status --short`, the paths you will plan against); report any mismatch in one line and fold it into the plan's Current State.

You are writing a **plan**, not implementing. Research thoroughly, reason carefully, then write a comprehensive plan document.

**Same-message implementer roster does not waive this.** If the user writes `/create-plan … orchestrate to grok 4.6 medium supersoldiers`, `implement using <model> <effort> <supersoldiers|vibin|chillin>`, or otherwise names Codex/Grok/Claude, effort, or a stance in the same request, that clause names **who should implement later**. It is not permission to edit product source or launch a delegate in this turn. `<model> <effort> reviews` (or "reviewer") names the work-audit auditor and goes in the Reviewer column. Record it in the plan's **Orchestration** section, finish the plan, give the path, name `/implement <path>` as the next step, and stop. Implementation starts only on a later `/implement` (or an explicit "now implement" after the plan exists).

---

## 1. Research

Before writing the plan, investigate:

0. **Active roadmap first.** If this plan is a phase of an initiative with a living `ROADMAP.md` (the project `master.md` lists it under `## Active roadmaps`, or the user named it), read it before anything else: Resume here, North star, Locked decisions, Guarantees, and this phase's readiness notes. Open the explore doc, mock or other sources it links **only at the sections this phase touches**. Do not read superseded handoffs or closed plans for context the roadmap already distils.
1. **Core reference files:**
   - Project instruction files (`CLAUDE.md`, `master.md`, or equivalent) for workspace overview
   - Context files, memory index, or recent handoffs if they constrain the work
2. **Relevant areas:**
   - New commands/skills: read existing commands and skills for patterns
   - Output changes: explore `outputs/` structure and examples
   - Template updates: check `reference/` for existing patterns
   - Scripts: check `scripts/` for conventions
3. **Relationships:**
   - How does this change connect to existing workflows?
   - Which files reference or depend on areas being changed?
   - Naming conventions to follow?

---

## 2. Clarify — always, before writing

Ask **at least one round** of clarifying questions before writing the plan, even for a small or apparently obvious change. Use the host's question mechanism (decision-point questions where options exist; free text when open-ended). Ask what changes the plan: scope boundaries, acceptance criteria, trade-offs you would otherwise pick silently, constraints research could not settle, and — when a roster was named — any missing model/effort/speed or which tasks go to which named model.

**Verification scenarios:** propose 2–5 user-level scenarios (what runs, the medium-to-hard case, the artifact it leaves) and have the owner approve them in this round (`~/AGENTS.md` → Testing). They become the plan's Verification scenarios section.

Skip this step only when the request explicitly opts out ("no questions", "just plan it"). If more questions surface while writing, ask another round rather than inventing answers.

**Auditor, always:** in this round ask for the final-review auditor (model + effort, two questions, no "(Recommended)" label on a tier) and the audit depth (Light / Full / ask after triage), even when no implementer was named. Offer the tiers `python3 ~/.agents/skills/stance/scripts/route.py menu` lists, none preselected. Skip only what the request already names. Record both in Orchestration.

**Roadmap phase:** always ask, every phase, for the implementer roster (model, effort and stance, unless the request already named them) and for permission before creating test infrastructure (databases, branches, preview deploys), even when the previous phase's answer looks obvious. If a test environment recorded in the roadmap is still valid, offer it as the first option.

**More than one phase emerging:** if the plan turns out to need 2 or more phases that each need their own plan, and no roadmap exists, ask: create a roadmap with the `roadmap` skill (Recommended) / keep it as one plan.

---

## 3. Write the plan

Save to:

`plans/YYYY-MM-DD-<slug>.md`

- Use today's date
- Replace `<slug>` with a short kebab-case name (e.g. `add-guest-research-command`, `restructure-outputs`)

If the working directory is a git repository, write outputs to the project folder outside the git tree, or to the session scratchpad — never commit AI-process artifacts.

When a roadmap governs the work, save the plan in that roadmap's folder instead: `<handoffs-root>/roadmap-<slug>/plans/YYYY-MM-DD-<slug>.md`, and add the **Carried from roadmap** section shown in the format below (omit that section otherwise).

Fill every section of the format below. Replace all placeholders with specific, actionable content. Be thorough — implement will execute this plan and needs enough detail to proceed without ambiguity. Follow existing patterns; study similar files before proposing new structures.

### Plan format

```markdown
# Plan: <descriptive title>

**Created:** <YYYY-MM-DD>
**Status:** Draft
**Requirement:** <one-line summary of the requirement>

---

## Start here (cold start)

- **Goal and where this sits:** <the broader goal; initiative and phase if any>
- **Verified <YYYY-MM-DD HH:MM>:** <repo, branch, HEAD SHA, or "not a git repo"; any server, branch or DB the work reuses, with expiry>
- **Read first:** <paths and why; "this plan only" when it carries everything>
- **Next:** `/implement <this path>`
- No `/prime` or `/handoff` needed. cold-start pass <YYYY-MM-DD>

---

## Overview

### What this plan achieves

<2–3 sentences describing the end result and why it matters>

### Why this matters

<Connect this change to project goals. How does it create value?>

---

## Carried from roadmap

<Only when a roadmap governs this phase. Roadmap path, then the details implement must not lose:>
<- This phase's slice of the definition of done, plus its must-have / can-wait split>
<- Locked decisions (by ID, e.g. D3) and guarantees that bind this phase, one line each>
<- Readiness facts used: current behaviour, gaps, approved approach, budget, owner decisions>
<- Follow-ups carried from earlier phases that this plan takes on, or explicitly defers>

---

## Current State

### Relevant existing structure

<List of files, folders, or patterns that exist and relate to this change>

### Gaps or problems addressed

<What is missing, broken, or suboptimal that this plan fixes?>

---

## Proposed Changes

### Summary of changes

<High-level bullet list of all changes>

### New files to create

| File path | Purpose |
| --------- | ------- |
| `path/to/file.md` | Description of the file's role |

### Files to modify

| File path | Changes |
| --------- | ------- |
| `path/to/file.md` | Description of modifications |

### Files to delete (if any)

<List any files to remove and the reason>

---

## Design Decisions

### Key decisions made

1. **<Decision>**: <Rationale>
2. **<Decision>**: <Rationale>

### Decisions made in chat

- <YYYY-MM-DD: each owner decision from the question rounds or later chat, or "None">

### Alternatives considered

<Other approaches considered and why they were rejected>

### Open questions (if any)

<Index only: "Step N: <question>". Each open decision sits inside the step it changes (see the step template).>

---

## Step-by-Step Tasks

Execute these tasks during implementation in the order given.

### Step 1: <task title>

<Detailed description of what to do>

**Decision (open):** <only if this step has one: the question> — default: <recommended option>

**Actions:**

- <Specific action>
- <Specific action>

**Files affected:**

- `path/to/file.md`

---

### Step 2: <task title>

<Detailed description of what to do>

**Actions:**

- <Specific action>
- <Specific action>

**Files affected:**

- `path/to/file.md`

---

<Continue with as many steps as needed. Be thorough. Include:>
<- Creating new files (with full content specifications)>
<- Modifying existing files (with before/after or specific edits)>
<- Updating cross-references>
<- Test/validation steps>

---

## Orchestration

<If the user named no implementer: "Implementer: current session. Stance: <stated or Vibin>. Reviewer: <model> <effort> · Audit depth: <Light | Full | ask after triage>." and nothing else.>

<If the user named a roster ("implement using <model> <effort> <stance>", "orchestrate to …"), or tasks will be delegated, fill this section so /implement can run it without re-planning. Follow `~/.agents/skills/stance/SKILL.md` for stance defaults, routes and splitting. Each row's tier is the one the owner named (source `named`) or the approved roster's (source `roster`); a task with neither is asked in step 2 (offer `route.py menu`). Classify each task's type, then resolve each row with `python3 ~/.agents/skills/stance/scripts/route.py resolve --task-type <t> --host <host the implementer will run on> --named M:E` (owner-named tier) or `python3 ~/.agents/skills/stance/scripts/route.py resolve --task-type <t> --host <host the implementer will run on> --roster M:E` (roster tier) and copy its model, effort, speed, route and source. Escalation is "ask owner" (asked at the second failure, never pre-set); fallback is the owner's or none. Use concrete model IDs (never aliases; the subagent alias is derived at launch); speed is `standard` unless the user said fast. The planner may propose a cheaper tier for mechanical tasks; the user approves it with the plan.>

**Stance:** <supersoldiers | vibin | chillin> — **Integration owner:** <who merges parallel work> — **Final review:** <planner, or WarFleet reviewing Admiral>

| Wave | Task (step #) | Task type | Model ID | Effort | Speed | Route | Source | Lane | Owned files | Depends on | Allowed checks | Smoke test | Fallback | Escalation | Helper budget | Reviewer |
| ---- | ------------- | --------- | -------- | ------ | ----- | ----- | ------ | ---- | ----------- | ---------- | -------------- | ---------- | -------- | ---------- | ------------- | -------- |
| 1 | Step 1 | <mechanical/standard/hard/review/network> | <e.g. claude-sonnet-5-5> | <high> | standard | <subagent / native:codex / headless:claude / headless:codex / headless:grok> | <named/roster> | <A/B/C> | <paths> | — | <headless:claude lane B: permission rules passed as `--allow-tools`, e.g. `Bash(npx vitest run:*)`; otherwise —> | <command, or none> | <tier/route, or none> | ask owner | <helpers, or one-line reason for fewer than the stance default> | <auditor tier for implement's final work-audit; any family; "<model> <effort> reviews" in the request fills it> |

**Readiness** (checked at plan time; fix or ask before marking the plan Ready):
- [ ] `python3 ~/.agents/skills/stance/scripts/route.py validate` exits 0 (catalogs parse; every family in `families.json` is known)
- [ ] Every wave's context packet passes `python3 ~/.agents/skills/stance/scripts/packet-check.py <packet>`
- [ ] Network-dependent tasks have a smoke test and a fallback (`~/.agents/skills/stance/references/capabilities.md` §4)
- [ ] The needed wrappers are present; `claude --version` is recorded (fast-mode headless needs the catalog's `fast_min_cli`)

**Context packet per wave:** <for each wave, the shared brief from `~/.agents/skills/stance/templates/context-packet.md`: goal, task type, owned files, contracts, binding rules, smoke test, fallback, runnable acceptance, report footer>

Rules: tasks in one wave never share owned files; a task depends only on earlier waves; browser work stays with the dispatcher; the named implementer owns ordinary repairs (`~/.agents/skills/stance/SKILL.md`).

---

## Connections & Dependencies

### Files that reference this area

<List all files that link to or depend on changed areas>

### Updates needed for consistency

<List documentation, references, or related files that must be updated>

### Impact on existing workflows

<How this affects existing commands, outputs, or processes>

---

## Verification scenarios (owner-approved)

<The 2–5 scenarios the owner approved in step 2, run the way a user would (`~/AGENTS.md` → Testing):>

- [ ] <S1: what runs, the medium-to-hard case, and the artifact it leaves (screenshots, trace, script output)>
- [ ] <S2: …>

<Then mechanical checks:>

- [ ] <e.g. "Cross-references updated and valid", "Project docs reflect the new structure">

<Name automated tests only when they fall under the Testing rule's allowed cases.>

---

## Success Criteria

The implementation is complete when:

1. <Specific, measurable criterion>
2. <Specific, measurable criterion>
3. <Specific, measurable criterion>

---

## Notes

<Additional context, future considerations, or related ideas>
```

---

## 4. Report and next step

After writing the plan:

1. Deliver a short summary of what the plan covers
2. List any open questions that need user input before implementation
3. Give the full path: `plans/YYYY-MM-DD-<slug>.md`
4. Name the next step explicitly: run `/implement plans/YYYY-MM-DD-<slug>.md` (or pass that path as the implement argument)
5. If a roadmap governs the work, run the `roadmap` skill's Update step: set the phase row to Planned with the plan path, record the owner decisions from step 2 under Locked decisions, rewrite Resume here, and add a session-log line

6. **Run the cold-start gate** (`~/.agents/skills/handoff/references/cold-start-gate.md`) on the plan as the last write: Start here, chat decisions, scratchpad sweep, paths, the implement probes (repos' HEAD and status, `gh auth status` when the plan pushes, expiry of reused test infrastructure), `doc_check.py`, stamp. A new session then starts `/implement` from the paste line alone.

**Decision page:** with 4+ open decisions or a plan over ~15 KB, also build a Lavish decision page (`~/.agents/skills/explore-design/references/decision-page.md`); the Markdown plan stays the source of truth.

**Artifact chain:** explore or explore-design writes `plans/explore-YYYY-MM-DD-<slug>.md` → create-plan writes `plans/YYYY-MM-DD-<slug>.md` → implement reads the plan path.

If open questions block implementation, set status to `Draft` and stop after reporting them. If the plan is ready to execute, note that implement can proceed (status may stay `Draft` until implement starts, or use `Ready` if the user confirmed all decisions).

---

## Quality standards

- **Completeness:** Every section filled with specific content; no generic placeholders left
- **Actionability:** Steps detailed enough that implement can run them without follow-up questions
- **Consistency:** Follows existing workspace patterns and naming conventions
- **Clarity:** Someone unfamiliar with the project could understand and execute the plan
- **Traceability:** Changes are linked to goals and rationale

---

## Guardrails

- **Plan only** — do not implement changes while this skill is running. Do not launch Grok, Codex, or headless Claude. A same-message model/effort/stance clause is dispatch identity for the Orchestration section, not a start.
- **Always clarify** — never write the plan without at least one question round unless the user opted out.
- **No empty placeholders** — every section must have real content or an explicit "N/A" with reason.
- **Do not invent product requirements** the user did not state; ask decision-point questions instead.
- **Never commit** plan files into a client-facing git tree.
- **Do not hardcode model names** as stage requirements.
- **Prefer existing patterns** over novel structure.
