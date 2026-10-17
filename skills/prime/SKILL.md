---
name: prime
description: >-
  Start a session warm: load only the project state not already in context
  (master.md, the active roadmap or newest open handoff, due reminders, git state),
  then print at most 6 lines and a 3-option pick-up menu. Read-only. Trigger:
  /prime, "good morning", "session start", "where were we", "pick up where we left
  off". Use at session start, never mid-work.
---

# Prime

Open a session with what is open and true right now, in six lines and three options, without re-deriving context.

> **Decision points:** If an interactive question tool (e.g. `AskUserQuestion`) is
> available, use it with 2–4 prefilled options, recommended option first and labeled
> "(Recommended)". Otherwise, print the same options as a numbered list in chat, state
> the recommended number, and wait for a reply. Never proceed past a decision point on
> an assumption.

## 1. Resolve the project

First match wins: the project the user named → the session's cwd (nearest folder with
`master.md` or `.git`) → ask a decision-point question listing the folders under
`~/Workspace/Projects/`. Never open with another project's agenda because its handoff is newer.

## 2. Find urgent stops first (every branch)

Before routing anywhere, run `grep -rlE '^#{2,6} Interrupted' <handoffs-root>` (handoffs,
plans, explore docs, mocks READMEs, roadmap folders; `handoff` skill for the path). Surface
any hit first, before the roadmap agenda or any other thread, and name its
`Unverified (urgent stop)` steps.

## 2b. Route to the roadmap when one governs the work

If the project's `master.md` lists an active roadmap under `## Active roadmaps` (or the
SessionStart hook named one) and the user's opening words don't point at other work:
**run the `roadmap` skill's Resume step and stop here.** Do not read `master.md` further,
or `CHANGELOG.md`, handoffs or memory files. The roadmap is the whole budget, and its
Resume step prints the same agenda format as step 4. With several active roadmaps, ask
which one (decision point).

## 3. Load only what is not already in context

**Skip anything the host already injected.** Claude Code loads `CLAUDE.md`/`AGENTS.md`
and the `MEMORY.md` index at start; the SessionStart hook may already show the active
roadmap's Resume here and the newest open handoff path. Do not read those again.

Then read, silently, in this order:

| Source | How much |
|---|---|
| Project `master.md` | all (current state only); note any `## Reminders` and `## Active roadmaps` |
| Newest open handoff | `<handoffs-root>/YYYY-MM-DD-<slug>.md`, skipping files marked Superseded or `Status: Done` (`handoff` skill for paths) || `CHANGELOG.md` | newest entry only, and only when there is neither a roadmap nor a handoff |
| Memory files | only the 0–3 entries in the index that clearly bear on the opening task |
| Git | `git status --short`, `git branch --show-current`, `git log --oneline -5` |

Never scan the codebase. If `master.md` is missing, say so in one line and offer `/end`
at session close to create it.

## 4. Print the agenda

At most six state lines, then three options:

- one line per genuinely open thread (from Resume here, the handoff's Next actions, or
  master.md Current status), as keywords rather than sentences
- one line if git disagrees with the docs (uncommitted work, an unexpected branch, a HEAD
  newer than the doc's Last updated)
- one line per **due reminder**: a `when:` of "next session" or a date that has passed
  (`remind` skill)
- one line if a decision is waiting on the user

```
<state lines>

Pick up:
1. <a concrete action that can start now>
2. <…>
3. <…>
```

Present the menu as a decision-point question. Options are concrete ("rerun the failing
Neon suite on br-long-sea"), never categories ("continue backend").

## Output

Chat only: six state lines at most plus the menu. No list of loaded files, no pasted git
output, no file written.

## Guardrails

- **Read-only.** Never write files, memory or commits. Writing belongs to `/end`,
  `roadmap`, `handoff` and `remind`.
- **Never re-read what the host already loaded,** and never scan the codebase.
- **Never invent an open thread.** Thin docs mean a thin agenda.
- **Never pull, fetch, checkout or stash.**
- **Never print secrets** that slipped into a doc. Skip that line.
- **Stay in the resolved project.**
