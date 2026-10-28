# Personal rules

Copy this file to `~/AGENTS.md` and edit it. Every skill in this bundle defers to it. Codex reads
it through `~/.codex/AGENTS.md`; Claude Code through a line `@~/AGENTS.md` in `~/.claude/CLAUDE.md`.
Keep it short: skills hold the procedures, this file holds only your preferences.

## Working style

- Prefer one simple, robust implementation and focused changes; fix root causes.
- Ask only questions that change the work. Distinguish evidence from assumptions.
- (Optional) How to address me: <name or title>.

## Context and completion

- Each project keeps its current state in `master.md` (written by `/end`); plans, handoffs and
  roadmaps live outside Git.
- Every stage doc (explore doc, plan, roadmap, audit findings) passes the cold-start gate when
  written, so a new session continues from its paste line alone. `handoff` is for mid-task
  pauses and urgent stops.
- Do not call partial or unverified work complete; list what was not verified.

## Publication and consequential actions

- Commits, pushes, deployments, production writes and credential changes need my explicit go.
- (Optional) Keep assisted-authorship marks out of commits, branches and PRs.
- Keep plans, handoffs and run reports out of Git working trees.

## Delegation (only if you installed skills-orchestration)

- I name helpers as `implement using <model-id> <effort> <chillin|vibin|supersoldiers>`.
  When I name nothing, ask me. Never pick a model for me.
- Always ask me for the auditor (model and effort) that reviews finished work.
- After a second failed attempt, ask me for the escalation tier. Launch, auth or tier failures
  never switch to another model family without asking.

## Testing

- Prove a change the way a user would (browser, CLI or API on test data) and leave a repeatable
  artifact. Write automated tests only for rules with many edge cases, data/API contracts, or
  cases I ask for.

## Planning

- Ask at least one round of clarifying questions before finalizing a plan, unless I say
  "no questions". A plan is not permission to implement; I start that with `/implement <plan>`.
