# Verification (E2E-first)

Read at the verify step of every implementation. The short rule lives in `~/AGENTS.md` → Testing; this file holds the detail. Project rules that require tests win over this file.

## Policy

"Done" means the change ran the way a user would use it, on a scenario that could fail, and left an artifact someone can re-run or re-inspect. Passing tests the agent wrote about its own code does not count as proof.

1. **Run it like a user.** Exercise the real entry point on a medium-to-hard case, never only the easiest path.
2. **Leave a repeatable artifact.** Something the owner can open or re-run later.
3. **Automate only where it pays.** Write automated tests only in the four allowed cases below.
4. **Never write the banned kinds.** See Banned.
5. **Respect existing tests.** Keep them running; stop growing them; prune the bad ones you touch.

## Scenarios come from the owner

Each plan carries 2–5 owner-approved scenarios (create-plan step 2). They state what runs, the hard case, and the artifact. Run every one of them. When a plan has none (ad-hoc work), pick the scenario a real user would hit first plus one failure path, and say which you chose.

Good scenario cases include failure paths: bad input, empty input, a dependency timeout, permission denied, a slow network, a second device or user.

## Running it like a user

| Surface | How | Artifact |
|---|---|---|
| Web UI (Claude Code) | The built-in browser (`preview_start` / `navigate`, click and type through the flow) at phone (390) and desktop (1366–1440) width | Screenshot set of the key states, named by step |
| Web UI (Codex, Grok) | Playwright (`npx playwright`) or the `chrome-devtools` MCP | Playwright trace or video, or a screenshot set |
| CLI or script | The real command with real arguments | The command and its output |
| API or backend | `curl` or a small script against a test database or branch, never production | A script with definite pass/fail output |
| Data change | A query before and after on a test branch | Both query results |

Save artifacts outside git (the session scratchpad, or the project's handoffs folder), unless the plan keeps a Playwright spec in the project's existing test directory. Creating databases, branches or preview deploys for testing needs the owner's permission per plan or phase.

## Script hygiene

- **Scripts enforce their own time limit.** Node: `setTimeout(() => { console.error('timeout'); process.exit(2) }, ms).unref()`. macOS has no `timeout` binary; the shell fallback is `perl -e 'alarm N; exec @ARGV' <command>`.
- **No foreground `sleep` polls.** Wait with the host's background-command or Monitor tools.
- **Browser scripts retry once on puppeteer "detached Frame" errors** and log the retry.
- **One current script per scenario.** Each evidence folder has a `scripts/README.md` listing one current script per scenario with its expected output. Superseded scripts move to `scripts/old/` and are never listed in a plan's re-run list.

Example: `<project>-handoffs/<slug>-mocks/verify/scripts/timed-reload.cjs` (Node timer plus a database truth check).

## Allowed automated tests

1. **Owner- or plan-specified cases.** The owner wrote the case or approved it in the plan. Their intent is the value; the agent's guess is not.
2. **Pure rules with many boundary inputs.** Date and timezone helpers, money and rounding, parsers, validators, scoring formulas: cheap to check thousands of inputs without a browser.
3. **Data/API contracts.** Integration tests at boundaries where schemas drift: service to service, app to database, app to a provider's response shape.
4. **Golden examples.** Fixtures captured from real data (anonymised), checked against known-good output.

E2E specs (Playwright) that encode an owner-approved scenario count as case 1.

## Banned

- **Tautological tests:** they restate the implementation (assert that a function returns what its body obviously returns, or that a constant equals itself).
- **Change-detector tests:** they fail on any edit rather than on wrong behaviour. This includes tests that read source files as strings, snapshot internal structure, or assert exact markup or class names that users never see.
- **Mocking the unit under test,** or mocking so much that the test checks the mock.
- **TDD by default.** Agent-written failing tests first, then code, measured worse and costlier for agents. Use it only when the owner asks.
- **Reflex regression tests.** After a bug fix, add a test only when no existing behaviour test or scenario could have caught the bug; otherwise fix the existing test's data or assertion.

## Existing tests

- Keep running the project's suite when it exists; a red suite is still a blocker.
- Do not add to it outside the allowed cases.
- When work touches an area, delete clear change-detector or tautological tests there and list each deletion (file, test name, reason) in the report. Do not run a prune pass across a whole project unless the owner asks.

## Evidence (2026-10-09)

| Source | Claim | Verdict |
|---|---|---|
| [Kun Chen, 2026-10-08](https://x.com/kunchenguid/status/2108030810691629403) | DeepSWE, Sonnet 5.5 high: banning agent-written tests left success flat (slightly higher, not significant) with significantly less time and tokens; tests were 65% unit, 35% integration, neither helped. Follow-up: human-guided tests may help; E2E not measured | Follow, with his caveats |
| [Kun Chen, 2026-09-08](https://x.com/kunchenguid/status/2097035514067272079) | E2E is the only test that guards real behaviour; making E2E match real use is high ROI | Follow |
| Kun Chen, 2026-06-09 (quoted in the above) | TDD harmful for agents (ProgramBench; secondhand figures: lower pass rate, +50–70% cost) | No TDD by default |
| [Chen et al. 2026](https://arxiv.org/abs/2602.07900) | SWE-bench Verified, 6 models: changing agent test volume did not change outcomes; agent tests are mostly print-style observation | Supports the policy |
| [Ansh Nanda](https://x.com/anshnanda/status/2101627891721371971) | E2E as the main mechanism with a repeatable artifact (video for UI, script for backend); failure modes first when isolating. Reply: verify on a medium-to-hard scenario | Follow + enhance |
| [Robert Baddeley](https://x.com/imrobertjames/status/2100787901701456057) | Ban tautological and change-detector tests; no regression test without a genuine gap | Follow verbatim |
| [Richard Wu](https://x.com/0xrwu/status/2106160407576490289) | E2E > integration > golden; small tests valid for pure rules ("the 1%") | Follow, keep the exception |
| [Sherwood Callaway](https://x.com/shcallaway/status/2106142042405453879) | Deleted 800k lines of unit tests; results not yet posted | Ignore until results exist |

Risks still standing: the studies cover single benchmark tasks, not long-lived codebases (Matt Pocock's objection); E2E's own value is unmeasured; E2E is slower and can be flaky. Revisit when new evidence lands.
