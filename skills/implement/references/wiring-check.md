# Wiring check

Read before calling a build of real size done.

Trace every connection in a build end-to-end — presence and wiring only — so nothing is missing, broken, or orphaned.

**Decision points:** If an interactive question tool (e.g. `AskUserQuestion`) is available, use it with 2–4 prefilled options, recommended option first and labeled "(Recommended)". Otherwise, print the same options as a numbered list in chat, state the recommended number, and wait for a reply. Never proceed past a decision point on an assumption.

Three behaviors define this check:

1. **Trace, don't skim.** A QA pass is an inventory plus a trace of every item to its endpoint — not a vibe-read of the code.
2. **Ask, don't assume intent.** When you can verify *that* something is broken but can't know what it was *meant* to do, that's a question for the user, not a guess.
3. **Learn and remember.** Every answer the user gives is recorded in a project notes file so the next pass starts smarter.

## Workflow

### 0. Load prior knowledge

Look for `qa-notes.md` in the project root (or working directory). If it exists, read it — confirmed intents, prior answers, intentional exceptions. Treat its contents as ground truth unless the code has visibly changed in a way that contradicts it. If it doesn't exist, create it at the end of this pass.

### 1. Build the inventory

Map what exists before judging it. Walk the project and list every **connection point** — every place where one thing refers to another:

- Interactive elements (buttons, links, forms, inputs) and the handlers, destinations, or endpoints they claim
- Routes/views and the components or pages they render
- Imports/exports/requires and the files they point at
- Asset references (images, fonts, stylesheets, scripts) and the files behind them
- Data flow: state and props declared vs actually consumed; API calls vs the UI that displays their results
- IDs and selectors referenced in JS/CSS vs elements that actually carry them
- Config/env references vs values that exist

For a small artifact this inventory lives in your head; for a real codebase, write it down so nothing silently drops out. Read `wiring-check/connection-types.md` for the exhaustive per-category checklist on any substantial pass.

### 2. Trace every connection end-to-end

For each inventory item, follow it to its endpoint and classify it:

- **Verified** — the connection resolves and the endpoint does what the reference implies.
- **Broken** — the connection fails: handler undefined, file missing, route unregistered, ID mismatch, endpoint 404. Provable, no intent needed.
- **Orphaned** — the reverse failure: a handler no element calls, an exported component nothing imports, a defined route nothing links to, state that's set but never read.
- **Uncertain intent** — it resolves, but you can't tell if it resolves to the *right* place.

Where the environment allows, verify by *doing*, not just reading: run the build, click the flows, hit the endpoints, load the pages, check the console. Static tracing catches most wiring bugs; execution catches the rest. If you can't execute, say so in the report and mark which findings are static-only.

### 3. Ask about the uncertain

Never resolve uncertain intent by silently picking an interpretation. Also never drip questions one at a time across a long conversation.

- **Batch** all uncertain-intent items into one round of decision-point questions at the end of the trace.
- **Make each question cheap to answer**: show the evidence (file/line or element), state 2–3 plausible intents as options (plus "something else" when useful).
- **Filter through the notes file first.** If `qa-notes.md` already answers it, don't ask — apply the recorded answer and cite it.
- **Don't ask what you can verify.** If two more minutes of tracing would answer it, trace.

If the user answers "that's intentional," record it — that is exactly the knowledge this check accumulates.

### 4. Report by severity

Deliver a report ordered by what hurts most:

1. **Broken** — what, where (file/line or element), evidence, concrete fix. Where the fix is unambiguous (typo'd path, renamed handler), offer to apply it or apply it if already editing with the user's blessing.
2. **Orphaned** — each tagged "likely dead code, safe to remove" vs "looks like an unfinished feature — confirm before deleting."
3. **Answered uncertainties** — what you asked, what the user said, what you did about it.
4. **Verified** — compact summary (counts per category), plus anything you *couldn't* check and why.

Right-size it: a single artifact gets a few sentences; a codebase gets the structured report.

If you write a report file, and the working directory is a git repository, write outputs to the project folder outside the git tree, or to the session scratchpad — never commit process artifacts. Prefer keeping `qa-notes.md` as a durable project note the user can edit; if the repo is client-facing and the user does not want it committed, place it outside the git tree and say where.

### 5. Write back what you learned

Create or update `qa-notes.md` in the project. Append, don't overwrite; keep entries dated and terse:

```markdown
# QA Notes
Maintained by the wiring check. Records confirmed intents and user
decisions so future QA passes don't re-ask. Safe to edit by hand.

## Confirmed intents
- 2026-07-07: `newsletter` field in signup form is collected but unused —
  intentional, backend integration planned for later. Do not flag.

## Decisions & conventions learned
- 2026-07-07: dead code should be flagged but NOT auto-deleted.

## Recurring problem areas
- 2026-07-07: handler renames have broken buttons twice — check
  onClick↔function-name pairs extra carefully in this project.
```

The three sections matter: **confirmed intents** kill repeat questions, **decisions & conventions** teach how this user wants QA to behave, and **recurring problem areas** focus future passes where this project actually breaks.

If a lesson is clearly universal rather than project-specific, suggest the user update this reference — do not edit it mid-run.

## Scope discipline

This check is about **presence and connection** — is everything there, and does everything go where intended. It is not a general code review, a style critique, or a performance audit. If you spot a serious issue outside scope while tracing (security hole, data-loss bug), mention it in a short "outside QA scope but worth knowing" note — never silently ignore a live grenade — but don't let the report sprawl.

## When there's nothing to trace against

If asked to QA something with no stated intent (bare files, no conversation history, no notes file), the structure itself declares intent: a button declares it should do something, a nav link declares a destination should exist, a fetch declares a consumer. Trace against those implicit declarations; reserve questions for the genuinely undecidable.

## Guardrails

- Do not silently rewire product intent when a connection is ambiguous — ask.
- Do not auto-delete orphaned code without confirmation.
- Do not expand into visual design, performance tuning, or full engineering review.
- Do not re-ask questions already answered in `qa-notes.md`.
- Do not claim runtime verification when only static tracing was possible — name the limit in the report.
