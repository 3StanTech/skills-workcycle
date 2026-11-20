---
name: handoff
description: >-
  Make work resumable in a new session on any host: pause it mid-task, stop it
  urgently, or resume it. Stage docs (explore, plan, roadmap, findings) are
  already cold-start ready through the gate their skills run, so handoff is for
  everything else. Pause triggers: /handoff, "prepare to pause", "make it
  resumable", "continue in a new session", "context is nearly full". Urgent
  triggers: /handoff now, "limit is about to hit", "stop now", "I have to go". Resume trigger: "resume
  from <path>". Works with or without a roadmap, plan or explore doc. Not for the
  session-close ritual (`/end`).
---

# Handoff

Make the current work resumable cold: update the doc that owns it (or write one handoff file when nothing does), secure what lives only in this session, and prove a fresh session can continue from the path alone.

**Decision points:** If an interactive question tool (e.g. `AskUserQuestion`) is available, use it with 2–4 prefilled options, recommended option first and labeled "(Recommended)". Otherwise, print the same options as a numbered list in chat, state the recommended number, and wait for a reply. Never proceed past a decision point on an assumption.

**Template:** `references/template.md`. **Gate:** `references/cold-start-gate.md` (the stage skills run it as their last step; pause mode reuses it). **Checker:** `~/.agents/skills/roadmap/scripts/doc_check.py`.

**Paths.** The single owner of where workcycle files go; the other skills point here. Read `~/.agents/local/workcycle.md` first.

- **With a `## Workcycle root` section:** the project's **workcycle folder** is `<root>/<name>`. `<name>` is the `## Workcycle folders (overrides)` entry for the project path (longest prefix wins), else the basename of the nearest folder holding `master.md`, else of the git root; no project → `<root>/General`. Each piece of work gets a **work folder**, `<workcycle folder>/<YYYY-MM-DD>-<slug>/`, created by its first stage (explore, explore-design, a plan or page plan with no explore doc, a handoff nothing owns); later stages write into the work folder of the doc they were given. Inside, created when needed: `plans/` (explore docs, plans, page plans), `handoffs/`, `audits/`, `runs/`, `mocks/`, and `ROADMAP.md` for a roadmap. The project's `master.md` and other gitignored context files live at the workcycle folder's root, and the project keeps symlinks to them. Finished work folders move to `<workcycle folder>/_archive/` when eligible (`end` skill step 11 owns the rule).
- **Without it (the default):** `<handoffs-root>` is: project is a git repo → `<project-parent>/<project-name>-handoffs/`; project folder is not a git repo (it may contain one) → `<project>/handoffs/`; no project → the no-project handoffs folder in `~/.agents/local/workcycle.md`, else `~/.agents/handoffs/`. A roadmap's work folder is `<handoffs-root>/roadmap-<slug>/`; other docs use `<handoffs-root>/plans/`, `audits/` and its root.

- **Another host's paths:** a doc written on another host names paths under that host's workcycle root (a cloud session's `/home/user/workcycle-files/…`, the owner machine's own root). Before opening one, pull the root when it is a git repo (`git -C <root> pull --ff-only`), then read the path with the other host's root prefix replaced by this host's root (the part after `workcycle-files/` or after the local root is the same on both). Write new paths with this host's root as usual.

Elsewhere in these skills `<handoffs-root>` means the workcycle folder when a root is set, and **work folder** means the folder above. Neither is ever inside a product repo; the workcycle root may be its own private repo.

---

## 1. Find the owning doc

1. **A roadmap governs the work** (`master.md` lists it under `## Active roadmaps`, or the user named it): run the `roadmap` skill's Update **steps 1–7 only** (state, Resume here, log, budget, checker); this skill owns the pause, so skip Update step 8 and continue §2 here. If the work is mid-plan, also rewrite the current phase plan's Start here. Write a handoff only for in-flight detail neither doc should hold, in the roadmap's work folder (`handoffs/`), and link it from the roadmap's `In-flight handoff:` line.
2. **A plan, explore doc or mocks README owns it:** rewrite **that doc's Start here** (status, verified state, numbered next actions, paste prompt). No second file.
3. **Nothing owns it:** write a handoff file from the template at `<work folder>/handoffs/<YYYY-MM-DD>-<slug>.md` (without a workcycle root: `<handoffs-root>/<YYYY-MM-DD>-<slug>.md`). If one for the same thread exists from today, rewrite it. If an earlier one exists, set `Previous handoff:` and add `> **Superseded:** resume from <new path>.` as the old file's first line.

**Roadmap promotion:** if the work now has 2 or more proposed phases, or this is its third handoff, ask: promote to a roadmap (Recommended) / keep handing off. On promote, run `roadmap` Create, seeded from this state.

**Writing rules:** write from what the session knows; do not re-scan the codebase. Next actions first (2–5, exact commands and `file:line`). Read first lists only what the next session needs, each with its reason. Point, don't paste: copy only facts that exist nowhere else (chat-only decisions, what failed). Project rules only. Handoff file budget 8 KB.

## 2. Pause mode

1. **Owning doc:** §1.
2. **Secure the scratchpad.** It is session-specific and can disappear.
   - Secrets move to the **secret folder** `<handoffs-root>/.secrets-<slug>/` (dir 0700, files 0600), referenced by path only, never printed. When the workcycle root is a git repo, its `.gitignore` must exclude `.secrets-*/`; check with `git check-ignore` before writing. This is the only place the skills put secret files.
   - Reusable scripts and evidence move to the work folder (`runs/`); without a workcycle root and no roadmap, to `<handoffs-root>`.
   - Launch configs that pointed at the scratchpad are repointed.
3. **Stop or record running things.** Stop dev servers (`preview_stop`) and background jobs. Record each headless helper in the owning doc as its full registry entry `{"engine","id","task","lane","topic"}`; the resuming session imports those entries per headless contract §3 (imported entries). For in-session subagents, record the packet and a WIP note to relaunch from; they cannot be resumed from a new session. Reset browser viewport emulation.
4. **Verify current state** with cheap checks: `git status --short`, `git branch --show-current`, `git log --oneline -5`, ahead/behind the remote; the plan's `**Status:**`; test branches or databases the next session reuses and their expiry. Anything not checked goes under **Not verified**.
5. **Run the gate's steps 1–5** (`references/cold-start-gate.md`) on the owning doc: Start here, chat decisions, scratchpad sweep, paths, probes. Read the doc as a fresh session given only its path, on any host, with no `/prime`, roadmap Resume or chat history. Facts from other files the session would otherwise open (other repos' `master.md`, IDs, versions, quotas) are copied in as a short dated list with source paths. A mid-task pause probes beyond the next stage, read-only, recording each result with a date:

   | Assumption | Probe |
   |---|---|
   | Tools and versions | `node -v`, `java -version`, CLI `--version`; supported-engine ranges from their docs |
   | Access | the MCP/CLI can see the target resource (list the project, repo or branch) |
   | Auth | logged in where needed (`… login:list`, `gh auth status`); never read secrets, only presence |
   | Env traps | frameworks that auto-load env files (`.env.local`, `.env`) that could point at production; plan explicit overrides plus a guard that refuses to run against production |
   | Interactive commands | anything that prompts (logins, `init` wizards) cannot run in an agent shell without a TTY; make it an owner step with an answer sheet |
   | Browser identity | which browser holds the needed sign-ins (the built-in pane has none; Claude in Chrome uses the owner's); the agent never enters passwords |
   | Third-party terms | licences, quotas and pricing verified at the official source, with the URL and date |
   | Sandbox limits | delegated lanes without network, ports or JDK; move those steps to the dispatcher or CI |

   A failed probe becomes a doc change (a new step, an owner pre-flight item, a guard), never "check later".
6. **Owner pre-flight and authority.** List what the owner must do before the session starts, with exact paths and commands; create empty secret files in advance in the secret folder (step 2) so the owner only pastes a value. Separate what is pre-approved from what needs a go at the time (deleting branches, commits, pushes, merges, deploys, production writes, billing).
7. **Align and hand over.**
   - The roadmap's Resume here, any handoff pointer and the doc say the same thing.
   - Carry due reminders: copy any `next close` line from `master.md` → `## Reminders` into Open questions and show it in the reply (leave it; `/end` clears it).
   - Gate step 6: `python3 ~/.agents/skills/roadmap/scripts/doc_check.py --text [--kind <kind>] [--repo <repo>] <file>`. Fix every ERROR; fix each WARN or say why it stays. Then note "cold-start pass <YYYY-MM-DD>" in Start here (the handoff file's header for a handoff).
   - Gate step 8 (publish) last, once the stamp is written.
   - Reply with three lines: the path, the most important next action, and the paste line `resume from <path>`.

## 3. Urgent mode (`/handoff now`)

Order is set by what is lost first. Do these in strict order.

1. **One write first, within the first minute:** an `## Interrupted <YYYY-MM-DD HH:MM> (urgent stop)` block at the top of the owning doc's Start here, or a handoff file when nothing owns the work (template block). It holds the goal, what was in flight (`file:line`, uncommitted edits, the half-done step), the single next action, the paste line, and `Unverified (urgent stop): §2 steps 4–7`, so the block is complete at any moment.
2. **Copy scratch secrets and scripts out** in one command (secrets to the secret folder, §2 step 2, ignore check included).
3. **Stop or record running things** (§2 step 3). Never kill a helper mid-write without recording what it was writing.
4. **Snapshot git state into the block** (branch, HEAD, dirty files). Never commit or push a product repo. Then publish the workcycle docs once (gate step 8): the early recovery copy, and the only way the block survives a cloud session.
5. **If time remains,** run §2 steps 4–6 and step 7's alignment and doc check (not its publish or reply), removing each step from `Unverified (urgent stop)` once done. When none is left, publish a second, final time and reply as §2 step 7 says; otherwise the early copy stands and the resume session runs whatever stays listed first.

## 4. Resume

When a session starts with "resume from <path>":

1. Read the doc or handoff fully, then only the files under **Read first**.
2. If it has an `Interrupted` block, run its `Unverified (urgent stop)` steps first.
3. Verify current state against git with §2 step 4's checks. If git moved on, say so in one line and trust git.
4. Open with **Next actions** as a decision-point menu (recommended first), then start work. Remove the `Interrupted` block once its state is folded into Start here.
5. When the thread's work is done, set `Status: Done`.

---

## Output

- The owning doc's rewritten Start here; or `<work folder>/handoffs/<YYYY-MM-DD>-<slug>.md` (the roadmap's work folder when a roadmap governs the work; without a workcycle root, `<handoffs-root>/<YYYY-MM-DD>-<slug>.md` or `roadmap-<slug>/handoffs/…`).
- Chat: path, next action, paste line.

Outputs stay outside every product repo; never commit them to one (the workcycle root's own private repo is the exception).

## Guardrails

- **Never store secrets,** credentials, tokens or connection strings in a doc. A checker ERROR means the handoff is not done.
- **Never commit a handoff to a product repo or publish it anywhere public,** and never put AI attribution in it. Pushing it to the private workcycle root through gate step 8 is the one exception.
- **Never append checkpoints.** Rewrite the doc or handoff, or supersede it.
- **Never write a parallel handoff** when a roadmap, plan, explore doc or mocks README owns the work.
- **Never state an unverified claim as current state.**
- **Never restate global rules.** List only project-specific ones.
