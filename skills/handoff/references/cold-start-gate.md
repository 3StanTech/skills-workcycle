# Cold-start gate

The last step of every skill that writes a stage doc (explore and explore-design docs, mocks
READMEs, plans, `ROADMAP.md`, work-audit findings files). A doc that passes needs no `/handoff`
or `/prime`: a new session on any host starts the next stage from its paste line alone.

1. **Start here** holds:
   - the goal, and where this step sits (initiative and phase, if any);
   - `Verified <YYYY-MM-DD HH:MM>:` repo, branch and HEAD per repo, or "not a git repo";
   - **Read first:** each path with its reason ("this doc only" when it carries everything);
   - **Next:** the exact paste command in backticks (`/create-plan <path>`, `/implement <path>`,
     `/work-audit fix <path>`);
   - the line "No `/prime` or `/handoff` needed".
2. **Decisions made in chat** during or after the stage are copied into the doc (Discovery Notes,
   Design Decisions or Locked decisions), dated. A decision left only in chat is lost. The
   confirmed restatement is on disk verbatim (`restatement.md` beside a mocks README; the
   "Confirmed restatement" section of an explore doc), not a paraphrase.
3. **Scratchpad sweep.** Artifacts the next stage needs move beside the doc (its folder or
   `runs/`). No session-scratchpad, `/tmp` or `/private/tmp` path stays in the doc.
4. **Paths** are absolute (or anchored to the doc's folder) and either exist or are marked
   "(created by Step N)".
5. **Next-stage probes only**, read-only, each result dated in the doc:
   - before create-plan: HEAD and `git status --short` of each repo the Verified line names;
   - before implement: `git status --short` and HEAD of the plan's repos, `gh auth status` when the
     plan uses `gh` (CI waits, PRs; a cloud session pushes with git and has no `gh` login), and the
     expiry of any test infrastructure it reuses;
   - before work-audit fix: the findings file's `Recorded at` SHAs still match;
   - phase plans: anything the plan's Environments names.

   A failed probe becomes a doc change (a step, an owner pre-flight item), never "check later".
6. **Check and stamp.** Run
   `python3 ~/.agents/skills/roadmap/scripts/doc_check.py --text [--kind <kind>] [--repo <repo>] <doc>`.
   Fix every ERROR; fix each WARN or say why it stays. Then add "cold-start pass <YYYY-MM-DD>" to
   Start here.
7. **Next-stage start.** The skill that reads the doc first re-checks its Verified line cheaply
   (HEAD, `git status --short`, the paths it will act on). A mismatch is reported in one line and
   folded into the doc before work starts. A doc written on another host is read through
   `handoff` skill → Paths → Another host's paths (pull first, then map the root prefix).
8. **Publish, last** (after step 6's stamp, so the pushed copy is the final one; an urgent stop also
   publishes once early, `handoff` skill §3). When the doc sits under a `Workcycle root` (`handoff`
   skill → Paths) that is the top of a git work tree, publish its work folder so a session on
   another host (a cloud thread, the Mac) resumes from the pushed copy: `python3
   ~/.agents/skills/handoff/scripts/publish_workcycle.py --stage <stage> <work folder>`. It refuses
   while anything is already staged in the root, pulls with `--ff-only`, commits only the paths
   given (never the whole root; the root's commit hooks run), refuses earlier unpushed commits
   (checked one by one) that touch other paths and anything that looks like a secret, pushes the
   commit to the upstream branch without force (refusing a remote with several push URLs or one that
   differs from its fetch URL), and confirms the remote branch holds it. A line `standing go: yes …`
   or `standing go: commit and push …` in `~/.agents/local/workcycle.md` → `## Workcycle publish` (not in a
   code block; any other `standing go:` value there withholds it) lets it run unasked; on exit 3
   ask the owner ("Push the workcycle docs for <work folder>?") and, on a yes, run the same command
   with `--owner-approved`. Exit 4 (staged files, pull, push, scope, commit or HEAD-moved problem)
   and 5 (secret) stop and go to the owner with the script's message. Skip this step when no root is set or the
   root is not a git repo. In a cloud session (`CLAUDE_CODE_REMOTE=true`) never skip it: the VM's
   files do not outlast the session.

## When create-plan is next

At the end of explore or explore-design, and at every phase close (implement's roadmap Update),
refresh in the same step **every doc that names that create-plan**: the explore doc's Start here,
the roadmap's Resume here and Environments, and the closing plan's Start here.

- **Next:** the exact paste line; for a roadmap phase,
  `/create-plan <explore doc absolute path> Phase N only`.
- **Verified:** the current time and the HEAD of each repo, read from git now, not copied.
- **Read first:** the current decision range (e.g. D1–D26) and the next phase's readiness section.
- **Line references** (`file:NN`): re-check each against the file; fix or remove it.

Then run step 6 with `--repo` on each refreshed doc: `doc_check.py` warns when the next stage is
create-plan and the repo's HEAD is missing.

Mid-task pauses and urgent stops stay with the `handoff` skill (pause mode reuses steps 1–6 and 8).
