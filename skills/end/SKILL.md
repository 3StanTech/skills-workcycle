---
name: end
description: Project-context auto-update (the \end protocol). Fold the current session's decisions, findings, and status changes into the owning project's master.md, then run any local extra close steps. Use when the user types /end or \end, or says "run the end protocol".
---

# `\end` — project context auto-update

Keep one consistent, up-to-date context file per project so every new chat starts aligned. Run only when the user requests the end protocol.

## 1. Resolve the project scope

Find the owning project: the nearest directory at-or-above the session's working files that contains a `master.md`. If `~/.agents/local/workcycle.md` exists, read it first: its projects root and project rules (for example a fixed target for one kind of work) win over this search. If no `master.md` exists for a genuine project yet, create one (sections: Overview · Key decisions · Current status · File index) with a sibling `CHANGELOG.md` when dated history is useful. Seed Overview and File index with a cheap survey, not a deep scan: `README*`, `CLAUDE.md`/`AGENTS.md`, the package manifest, the top-level listing (5–15 load-bearing paths), and `git log --oneline -10`. Never invent goals, clients or stack details the survey and session did not show. Keep process content outside Git or locally ignored; do not create a tracked process file. If the session spans multiple projects, run the fold once per project, each strictly scoped.

**Two files per project, since 2026-07-30:** `master.md` is **current state only**; session history lives in a sibling `CHANGELOG.md`. Read `master.md` always; read `CHANGELOG.md` only when you need history.

## 2. Fold the session into master.md

1. Read the existing `master.md` in full first.
2. Fold every new decision, research finding, prospect/entity, status change, and deliverable **from this session that belongs to this project** into the relevant sections.
3. Add a dated entry at the **top** of `CHANGELOG.md` (newest first) — not in `master.md`.
4. Update the "Last updated" date and affected current-status sections. Update an Active pipeline table only if the project has one and the session changed it.
5. Overwrite `master.md` in place — same filename, same location, **never a second copy, dated variant, or root-level copy**. Convert relative dates to absolute.
6. **Keep `master.md` current-state only.** If a section has started reading as narrative history ("overhauled July 14…", "took several passes…"), compress it to the decision or constraint that still holds and push the story to `CHANGELOG.md`. A body section should tell a new session what is true now, not how it got that way. This is the discipline that keeps the file from doubling in size while saying the same thing.
7. **Check disk before writing.** If the file names a folder, template, or path, confirm it still exists — deleted folders and superseded SOPs are the most common way `master.md` goes quietly wrong.
8. **Scope rule:** content from other projects and general account/skills maintenance stays out. Session handoffs and initiative roadmaps live in the project's outside-Git handoffs folder (`handoff` and `roadmap` skills), never in `master.md`; durable personal preferences require an explicit memory request. Do not edit Codex managed memories.
9. **Roadmaps.** Keep a `## Active roadmaps` pointer section in `master.md`: one line per initiative roadmap (`- <Initiative> (<Active | Closed date>, Phase <N>): <path to ROADMAP.md>`). When the session's work belongs to a roadmap, fold only what it marks as shipped, closed or decided since the last fold (phase outcomes with SHAs, decisions that still hold, carried follow-ups); never copy the roadmap into `master.md`. Step 4 runs the roadmap Update with the fold date so it prunes the folded session-log lines.

10. **Reminders.** Read `master.md` `## Reminders` (and the active roadmap's `## Deferred owner reminders`, if a roadmap governs the work). Any reminder whose `when:` is `next close`, a passed date, or an already-shown `next session` is due: list it in the report under **Reminders**, record `Reminded: <text>` in the CHANGELOG entry, and delete its line (`remind` skill, step 5).

11. **Closed audit files.** In `<handoffs-root>/audits/` (`<handoffs-root>` as in the `handoff` skill), move each `*.md` whose `Status: Closed` line is present and whose `## Open items` section is empty or says none into `<handoffs-root>/audits/archive/` (create it if missing; never delete; if a file of that name already exists there, append `-2`, `-3`, … before `.md` instead of overwriting). Leave every other file. List the moved paths in the report under **Archived audits**.

## 3. Local extra steps

If `~/.agents/local/workcycle.md` lists steps under `/end extra steps`, run them exactly as written (each says which projects it applies to). Skip this section when the file or the section is absent.

## 4. Close checks (no git operations)

1. **Roadmap.** When a roadmap governs the session's work, run the `roadmap` skill's Update step, passing the fold date.
2. **In-flight work.** If the session stopped mid-task and no resumable file captures it (a plan's Start here, the roadmap's Resume here, or a handoff), rewrite that plan's Start here, or write a handoff with the `handoff` skill. Follow `~/AGENTS.md` → Resumable outputs.
3. **Uncommitted files.** For each repo the session touched, report `N uncommitted files in <repo>` from `git status --short`. Never stage, commit or push.

## 5. Report

Reply with a short summary of exactly what changed since the last version — including anything found-but-not-fixed, listed as open items — then any due **Reminders** and **Archived audits**, the in-flight result (what captures unfinished work, or that none was in flight), and the `N uncommitted files in <repo>` lines.
