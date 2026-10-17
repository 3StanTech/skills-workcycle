# <Initiative> roadmap: <Project>

Status: Active
Last updated: <YYYY-MM-DD> (<what changed, one line>)
Project: `<repo path>` · State: `<master.md path>` · Suggest `/end` at: <e.g. after Phase 2 and after the final phase> (the owner's `/end` always folds)
Read this first in every session for this initiative. Update it last. It lives outside Git, is never committed, and holds no secrets.

## Resume here

1. **<Owner | Agent>:** <the next action>. <Approval needed, or "no approval needed">.
2. **<Owner | Agent>:** <the next action>.

In-flight handoff: none

## North star (do not drift)

- **Vision:** <one or two sentences>
- **Definition of done:**
  - <observable outcome>
  - <observable outcome>
- **Users:** <who, and who it is not for>
- **Phase order:** 1 <name> → 2 <name> → 3 <name>
- **Must have:** <component IDs or short names> · **Can wait:** <…>
- **Out of scope:** <…>

Full detail lives only in the sources. Open the section a phase touches, not the whole file:
- Explore doc: `plans/explore-<YYYY-MM-DD>-<slug>.md`
- <Approved mock or design, if any>: `<path>`

## Locked decisions (change only with the owner)

IDs are permanent: a new decision takes the next number; a replaced one stays, marked superseded. Plans cite them ("per D3"); commit messages never do, since the roadmap is private.

- **D1 Budget:** <money, quotas, rate limits> (<YYYY-MM-DD>)
- **D2 Models or providers:** <the defaults and fallbacks the product uses>
- **D3 UX:** <a decision from the approved mock; one ID per decision>
- **D4 Pushes, deploys and production writes:** <the rule, e.g. the owner's explicit go each time>
- **D5 `/end` milestones:** <when agents suggest a fold>

Asked every phase, never locked: implementer model, effort and stance; permission before creating test infrastructure (databases, branches, preview deploys).

## Guarantees every phase must preserve

- <invariant, security rule, style rule or platform limit>

## Phase status

| Phase | Status | Plan | Shipped on | Notes |
|---|---|---|---|---|
| 1 <name> | Not started | — | — | |
| 2 <name> | Not started | — | — | |

Status values: Not started · Planned · In progress · Shipped · Closed · Dropped. A phase is Shipped when its code is live and Closed when its live check passed and the follow-ups are carried below.

## Current phase: <N> <name>

| Commit | What |
|---|---|
| `<sha>` | <one line> |

- **Evidence:** <tests, benchmarks, live checks; paths to reports>
- **Open in this phase:** <what is left before it can close>

## Closed phases

<Each closed phase in 6 lines or fewer. Detail lives in its plan's Implementation Notes and, after `/end`, in CHANGELOG.md.>

## Follow-ups (carried)

- [ ] <follow-up> (from Phase <N>; owner or agent)

## Next phase readiness: Phase <N+1> <name> (facts, not a plan)

- **Scope (explore doc):** <components>
- **Current behaviour:** <what the code does today, with file paths>
- **Gaps:** <what is missing>
- **Approved approach:** <decided direction only>
- **Budget:** <cost per run, quota impact>
- **Owner decisions so far:** <dated>
- **Test material the owner must prepare:** <files, accounts, data>

## Environments (no secrets)

- **Production:** <URL, project and service IDs>
- **Test infrastructure:** <branch or database name and its expiry date>
- **Runners and harnesses:** <commands, with paths>
- **Owner-only secret files:** <paths only, never values>
- **Tool and permission quirks:** <what blocks the agent and the workaround>

## Deferred owner reminders

- <reminder> (raise when <trigger>)

## Session log (newest first; pruned after each `/end` fold)

- <YYYY-MM-DD> (<phase>, <plan | implement | live check | probe>): <one line>. <Pointers.>
