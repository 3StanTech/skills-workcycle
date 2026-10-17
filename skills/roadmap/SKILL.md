---
name: roadmap
description: >-
  Create and maintain one living ROADMAP.md per multi-phase initiative so every
  session reads one file instead of re-scanning handoffs, plans and transcripts.
  Trigger: /roadmap, "start a roadmap", "update the roadmap", "resume the
  roadmap", "what's left", "close the roadmap", or explore/create-plan proposing
  2+ phases. Use for work with 2+ phases, each with its own plan. Not for
  single-phase or session-transfer work (use handoff).
---

# Roadmap

Keep one living document per multi-phase initiative that every session reads first and updates last, so it replaces per-session handoffs.

**Decision points:** If an interactive question tool (e.g. `AskUserQuestion`) is available, use it with 2–4 prefilled options, recommended option first and labeled "(Recommended)". Otherwise, print the same options as a numbered list in chat, state the recommended number, and wait for a reply. Never proceed past a decision point on an assumption.

**Terms.** An *initiative* is one body of work with a single explore doc and a definition of done. A *phase* is a slice of it that ships on its own: it gets its own plan (`create-plan`) and implementation, ends in a live check, and may take several sessions. A project can run several initiatives, so it can have several roadmaps. `master.md` stays the single project-wide state file and only points at roadmaps.

**Templates:** `references/template.md` (the roadmap). **Checker:** `scripts/doc_check.py`.

---

## 1. Resolve the roadmap

Find the roadmap in this order (first match wins):

1. A path the user gave.
2. The project `master.md` section `## Active roadmaps` (one line per roadmap).
3. `<handoffs-root>/roadmap-*/ROADMAP.md` whose header says `Status: Active`.

`<handoffs-root>` is the project's outside-Git process folder, the same one `handoff` and `prime` use:
- project is a git repo: `<project-parent>/<project-name>-handoffs/`
- project folder is not a git repo (it may contain one): `<project>/handoffs/`
- no project: the no-project handoffs folder in `~/.agents/local/workcycle.md`, else `~/.agents/handoffs/`

If several active roadmaps match and the user did not name one, ask a decision-point question. If none exists and the trigger was not "start a roadmap", say so and offer step 3.

## 2. Pick the mode

| Trigger | Mode |
|---|---|
| "start a roadmap", explore or a plan proposes 2+ phases | Create (step 3) |
| session start, "resume the roadmap", `prime` found one | Resume (step 4) |
| a work chunk ended, a plan was written, a phase shipped, the owner decided something | Update (step 5) |
| "what's left?", "status" | Status (step 6) |
| the final phase closed and its `/end` fold ran | Close (step 7) |
| "check the roadmap" | Run the checker only (step 5, item 7) |

**Bare `/roadmap` (no words after it) picks the mode itself.** Decide from the state, in this order, and say which mode you chose in one line:

1. No roadmap governs the work → offer **Create** if the work has 2 or more proposed phases; otherwise say a handoff fits better.
2. The roadmap is `Closed` → **Status** ("closed on <date>; nothing to resume").
3. Its final phase is Closed and the last `/end` fold is newer than that close → offer **Close**.
4. This session has not read the roadmap yet → **Resume**.
5. Work happened this session since the last update → **Update**, then a two-line **Status**.
6. Otherwise → **Status**.

Only the chained Update then Status runs two modes in one invocation. Create and Close always ask first.

**Suggest, never impose.** When an explore doc or plan proposes 2 or more phases and no roadmap exists, ask: create a roadmap (Recommended) / keep using handoffs. The owner confirms.

## 3. Create

1. **Read the sources once:** the explore doc, any approved mock or design, the first plan if one exists, and the newest handoff for this work.
2. **Ask one decision-point round** for anything the sources do not settle: the `/end` milestones (when agents should *suggest* a fold; recommend after the middle phase and after the final phase), the slug, and any locked decision that is still ambiguous.
3. **Create the folder** `<handoffs-root>/roadmap-<slug>/` with `ROADMAP.md`. Put the initiative's explore doc and phase plans in `plans/` there, implement run records in `runs/`, and mid-task handoffs in `handoffs/`. Owner-only secret files may sit beside them with mode 600.
4. **Fill the template, distilling instead of copying.** Copy only what defines the goal: vision, definition of done, users, phase order, must-have / can-wait, out of scope, and locked UX decisions as one line each. For everything else, write the path to the source and say which section to open when.
5. **Point to it from `master.md`.** Add one line under `## Active roadmaps` (create the section if missing): `- <Initiative> (Active, Phase <N>): <path to ROADMAP.md>`. This is the only `master.md` edit this skill makes; everything else waits for `/end`.
6. **Supersede the handoffs.** Add this first line to every older handoff for this work: `> **Superseded for resuming:** read <path to ROADMAP.md> first. Kept as history.`
7. **Check it:** step 5, item 7.

## 4. Resume (session start)

The roadmap is the whole reading budget. That is how this skill saves tokens.

1. **Read `ROADMAP.md` fully.** It is capped at 16 KB. Then read the `Interrupted` block, if any, of the doc Resume here points to and of any `In-flight handoff:`, and run its `Unverified (urgent stop)` steps before anything else (`handoff` §4).
2. **Do not open** older handoffs, `CHANGELOG.md`, closed plans, run logs or old transcripts unless Resume here or the current task points at one. Open a source doc (explore, mock) only at the section the current phase touches.
3. **Verify cheaply:** run `python3 ~/.agents/skills/roadmap/scripts/doc_check.py --text --repo <project repo> <ROADMAP.md>`, plus targeted checks for claims you will act on: test-branch expiry dates, deployed SHA, a running server. Never scan the codebase to rebuild context.
4. **Correct drift before acting.** If git or the checker contradicts the doc (for example HEAD is newer than Last updated, or a plan says Implemented while its row says In progress), fix the roadmap first and tell the owner in one line.
5. **Show due reminders** from Deferred owner reminders (dates passed, or `next session`).
6. **Open in `prime`'s agenda format:** at most six state lines (the current phase and its status, one line per drift fixed, one per due reminder, including due lines in `master.md` `## Reminders`), then a decision-point menu of 3 concrete next actions from Resume here, saying who acts and which approval each needs. `/prime` routes here when a roadmap is active, so both entry points open the same way.

## 5. Update (end of a work chunk)

Run this whenever a chunk of work ends, and always before the session ends. Do not wait for the owner to ask.

1. **Rewrite Resume here from scratch**, with 2 to 5 numbered actions. Never append to it. Set `In-flight handoff:` to `none`, or to a path (see the handoff note below).
2. **Bump `Last updated`** with today's date and one line on what changed.
3. **Record new owner decisions** in Locked decisions immediately, with the next free ID (`D<n>`) and the date. Never renumber. When a decision changes, keep the old line, append `(superseded by D<m>, <date>)`, and add the new one. A decision mentioned only in the session log will be lost.
4. **Update the phase.**
   - Plan written: set the row to Planned, add the plan path, and fold the plan's owner decisions into Locked decisions.
   - Work landed: add commits to the Current phase table and add evidence.
   - Phase shipped: set the row to Shipped. Show and then delete any `end of Phase <N>` reminders (`remind` skill). Once its live check passes, set it to Closed. Compact the phase into Closed phases (6 lines at most), move its leftovers to Follow-ups, **delete its readiness section**, and write readiness notes for the next phase.
5. **Add one session-log line at the top:** date, phase and mode, outcome, pointers.
6. **Stay within budget (16 KB).** If over: compact Closed phases further, and delete session-log lines already folded by `/end` (CHANGELOG.md now holds them).
7. **Run the checker**: `python3 ~/.agents/skills/roadmap/scripts/doc_check.py --text --repo <repo> <ROADMAP.md>`. Fix every ERROR. Fix each WARN or state why it stays.
8. **New session next?** Skip this step when the Update is already running inside `handoff`. Otherwise, when the owner says the next step happens in a new session, run the `handoff` skill (pause mode) instead of finishing here: it performs steps 1–7 itself, then pauses the doc Resume here points to and makes Resume here's first action the exact prompt to paste.

**Mid-task stop.** If the session ends in the middle of a task with detail that does not belong in the roadmap (a half-applied edit, a failing test being chased), write a handoff with the `handoff` skill into `roadmap-<slug>/handoffs/` and set `In-flight handoff:` to its path. When the stop is urgent (a limit about to hit), use `/handoff now`: its `Interrupted` block is the first write, and the Update waits for the resume session. The next Update consumes it: set the line back to `none` and mark the handoff superseded.

**Phase hand-offs to other skills:**
- **Planning a phase:** run `create-plan`, fed by this roadmap, the phase's readiness notes and the explore doc sections they name. The plan carries a `Carried from roadmap` section that cites the binding decisions by ID, and is saved in `roadmap-<slug>/plans/`. Ask for the implementer roster (model, effort, stance) and for test-infrastructure permission every phase, even when the previous phase's answer seems obvious.
- **Implementing:** `implement` reads Resume here, Locked decisions and Guarantees, then runs this Update at close.
- **Milestones:** the header's `/end` milestones say when an agent should **suggest** `/end` on its own. An `/end` the owner runs always folds, at any point. After any fold, prune the folded session-log lines and add "(folded into master.md <date>)" to the latest one.

## 6. Status ("what's left?")

Answer from the roadmap alone, in chat, in two parts:

- **(a) To finish the current phase:** the owner's tasks first (approvals, live checks, files to prepare), then the agent's.
- **(b) Before the next plan:** readiness gaps, owner decisions still open, test material to prepare, infrastructure expiring soon.

Add one line for any Deferred owner reminder whose trigger has arrived. Do not open other files unless the owner asks for detail.

## 7. Close

Run this after the final phase is Closed and its `/end` fold has run.

1. Replace the header's `Status:` line with `Status: Closed <date> · Final SHA <sha>` (never add a second Status line), and replace Resume here with `Initiative closed. Nothing to resume.` plus any Deferred owner reminders still open.
2. In `master.md`, change the roadmap's line under `## Active roadmaps` to `(Closed <date>)`. Remove it once the owner says it is no longer useful.
3. Keep the folder as history. Never delete it.

---

## Output

- Roadmap: `<handoffs-root>/roadmap-<slug>/ROADMAP.md`, with `plans/`, `runs/` and `handoffs/` beside it. One file per initiative, overwritten in place, never a dated copy.
- `master.md`: one pointer line under `## Active roadmaps`.
- Status mode: chat only, no file.

If the working directory is a git repository, write outputs to the project folder outside the git tree, or to the session scratchpad — never commit AI-process artifacts.

## Guardrails

- **Never store secrets.** Point to owner-only files by path. A checker ERROR blocks the write from counting as done.
- **Never commit or publish the roadmap,** and never put AI attribution in it or in anything it feeds.
- **Never append to Resume here,** and never let it disagree with the phase table.
- **Never change a Locked decision without the owner.** Supersede it with a new ID; never edit or renumber it in place.
- **Never copy whole source docs.** Distil the goal-defining parts; link the rest.
- **Never invent status.** Shipped means a SHA is live; Closed means its live check passed.
- **Never run `/end` on your own initiative** between milestones. The owner's `/end` always folds.
- **Never skip the per-phase questions:** the implementer roster, and permission before creating test infrastructure.
- **Never let an active doc pass 16 KB** without compacting it. A Closed doc is history; the checker stops enforcing size and compaction.
