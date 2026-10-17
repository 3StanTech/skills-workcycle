---
name: work-audit
description: >-
  Audit that auto-fixes clear issues before commit, at Light depth (1 auditor,
  3 lenses) or Full depth (fleet, 7 lenses) chosen by a triage verdict; modes
  `report` and `fix <findings-file>`; /implement runs it as its final review, with
  the auditor and depth named or confirmed by the owner. Trigger: /work-audit, $work-audit, "audit our work", "check what
  we built", "work audit". Scopes: this session (default), a commit range, or a
  plan/roadmap's repos and live targets. Host-neutral (Codex and Grok have no
  built-in review). Use when something was built and needs a thorough check
  before committing. Not for diff-only bug hunting (in Claude Code use
  /code-review), code-quality cleanup (/simplify), or wiring-only QA
  (implement's wiring-check reference). Commits only on an explicit go in the
  request.
---

# Work-Audit

Fresh agents verify the work in scope, auto-fix the unambiguous, and leave a clean commit handoff.

**Decision points:** use the host's question tool with 2–4 pre-filled options (no "(Recommended)" label on tier options); otherwise print a numbered list and wait. Never proceed past a decision point on an assumption.


## Invocation

```
/work-audit [light|full] [report] [<scope>]
/work-audit fix <findings-file>
scope = session (default) | range <base>..<head> | plan <path> | roadmap <path>
```

Depth omitted: run triage and ask one depth question with its verdict as the recommended option (skipped when the request says "no questions"; the verdict is then used).

## Core philosophy

- **Fix now; never defer.** What is broken, contradictory, or off-plan gets fixed now, small stuff included.
- **No unsupervised irreversible harm.** Pause and ask only for (1) **irreversible destruction** (delete a file the work did not create; drop a DB column) and (2) **genuine ambiguity** (two valid fixes, wrong pick makes it worse).
- **Prove in reality.** Walk every realistic usage path and, where executable, **run the proof**.
- **Protect main context.** The main session orchestrates (brief, triage); agents read and fix.

## Scope modes

- `session` (default): what this session built or changed.
- `range <base>..<head>`: committed work. Ownership is `git diff --name-only <base>..<head>`; dirty files outside the range are not ours.
- `plan <path>` / `roadmap <path>`: the repos, commits and live targets the doc lists.

## Depth

| | Light | Full |
|---|---|---|
| Auditors | 1 | one repo: 3 (A plan fidelity + ripple; B correctness + sequence simulation + security lens; C cleanup + system fit). More repos: one per repo, all 7 lenses |
| Lenses | 2 Correctness, 3 Ripple, 5 Cleanup | all 7 |
| Proof | the project's mechanical checks (type-check, lint, tests, build) + one realistic usage path | every realistic path; live walk by the dispatcher |
| Fixes | unambiguous only; 1 re-check, no loop | up to 2 fix→re-verify loops (Phase 6) |

## Modes

- **`report`:** run Phases 0–4 and 7 only. The findings file stays `Status: Open` and gains `## Fix queue` (each unambiguous fix: file, locus, fix) plus `Recorded at: <repo>@<HEAD sha>` per repo (file mtimes for `--files` scopes).
- **`fix <findings-file>`:** read the file. If any repo HEAD or file changed since `Recorded at`, re-check that each queued finding still applies; drop and note those that do not. Then run Phases 5–7 on the queue and set Status as below.

## Findings file

`<handoffs-root>/audits/<YYYY-MM-DD>-<slug>.md` (`<handoffs-root>` as in `~/.agents/skills/handoff/SKILL.md`), outside git, written from Phase 1 onward and updated after each phase: brief (with the triage lines), findings (structured as in Phase 3), triage, fixes, checks, `## Open items` (questions and unfixed findings), and `Status: Open | Closed`. It is the resume point for a cut-off audit; `/handoff now` points at it. Set `Status: Closed` with open items "none" at the end of a clean run; `/end` archives closed files to `audits/archive/`.

**Light short form:** Brief (incl. triage lines), Findings, Fixes, Checks, Open items, Status.

## Flow (7 phases)

Phases 0, 1 and 4 run in the main session. The rest go to agents when available, else sequential passes.

### Phase 0 — Triage and roster (main session)

1. Run `python3 ~/.agents/skills/work-audit/scripts/triage.py` with the scope's repos and `--range`, `--worktree` or `--files` (non-git work: add `--base-dir <snapshot>` to count real diff lines; `--scope-kind plan|roadmap` when relevant; pass each client root listed under `work-audit client roots` in `~/.agents/local/workcycle.md` as `--client-root`, none when absent). Print its three lines verbatim in chat. The owner may override the verdict.
2. **Roster**, first hit wins: a tier named in the request, then the plan's Orchestration Reviewer column (the auditor), then a question to the owner whose "routing default" option is `python3 ~/.agents/skills/stance/scripts/route.py resolve --task-type review --host <host>` (read-only, lane A); the routing row is never a silent pick. Fixer: the plan's named implementer, else `route.py resolve --task-type standard`. Re-check: the auditor tier (any family). "Reviews" or "reviewer" in the request or plan means the auditor.
3. **Release authority:** from the request; default never commit. **Live targets:** those the plan lists; default none.
4. The auditor is always named or confirmed by the owner (request, plan Reviewer, or a question); a routing row alone never counts. Otherwise ask **only** for values still missing (`route.py` exit 3, or uncertain scope). When all are known, ask nothing. Anything the request states is not asked again.
5. **Plan-only turn:** read-only auditors (lane A) still run; fixes wait for a later typed `/work-audit`.

**Fallback:** if `route.py` or the helper route is unavailable, the main session runs the lenses as sequential read-only passes, then fixes, and the report says "sequential, no Orchestration".

### Phase 1 — Build the brief (main session)

A tight map for blank agents, in the findings file:

- What was built or changed, and in which scope mode?
- Which files were touched, **via edits AND via shell** (scripts, moves/deletes, generators)? In `range` mode, the range's file list; in `plan`/`roadmap` mode, the doc's repos, commits and live targets.
- Was there a plan? What did it require?
- Which systems does the work plausibly touch (docs, configs, indexes, sibling files)?

The **brief's file list is authoritative for ownership**.

### Phase 2 — Recon (1 agent or sequential pass)

Ground the brief in reality: diff on-disk state against it (`session`: `git status`, `git diff HEAD`; `range`: `git diff <base>..<head>`; `plan`/`roadmap`: each listed repo and commit) and classify every changed file as **ours / not-ours / uncertain**.

**Ownership rule (parallel sessions may share a tree):**

- Fix-eligible only if it **appears in the brief**. In `session` mode, known shared meta files (instruction file, docs, memory index, indexes) also qualify; in `range` and `plan`/`roadmap` modes they do not, and a file outside the scope qualifies only once the brief is expanded with evidence, otherwise it is a question.
- Everything else dirty is **not-ours** and untouched. **Uncertain** becomes a question, never a silent fix.
- Ownership is decided by **evidence**, not by how a file looks.

### Phase 3 — Audit (read-only)

Auditors per the depth table, each with its lenses. They read freely, follow ripples into connected files, simulate usage, and return **structured findings**. **None write.** Without subagents, run the lenses as sequential read-only passes.

`File · Line/locus · What is wrong · Evidenced by · Suggested fix · Clarity (unambiguous / destructive / ambiguous)`

**Live walk:** when the scope has live targets, the dispatcher runs the browser walks itself; helpers never do.

### Phase 4 — Triage (main session)

Deduplicate, discard false positives, sort into **unambiguous fixes** (fix pass), **the two pause cases** (questions to the human) and **non-issues**. An unambiguous fix that depends on an open question **waits**.

### Phase 5 — Fix pass

Fixes go to the named implementer as ordinary repairs (stance §6 ladder), **partitioned by file** (never two writers on one file). **Fix agents never touch git** (no `add`/`stash`/`commit`). Sequential: one file at a time under the same rule.

### Phase 6 — Re-verify

The re-check (auditor tier) confirms fixes hold and nothing new broke, **by execution** where possible (type-check, build, script, the sequence).

**Loop cap (Full): 2 fix→re-verify cycles** for re-breaks; if a fix keeps re-breaking, stop and ask. One extra cycle is allowed only for a confirmed **incomplete fix** found by the re-check, and the report says so. Light: one re-check, no loop; anything still failing goes to Open items.

**Release (explicit go only):** with "commit and push" (or equivalent) in the request, after a clean re-verify the dispatcher stages exactly the reported fix set, commits with no attribution, pushes, and runs `~/.agents/scripts/wait-ci-deploy.sh` in the foreground, reporting its result. Without a go: never commit.

### Phase 7 — Report

Short summary: scope, depth and verdict, what was audited, fixed, and waiting on the human, and the findings file path. The fixed list must be exactly the set the commit step picks up. End with "Clean — run the commit flow when ready", or with the release result when a go was given. In `report` mode, end with the Fix queue count and `/work-audit fix <findings-file>`.

**Coverage (required):** parallel or sequential; depth; lenses skipped; not-ours files left alone; loop cap hit or extra incomplete-fix cycle used. Never imply parallel coverage for a sequential run.

## The 7 audit lenses

1. **Plan fidelity** — was everything in the plan built? What is missing or drifted? (Full)
2. **Correctness & bugs** — broken logic, half-finished edits, wrong values, false claims.
3. **Ripple & contradictions** — did connected files (docs, instruction file, indexes, sibling configs) move with it? A stale reference elsewhere is a defect.
4. **Sequence simulation** — walk every realistic usage path end to end. (Full)
5. **Cleanup & clutter** — temp files, dead code, commented-out blocks, orphaned references, debug output.
6. **System fit & sustainability** — maintainable, or a fragile one-off hack? (Full)
7. **Security & production readiness (Full only)** — checklist in `references/security-lens.md`.

## Design guardrails (fixed)

- **Commits only on an explicit go**, by the dispatcher, after a clean re-verify. Audit and release stay separate jobs.
- **Anchored in the scope's work, ripples outward**; never fix the unrelated.
- **Fix everything except the two pause cases.**
- **Read-only auditors; file-partitioned writers.**
- **Biggest risk is the shared tree**: separate our work from foreign dirty files.
- **Ownership-from-brief is non-negotiable.**
- **No silent caps.** Sequential, partial or loop-capped coverage is reported.

## Workspace notes

- **Instruction file:** `CLAUDE.md`/`AGENTS.md`/`master.md`; the ripple lens checks the source of truth.
- **Commit handoff:** the workspace commit flow; never invent one.
- **Called by `/implement` §3** as its final review, at the depth the plan records or the owner picks after triage.
- **Cross-session (optional):** a second session may run the audit and report via SendMessage; the coordinator relays its questions.

## Guardrails

- **Never commit** without an explicit go; never stash or rewrite history.
- **Never fix not-ours or uncertain files** without a human decision.
- **Never auto-apply** irreversible destruction or ambiguous fixes.
- **No report file inside the repository**; the findings file lives outside git.
- **Never claim parallel coverage** for a sequential run.
- **Tiers:** from the request or the plan; the auditor is always named or confirmed by the owner (the routing `review` row is only the suggested option); never assumed.
