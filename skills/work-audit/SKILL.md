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

- **Fix what matters now; file the rest.** Every finding gets a score, frequency × severity (each 1–10). A score of 5 or more is fixed now, small stuff included. Under 5 it is filed, not fixed, and the owner is told and may ask for the fix. Do not design for rare or future cases nobody asked about.
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
| Fixes | scored 5+; unambiguous only; 1 re-check; leftovers get one effort bump and a second re-check, then the owner is asked (Phase 6) | scored 5+; up to 2 fix→re-verify loops (Phase 6) |

## Modes

- **`report`:** run Phases 0–4 and 7 only. The findings file stays `Status: Open` and gains `## Fix queue` (each unambiguous fix: file, locus, fix) plus `Recorded at: <repo>@<HEAD sha>` per repo, with the content hash (`git hash-object <file>`) of each scoped file that differs from that commit (file mtimes for `--files` scopes).
- **`fix <findings-file>`:** read the file. If any repo HEAD or file changed since `Recorded at`, re-check that each queued finding still applies; drop and note those that do not. Then run Phases 5–7 on the queue and set Status as below.

## Findings file

`<handoffs-root>/audits/<YYYY-MM-DD>-<slug>.md` (`<handoffs-root>` as in `~/.agents/skills/handoff/SKILL.md`), outside git, written from Phase 1 onward and updated after each phase: a `## Start here` block (goal and scope, `Verified` with each repo's HEAD, Read first, Next = `/work-audit fix <this path>` or the commit flow, "No `/prime` or `/handoff` needed"), brief (with the triage lines), findings (structured as in Phase 3), triage, fixes, `## Re-check` (whenever fixes ran), checks, `## Filed, not fixed`, `## Open items` (questions and unfixed findings), and `Status: Open | Closed`. It is the resume point for a cut-off audit; `/handoff now` points at it. Set `Status: Closed` with open items "none" at the end of a clean run; `/end` archives closed files to `audits/archive/`. A run with leftovers (Phase 6) closes only when every Leftovers line is FIXED with `Verified by` different from `Fixed by`, or accepted open by the owner; `doc_check.py --kind findings` refuses a Closed file otherwise. Filed items are not leftovers (they never went through a fix): a file may be Closed with filed items once the owner has answered the Phase 7 question for each, or the request said "no questions".

`## Re-check` begins with `Judged at: <repo>@<sha>` per repo, plus each scoped file that differs from that commit, with its content hash (`git hash-object <file>`), in every git scope (`session`, `range`, `plan`, `roadmap`); file mtimes for `--files` scopes, as `Recorded at` does. Under it, copy the final re-check's verdict for every item it covered (each re-checked finding and each NEW item) into `### Verdicts`, then give every PARTIAL, NOT FIXED or NEW item a Leftovers line with the same id:

```markdown
### Verdicts
- <finding id> · <FIXED | PARTIAL | NOT FIXED | NEW>

### Leftovers
- <finding id> · <PARTIAL | NOT FIXED | NEW> · Fixed by: <fixer's tier, e.g. `claude-opus-5-5 high (bump)`> · Verified by: <the auditor's or an owner-named reviewer's tier, or "none"> · <FIXED | Open | Accepted open by owner YYYY-MM-DD>
```

Under `## Filed, not fixed`, one line per filed finding (`· Pre-existing` after the score when its Origin is pre-existing):

```markdown
- <finding id> · F×S=N · <what> · <Filed | Fix requested by owner YYYY-MM-DD | Accepted by owner YYYY-MM-DD>
```

**Light short form:** Start here, Brief (incl. triage lines), Findings, Fixes, Re-check (`Judged at`, Verdicts, Leftovers), Checks, Filed, not fixed, Open items, Status.

**Last write:** run the cold-start gate (`~/.agents/skills/handoff/references/cold-start-gate.md`) on the findings file at the end of Phase 7, and whenever an audit stops early; a Closed file needs only the doc check.

## Flow (7 phases)

Phases 0, 1 and 4 run in the main session. The rest go to agents when available, else sequential passes.

### Phase 0 — Triage and roster (main session)

1. Run `python3 ~/.agents/skills/work-audit/scripts/triage.py` with the scope's repos and `--range`, `--worktree` or `--files` (non-git work: add `--base-dir <snapshot>` to count real diff lines; `--scope-kind plan|roadmap` when relevant; pass each client root listed under `work-audit client roots` in `~/.agents/local/workcycle.md` as `--client-root`, none when absent). Print its three lines verbatim in chat. The owner may override the verdict.
2. **Roster**, first hit wins: a tier named in the request, then the plan's Orchestration Reviewer column (the auditor), then a question to the owner (model + effort, offering the tiers `python3 ~/.agents/skills/stance/scripts/route.py menu` lists, none preselected; read-only, lane A). Fixer: the plan's named implementer, else asked. Re-check: the auditor tier (any family). "Reviews" or "reviewer" in the request or plan means the auditor.
3. **Release authority:** from the request; default never commit. **Live targets:** those the plan lists; default none.
4. The auditor is always named by the owner (request, plan Reviewer, or a question). Otherwise ask **only** for values still missing (a tier nobody named, or uncertain scope). When all are known, ask nothing. Anything the request states is not asked again.
5. **Plan-only turn:** read-only auditors (lane A) still run; fixes wait for a later typed `/work-audit`.

**Fallback:** if `route.py` or the helper route is unavailable, the main session runs the lenses as sequential read-only passes, then fixes, and the report says "sequential, no Orchestration".

### Phase 1 — Build the brief (main session)

A tight map for blank agents, in the findings file:

- What was built or changed, and in which scope mode?
- Which files were touched, **via edits AND via shell** (scripts, moves/deletes, generators)? In `range` mode, the range's file list; in `plan`/`roadmap` mode, the doc's repos, commits and live targets.
- Was there a plan? What did it require?
- Which systems does the work plausibly touch (docs, configs, indexes, sibling files)?
- When the local settings file (`~/.agents/local/workcycle.md`) has a `work-audit incident checklist` section, read the file it names and copy into the brief only the items whose trigger matches the diff or file list. No section: skip, and Coverage says "no incident checklist".

The **brief's file list is authoritative for ownership**.

### Phase 2 — Recon (1 agent or sequential pass)

Ground the brief in reality: diff on-disk state against it (`session`: `git status`, `git diff HEAD`; `range`: `git diff <base>..<head>`; `plan`/`roadmap`: each listed repo and commit) and classify every changed file as **ours / not-ours / uncertain**.

**Ownership rule (parallel sessions may share a tree):**

- Fix-eligible only if it **appears in the brief**. In `session` mode, known shared meta files (instruction file, docs, memory index, indexes) also qualify; in `range` and `plan`/`roadmap` modes they do not, and a file outside the scope qualifies only once the brief is expanded with evidence, otherwise it is a question.
- Everything else dirty is **not-ours** and untouched. **Uncertain** becomes a question, never a silent fix.
- Ownership is decided by **evidence**, not by how a file looks.

**Judge files.** Recon also marks every changed file that judges this work (tests, CI workflows, hooks, lint and type configs, checker scripts, the audit's own rule files) and says for each whether the plan or request asked for the change.

- Asked for: one line in the brief, and Coverage names it.
- Not asked for and weaker than before (an assertion deleted or loosened, a test skipped, a threshold raised, a hook or CI job disabled): a finding with Clarity `ambiguous`, so it is a pause case.
- Where a rule file changed without being asked for, the auditor judges by its base version (`git show <base>:<path>`).

### Phase 3 — Audit (read-only)

Auditors per the depth table, each with its lenses. They read freely, follow ripples into connected files, simulate usage, and return **structured findings**. **None write.** Without subagents, run the lenses as sequential read-only passes.

`File · Line/locus · What is wrong · Evidenced by · Suggested fix · Clarity (unambiguous / destructive / ambiguous) · Score (F×S=N, one-line reason) · Origin (ours / pre-existing, with the evidence)`

- **Frequency** (1–10): how often a real user or run meets it; 1 = needs a contrived input, 10 = every use.
- **Severity** (1–10): how bad when it happens; 1 = cosmetic, 10 = data loss, security or a blocked user.
- **Origin:** `pre-existing` only on evidence that the defect is already in the scope's base (`git show <base>:<file>`, or the file's state before the session) and the work neither caused nor worsened it. A stale reference the change created is `ours`.

When the brief lists incident checklist items, the auditor returns one line per item (`<id> · holds | broken · <evidence>`); a broken item is a finding like any other.

**Live walk:** when the scope has live targets, the dispatcher runs the browser walks itself; helpers never do.

### Phase 4 — Triage (main session)

Deduplicate, discard false positives, and confirm or correct each proposed score. Then sort into **unambiguous fixes scoring 5+** (fix pass), **the two pause cases** (questions to the human), **filed** (under 5, written to `## Filed, not fixed`) and **non-issues**. A filed finding whose fix another finding depends on is fixed with it, and the report says why. A pre-existing one waits for the owner's answer to it (Phase 4 for a security finding, else Phase 7), and so does the finding that depends on it: chosen, the two run Phases 5–6 together; not chosen (declined, or "no questions"), the dependent goes to `## Open items` as blocked by it, and the report says so. An unambiguous fix that depends on an open question **waits**.

A **pre-existing** finding is filed whatever its score, with `· Pre-existing` after the score; a pre-existing **security** finding becomes an owner question now, not in Phase 7: chosen, it joins this cycle's fix pass (in `report` mode, `## Fix queue`) and its line reads `Fix requested by owner YYYY-MM-DD`; declined, `Accepted by owner YYYY-MM-DD`; under "no questions" it stays `Filed`, listed first in the report and in `## Open items`.

Review the threshold after three audits: if nothing was filed, or the owner asked to fix most filed items, say so in the report.

### Phase 5 — Fix pass

Fixes go to the named implementer as ordinary repairs (stance §6 ladder), **partitioned by file** (never two writers on one file). **Fix agents never touch git** (no `add`/`stash`/`commit`). Sequential: one file at a time under the same rule. Pre-existing findings go to the fixer only when the owner chose them (the Phase 4 security question or the Phase 7 question), together with any finding that waited on them; they keep their Origin and are not logged against the fixer.

### Phase 6 — Re-verify

The re-check (auditor tier) confirms fixes hold and nothing new broke, **by execution** where possible (type-check, build, script, the sequence). Every re-check after the first audit gets a brief that carries each earlier report, the class sweep and the sibling list. It probes the fixed loci and the listed siblings first, then whatever the fixes changed; it does not rerun every lens from scratch. A second re-check also gets the first re-check's verdicts. The Full loop uses the same brief.

**Loop cap (Full): 2 fix→re-verify cycles** for re-breaks; if a fix keeps re-breaking, stop and ask. One extra cycle is allowed only for a confirmed **incomplete fix** found by the re-check, and the report says so. The class sweep and the effort bump below apply to Full's second cycle too. When Full hits the cap with items still failing, they are leftovers under the Light rule below.

**Light: one re-check, then one bumped fix and a second re-check.** Anything the re-check marks PARTIAL, NOT FIXED or NEW is a **leftover**: it goes to `## Open items` and the Verdicts and Leftovers blocks, and the file stays `Status: Open`.

- The fixer may prepare, apply and (with a release go) commit a fix for a leftover. That is implementation evidence, **never audit verification**: the fixer's own probes, suite runs or reading of the diff do not close a leftover.
- A leftover closes only when the auditor, or another reviewer the owner names, verifies it, or when the owner accepts it as open. The fixer's own checks never close a leftover.
- **Class sweep (before any second fix, Light or Full, bump or not).** For each leftover the fixer first writes, in the findings file's Fixes section: whether it is an instance or a design flaw; the failure class in one line; every sibling it can name (other input forms, orderings, repeats, negations, empty cases). It fixes all of them in one pass and lists them for the auditor to probe. A design flaw is reported to the owner before any fix.
- **Effort bump (once per audit).** Trigger: the first re-check marks any item PARTIAL, NOT FIXED, or NEW caused by a fix. A coverage gap alone is not a trigger: rerun the engine. Action: the leftover fixes run one effort level higher on the same model (the next entry after the fixer's current effort in that model's list from `route.py menu`). The owner gets one line, not a question: "Re-check 1 left N items; fixing at <model> <effort+1>". Then the auditor re-checks again.
  - Delegated fixer: relaunch that fixer's task at the raised effort with the leftovers, the class sweep and both reports.
  - Session fixer (Chillin): hand the leftovers to one helper, same model, one level up, with a context packet (stance templates). The session stays integration owner, applies nothing itself to the leftover files while the helper owns them, and re-runs acceptance.
  - Log it at close: `route.py log … --repaired-by fresh-helper --note "effort-bump <from>→<to>"`.
- **When the bump does not apply, ask the owner** (redesign / escalate to Full / a tier they name / accept as open): the fixer is already at the model's top level; the second re-check also leaves items; or `route.py` is unavailable. There is no second automatic bump. When the same file or function produced leftovers twice, recommend "stop and redesign" and say why. A standing go to commit and push covers releasing verified work, not deciding what counts as verified.

**Stale verdicts.** Before Release and before Closed, compare the current state with `Judged at` (repo SHAs, which scoped files differ from them, and each one's content hash), in every scope. A scoped file that changed since then (edited again, newly dirty, or committed) has a stale verdict: re-check that file only, with the history brief, before releasing or closing.

**Engine coverage:** when the audited work has owner-approved scenarios, the re-check lists each code path the fixes changed against the scenario engines that cover it, and states which were rerun after the fix. A covered path with an engine not rerun is a NEW finding ("coverage gap"), so it is a leftover.

**Release (explicit go only):** with "commit and push" (or equivalent) in the request, after a clean re-verify and after every owner question that can add to the fix set is settled (Phase 4 pause cases and the pre-existing security question, the Phase 7 filed-item question), with any re-check their chosen fixes started clean, the dispatcher stages exactly the reported fix set, commits with no attribution, pushes, and runs `~/.agents/scripts/wait-ci-deploy.sh` in the foreground, reporting its result. With no such question (no filed items, or "no questions") or none chosen, nothing more is waited for: the release follows the clean re-verify. `report` mode never releases. Without a go: never commit.

### Phase 7 — Report

Short summary: scope, depth and verdict, what was audited, fixed, and waiting on the human, and the findings file path. The fixed list must be exactly the set the commit step picks up. End with "Clean — run the commit flow when ready", or with the release result when a go was given. In `report` mode, end with the Fix queue count and `/work-audit fix <findings-file>`.

**Filed items:** list them with their scores; items already answered in Phase 4 are listed with that answer, not asked again. When any others exist, ask the owner one multi-select question: which to fix (none preselected; pre-existing items scoring 5 or more listed first). Chosen items, with any finding that waited on them (Phase 4), run Phases 5–6 (in `report` mode they join `## Fix queue` and run only under `/work-audit fix`) and their lines read `Fix requested by owner YYYY-MM-DD`; the rest read `Accepted by owner YYYY-MM-DD`. Under "no questions" they stay `Filed` and the report says so.

**Coverage (required):** parallel or sequential; depth; lenses skipped; not-ours files left alone; loop cap hit or extra incomplete-fix cycle used; effort bump used (from → to); leftovers and who verified each; filed count; judge files changed; checklist items matched (ids), or "no incident checklist". Never imply parallel coverage for a sequential run.

## The 7 audit lenses

1. **Plan fidelity** — was everything in the plan built? What is missing or drifted? (Full)
2. **Correctness & bugs** — broken logic, half-finished edits, wrong values, false claims.
3. **Ripple & contradictions** — did connected files (docs, instruction file, indexes, sibling configs) move with it? A stale reference elsewhere is a defect.
4. **Sequence simulation** — walk every realistic usage path end to end. For UI or stateful work, first list the implicit states and transitions ([usability → hidden states](../implement/references/ui-build/usability.md#feedback--system-status)) and walk each. (Full)
5. **Cleanup & clutter** — temp files, dead code, commented-out blocks, orphaned references, debug output.
6. **System fit & sustainability** — maintainable, or a fragile one-off hack? (Full)
7. **Security & production readiness (Full only)** — checklist in `references/security-lens.md`.

When the scope touches UI motion, lens 2 also applies `animation-performance` and `review-animations` per the [motion skill map](../implement/references/ui-build/motion.md#skill-map); if they are not installed, it applies the house rules there and says so.

## Design guardrails (fixed)

- **Commits only on an explicit go**, by the dispatcher, after a clean re-verify. Audit and release stay separate jobs.
- **Anchored in the scope's work, ripples outward**; never fix the unrelated; a defect that was there before the work is filed as pre-existing.
- **Fix everything scoring 5 or more except the two pause cases; file the rest and tell the owner.**
- **A change does not edit its own judge unasked.**
- **Read-only auditors; file-partitioned writers.**
- **Biggest risk is the shared tree**: separate our work from foreign dirty files.
- **Ownership-from-brief is non-negotiable.**
- **No silent caps.** Sequential, partial or loop-capped coverage is reported.

## Workspace notes

- **Instruction file:** `CLAUDE.md`/`AGENTS.md`/`master.md`; the ripple lens checks the source of truth.
- **Commit handoff:** the workspace commit flow; never invent one.
- **Called by `/implement` §3** as its final review, at the depth the plan records or the owner picks after triage.
- **Cross-session (optional):** a second session may run the audit and report via SendMessage; the coordinator relays its questions.
- **Incident checklist (optional, local).** A short file of past misses, named in the local settings file's `work-audit incident checklist` section (Phase 1). Item format: `- <id> · Trigger: <what in a diff sets it off: a path pattern or a kind of change> · Check: <one sentence> · Source: <where it came from>`. An item is added when the same miss has happened twice or the owner asks, and only if a diff can show its trigger. Delete an item once a script or hook enforces it. Review the list with the score threshold.

## Guardrails

- **Never commit** without an explicit go; never stash or rewrite history.
- **Never fix not-ours or uncertain files** without a human decision.
- **Never auto-apply** irreversible destruction or ambiguous fixes.
- **No report file inside the repository**; the findings file lives outside git.
- **Never claim parallel coverage** for a sequential run.
- **Tiers:** from the request or the plan, else asked; the auditor is always named by the owner; never assumed.
