---
name: implement
description: >-
  Execute a clear, authorized implementation plan from any source; verify and
  report the result. Trigger: /implement, $implement, "implement the plan",
  "execute the plan".
---

# Implement

Execute a clear, authorized plan. It may be user-authored Markdown, a create-plan
artifact, or another unambiguous durable plan. Filename and provenance do not grant
authority.

**An explore doc is not a plan.** If the path is an explore or explore-design doc
(`explore-*.md`, or a doc whose Status is `Explored`), or the work came out of
explore and no create-plan plan exists for it yet, write nothing. Say "No plan
exists for this yet" and offer `/create-plan <path>` as the next step. Ad-hoc chat
requests that never went through explore are unaffected.

Read `~/.agents/skills/stance/SKILL.md` before source changes. Its stance
defaults, tier resolution, routes, ownership, verification, failure ladder, phase and
acceptance rules govern this workflow on every host. GPT/Grok or other headless helpers launch through
`~/.agents/skills/headless/SKILL.md`.

Without the Orchestration bundle (no `~/.agents/skills/stance`), implement runs
single-agent in this session: Chillin semantics, no helpers, no tier resolution. Skip every
Orchestration-only section.

**Decision points:** If an interactive question tool (e.g. `AskUserQuestion`) is available, use it with 2–4 prefilled options, recommended option first and labeled "(Recommended)". Otherwise, print the same options as a numbered list in chat, state the recommended number, and wait for a reply. Never proceed past a decision point on an assumption.

**Input:** Any clear plan or path supplied by the user.

---

## 1. Understand the plan

1. **Read the plan file fully.** Do not skim — understand every section. A plan path is
   the resume point: read the plan's Start here and Read first, and do not run `/prime`
   or a roadmap Resume. When the plan has a **Carried from roadmap** section, open the
   roadmap only at the sections it cites (Locked decisions, Guarantees). That is the
   context budget; do not re-read superseded handoffs or the full explore doc. Re-check
   the plan's Verified line cheaply (each repo's HEAD and `git status --short`, reused test
   infrastructure's expiry); report any mismatch in one line and fold it into the plan
   before work.
2. **Check prerequisites:**
   - Are there open questions that must be answered before continuing?
   - Are there dependencies on external resources or user decisions?
   - If blockers exist, stop and ask the user before proceeding.
3. **Confirm authorization:** the user's current request must authorize
   implementation. A `Draft`, `Ready`, or `Explored` label is not permission.
4. **Resolve ownership:** record any named implementer before source changes. If
   none is named and delegation is not otherwise authorized, the current model may
   implement locally.
5. **Resolve stance:** if none is stated, announce “No stance was specified, so
   I’ll use Vibin.” A stance does not select or launch a model.
6. **Honor the plan's Orchestration section.** If it carries a roster, that is the
   approved dispatch: run its waves in order with the exact model ID, effort,
   speed, route, lane and file ownership per task, and the stated stance and
   reviewer. Do not re-plan, re-split tasks, or change tiers. A roster value that is
   missing or no longer valid (e.g. a model absent from the route's catalog) is a
   blocker to ask about, never a substitution. The `/implement` request itself is
   the launch authorization for the listed tiers; a user-named implementer in the
   current request (e.g. `/implement <plan> using sonnet 5 high supersoldiers`)
   overrides the plan's roster — then split and route it per `stance` before wave 1.
7. **Resolve and launch.** Every delegated task's tier comes from the plan's Orchestration
   row or a tier the owner names in the request; a task with neither is asked (model + effort,
   that task only; offer the tiers `python3 ~/.agents/skills/stance/scripts/route.py menu` lists).
   Resolve its route with
   `python3 ~/.agents/skills/stance/scripts/route.py resolve --task-type <t> --host <this host> --named <M:E> | --roster <M:E>`
   (exit 3 means no tier was given: ask). Check each packet with
   `python3 ~/.agents/skills/stance/scripts/packet-check.py <packet>` before launch. Launch per the
   route (stance §3, §5): Claude Code `subagent` rows pass the resolved alias and effort on the call,
   with no pause between planning and wave 1; headless helpers launch in the background with stdin
   closed and `--allow-tools` from the roster; a helper with no session transcript after two
   minutes has stalled.

If the plan is incomplete or ambiguous, ask decision-point questions — never invent missing requirements.

### References (read only the ones the plan needs)

| Reference | Read when |
|---|---|
| `references/verification.md` | Always, at the verify step |
| `references/ui-build.md` | The plan touches a UI |
| `references/wiring-check.md` | Before calling a build of real size done |
| `references/mock-to-code.md` | The plan builds from an approved mock or image |

---

## 2. Execute by dependency

1. **Respect genuine dependencies and integration order.**
   - Independent reads, checks, and disjoint owned work may overlap
   - If a step creates a file, write the complete file — no stubs
   - If a step modifies a file, read the file first, then apply changes precisely
2. **For each task:**
   - Read all affected files
   - Make the specified changes
   - Verify the change is correct before continuing
3. **Handle problems gracefully:**
   - If a step cannot be executed as written, note the problem and adapt when the intent is clear
   - When uncertain, ask the user rather than guessing
   - Document deviations from the plan

Maintain the smallest adequate state record: `planned`, `executing`, `verifying`,
`repairing`, `final review`, `complete`, `partial`, or `blocked`. The named
implementer owns implementation and ordinary repairs. A planner may inspect,
coordinate, run non-mutating checks, and capture browser evidence but may not take
over because a launch failed or verification found a defect.

---

## 3. Verify, repair, and final review

1. Run each owner-approved **verification scenario** and attach its artifact
   (`references/verification.md`), then the plan's mechanical checks; note failures.
2. Review **success criteria** — confirm each is met; note gaps.
3. **After any push**, run `~/.agents/scripts/wait-ci-deploy.sh` in the foreground and
   report its result (CI runs and deploy statuses for the full SHA). `none-found` and
   `timeout` are reported as such, never as passing.
4. **Visual bug fixes:** measure before theorising (computed styles, matched CSS rules,
   scroll vs client size), apply the fix in the browser first (inject the CSS or DOM change),
   screenshot, then commit; screenshot again after deploy.
5. **Final review = work-audit** (outside WarFleet). After proof passes, run
   `~/.agents/skills/work-audit/scripts/triage.py` on this run's scope (record `git rev-parse HEAD` per repo
   before wave 1 as `<start>`; `--range <start>..HEAD` for commits made in this run, else
   `--worktree`; for non-git work `--files`, with `--base-dir <pre-edit snapshot>` when one exists; each client root listed under
   `work-audit client roots` in `~/.agents/local/workcycle.md` as `--client-root`) and print its
   verdict. **Depth:** use the plan's recorded audit depth; if it says "ask after triage" or records
   none, ask Light vs Full with the verdict as the recommended option. **Auditor** = the plan's
   Reviewer (any family); if the plan has none, ask for model + effort (two questions, no
   "(Recommended)" label on a tier). Never start an audit on a tier the owner did not name. With no recorded depth and a **FULL** verdict, the depth question is: *Run Full audit
   (Recommended)* / *Run Light instead* / *Skip for now*, with the triage reasons in it. Then run
   `/work-audit light <scope>` or `/work-audit full <scope>` for the depth recorded or chosen; on
   *Skip for now*, run no audit, report "audit skipped by the owner" and recommend
   `/work-audit full <scope>` as the next step. Audit findings return to the named implementer as ordinary repairs (stance §6
   ladder). Cross-reference and consistency checks (new files referenced, project docs updated,
   naming conventions) are the audit's ripple lens. In WarFleet the reviewing Admiral's final
   review applies instead.

**Delegated tasks** (stance §6): run the packet's acceptance commands yourself when a helper
reports `STATUS: done`; only a pass counts. A failed smoke test launches the row's fallback; a
first acceptance failure returns to the same helper with the failing output; a second asks the
owner for an escalation tier (any family, never pre-set); a failed escalation is `blocked`. The auditor (the plan's Reviewer) may be any family.

Failed checks return to the same implementer with precise evidence. Final review
starts only after the planned implementation and repair evidence is delivered. In
WarFleet the reviewing Admiral owns final-review edits; otherwise audit findings
return to the named implementer (step 5). Missing core deliverables return to implementation. Rerun checks
invalidated by audit fixes, and obtain renewed independent review after a material
rewrite. Offline fixtures do not verify live provider readiness.

---

**Outcome log.** At close (complete, partial or blocked), for every delegated task run
`route.py check-model` for Claude subagents, then `route.py log …`
(stance §7, `~/.agents/skills/stance/references/routes.md` → Outcome log). Each `log` row classifies
the outcome: `--first-pass yes|no` (yes only when the helper's own acceptance passes on the
dispatcher's first re-run), `--returned-by acceptance|seam|review|dispatcher-check|none`,
`--repaired-by original|fresh-helper|dispatcher|escalation` (with `--repairs-of <task>` on a
repair task's row) and `--host claude|codex|grok|hermes|pi|other`. Fix a wrong row with an
appended `route.py correct --plan P --task T [--date D] … --note "<evidence>"`; never edit the
log. Report the outcome lines written.

## 4. Update plan status

After implementation, update the plan file:

1. Use `**Status:** Implemented` only when every required deliverable and check is
   complete. Otherwise use `**Status:** Partial` or `**Status:** Blocked`, and rewrite
   the plan's Start here to the current state (verified-at, next action) so a fresh
   session resumes from the plan alone.
2. Append an "Implementation Notes" section at the end:

```markdown
---

## Implementation Notes

**Implemented:** <YYYY-MM-DD>

### Summary

<Short summary of what was done>

### Deviations from the plan

<List of any changes during implementation, or "None">

### Issues encountered

<List of any problems and how they were resolved, or "None">

### Validation and unverified criteria

<Evidence for completed checks and an explicit list of unavailable checks>
```

If the working directory is a git repository, write outputs to the project folder outside the git tree, or to the session scratchpad — never commit AI-process artifacts. Update the plan at its existing path (whether in-tree, outside the tree, or scratchpad).

**Roadmap:** when a roadmap governs the work, run the `roadmap` skill's Update step after
the plan status update, and again at each stop that leaves the phase unfinished (owner go
pending, quota exhausted, session ending). It records the phase status, commits,
evidence, carried follow-ups, next-phase readiness, Resume here and a session-log line.
Keep wave-by-wave run state in `roadmap-<slug>/runs/`, not in the roadmap.

**Cold-start gate:** rerun the gate (`~/.agents/skills/handoff/references/cold-start-gate.md`) on the plan at each wave
boundary and at any stop, so its Start here always names the next wave or step and a new
session resumes with `/implement <plan>` alone. A stop in the middle of a task, with detail
the plan should not hold, runs the `handoff` skill (pause mode); if the session must stop
now, run `/handoff now` (urgent mode).

---

## 5. Report and next step

Deliver:

1. **Summary:** bullets of completed work
2. **Changed files:** created, modified, deleted
3. **Validation results:** status of each checklist item
4. **Deviations:** any changes from the original plan
5. **Next steps:** follow-up actions if any

Format:

```markdown
## Implementation complete

### Summary
- <What was done>
- <What was done>

### Changed files
**Created:**
- `path/to/new-file.md`

**Modified:**
- `path/to/changed-file.md`

**Deleted:**
- (none)

### Validation
- [x] <Passed check>
- [x] <Passed check>

### Deviations from the plan
<None, or list deviations>

### Plan status
`plans/YYYY-MM-DD-<slug>.md` status updated to "Implemented"
```

**Next step (name explicitly):**
- If code or config was built → report the triage verdict, the audit result and the
  findings file path. If Full was recommended and skipped, recommend
  `/work-audit full <scope>`. The audit does not transfer ordinary repair ownership or
  justify repeating checks without evidence.
- Then recommend the workspace's commit flow when the user is ready — **do not commit unprompted**

---

## Quality standards

- **Thoroughness:** Every step in the plan is executed, not skipped
- **Precision:** Changes match what the plan specifies
- **Completeness:** Files are written fully, not as stubs
- **Consistency:** All cross-references and documentation updated
- **Traceability:** Deviations are documented

---

## Guardrails

- **Never skip dependencies** without documenting why and confirming with the user when material.
- **Never leave stubs** or placeholder implementations.
- **Never invent requirements** absent from the plan; ask decision-point questions.
- **Never commit** or run git write operations unless the user explicitly asks.
- **Never attribute** AI-process notes to commit messages, branch names, or PR bodies.
- **Do not hardcode model names** as stage requirements; use strongest/fast tiers only if delegation is needed, and in this workspace the tier for any delegated run comes from the request or the plan roster, otherwise it is asked per the user's global delegation rules — never assumed.
