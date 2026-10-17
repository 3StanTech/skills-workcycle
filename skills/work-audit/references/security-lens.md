# Lens 7: Security & production readiness (Full only)

Ask each question of the work in scope; a finding needs the evidence named after the dash. Skip a group the work cannot touch, and say so in the coverage line.

## Credentials
- Is any key, token or password in source, logs, errors, examples or fixtures? — grep the diff and new files for key shapes and `.env` values.
- Do secrets come only from env or a secrets manager? — trace each credential to its read site.

## Injection and untrusted input (incl. LLM output)
- Are queries parameterized and shell calls argument arrays? — grep for string-built SQL/commands.
- Where does user or LLM output enter, and what validates it before use in SQL, shell, file paths or HTML? — follow each entry point to its sink.

## Auth
- For every endpoint or action: who may do this, and where is it checked? — locate the check in code; a missing one is a finding.

## Agent permissions
- Does any agent or automation hold narrower access than the user's own (own key, scoped token, own directories)? — read its config and env.

## Data exposure
- What leaves the machine, to which provider, and does the owner know? — list outbound calls and payload fields.

## Errors
- Does every external call handle failure with a message saying what failed and what to do? — grep for bare `except: pass`, empty catches, unhandled promises.

## Logging
- Can a failure be reconstructed from logs, with no secrets or full client data in them? — read the log statements.

## Rollback
- Can this change be undone in minutes (revert, flag, previous deploy, down migration)? — name the exact undo step.

## Idempotency
- Is anything triggered automatically (cron, webhook, agent) safe to run twice? — read the handler for duplicate-write paths.

## Handover
- Is config documented, setup reproducible from the README, and is there a plain-language "how to tell it is misbehaving"? — follow the README on a clean checkout where feasible.

## AI provider failure and confident-wrong output
- What happens when the provider is down or rate-limited (timeout, backoff, degraded mode)? — read the call wrapper.
- What happens when the model is confidently wrong? — find the validation or human check; "it won't be" is a finding.

## Autonomous writes
- Does anything write shared state without a human? If so, is storage versioned or transactional rather than a sync folder? — read the write path.
