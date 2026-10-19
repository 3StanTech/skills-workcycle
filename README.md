# skills-workcycle

The build cycle as agent skills: explore an idea, plan it, implement it, audit the result, and close the session so the next one starts warm. Works with Claude Code, Codex and Grok through the shared `~/.agents/skills` folder.

## Contents

| Skill | Role |
| ----- | ---- |
| `explore` | Five-stage interactive discovery for a new feature, system or capability |
| `explore-design` | Turn a UI, brand or image idea into an approved mock and a cold-start explore doc |
| `create-plan` | Write a detailed, plan-only implementation plan before coding |
| `implement` | Execute a clear, authorized plan, verify it and report |
| `work-audit` | Audit that auto-fixes clear issues before commit, Light or Full depth |
| `handoff` | Make work resumable in a new session on any host |
| `roadmap` | One living `ROADMAP.md` per multi-phase initiative |
| `prime` | Start a session warm from project state, read-only |
| `remind` | Park a reminder in an existing project file so it resurfaces later |
| `end` | Fold the session's decisions into the owning project's `master.md` |
| `lavish` | Open agent-written HTML in Lavish Editor for annotation (manual: `/lavish`; explore-design opens it itself) |

Hooks (`hooks/`) and `scripts/wait-ci-deploy.sh` (bounded wait for CI and deploy after a push) ship with it.

## Setup

### 1. Prerequisites

- Python 3 and git.
- Node.js, for `lavish`, `explore-design` and create-plan decision pages (they run the pinned `npx -y lavish-axi@0.1.90`, which downloads on first use).
- Optional: `gh` (and `jq` for the Netlify check) for `scripts/wait-ci-deploy.sh`.
- Optional: [`skills-orchestration`](https://github.com/3StanTech/skills-orchestration) for helpers, model routing and headless Claude/Codex/Grok workers. Without it, `implement` runs single-agent in your session.

### 2. Install

```sh
git clone https://github.com/3StanTech/skills-workcycle.git ~/.agents/bundles/skills-workcycle
~/.agents/bundles/skills-workcycle/install.sh
~/.agents/bundles/skills-workcycle/install.sh --check
```

`install.sh` symlinks each skill into `~/.agents/skills` (read natively by Codex and Grok) and into the skills folder of every installed host (`~/.claude/skills` for Claude Code, `~/.hermes/skills`, `~/.pi/agent/skills`; created when the host is installed but has no skills folder yet). Hooks go to `~/.agents/hooks`, scripts to `~/.agents/scripts`. It never replaces a real file or a link pointing elsewhere (reported as `conflict`); `--check` changes nothing and exits 1 on any finding. Re-run it after installing a new host. To update later: `git -C ~/.agents/bundles/skills-workcycle pull`.

### 3. Register the hooks

`install.sh` only places the hook files; each host registers them in its own config. Claude Code, in `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      { "matcher": "Bash|Agent", "hooks": [{ "type": "command", "command": "\"$HOME/.agents/hooks/create-plan-no-implement.sh\"", "timeout": 10 }] }
    ],
    "UserPromptSubmit": [
      { "hooks": [{ "type": "command", "command": "\"$HOME/.agents/hooks/create-plan-no-implement.sh\"", "timeout": 10 }] }
    ],
    "SessionStart": [
      { "hooks": [{ "type": "command", "command": "\"$HOME/.agents/hooks/roadmap-session-start.sh\"", "timeout": 10 }] }
    ],
    "PostToolUse": [
      { "matcher": "Bash", "hooks": [{ "type": "command", "command": "\"$HOME/.agents/hooks/push-ci-reminder.sh\"" }] }
    ]
  }
}
```

Merge these into any hooks you already have. Codex (`~/.codex/hooks.json`) and Grok (`~/.grok/hooks/<name>.json`) take the same shape; use the absolute path to your home folder there, in quotes if it contains a space. Matchers per host:

| Event | Claude Code | Codex | Grok | Script |
| ----- | ----------- | ----- | ---- | ------ |
| `PreToolUse` | `Bash\|Agent` | no matcher | `Bash\|run_terminal_command\|spawn_subagent` | `~/.agents/hooks/create-plan-no-implement.sh` |
| `UserPromptSubmit` | no matcher | no matcher | no matcher | `~/.agents/hooks/create-plan-no-implement.sh` |
| `SessionStart` | no matcher | no matcher | not registered | `~/.agents/hooks/roadmap-session-start.sh` |
| `PostToolUse` | `Bash` | not registered | not registered | `~/.agents/hooks/push-ci-reminder.sh` |

The hooks are guard rails (plan-only enforcement, roadmap reminder, CI reminder after a push); the skills run without them.

### 4. Your policy file

The skills defer to `~/AGENTS.md` for your personal rules: testing and publication policy, how to delegate, how to address you. Start from the example and edit it:

```sh
cp -n ~/.agents/bundles/skills-workcycle/AGENTS.example.md ~/AGENTS.md
```

`cp -n` never overwrites: if you already have `~/AGENTS.md`, merge the parts you want from the example by hand.

Without the file the skills still run; they just have no personal rules to defer to. Claude Code reads it when `~/.claude/CLAUDE.md` contains the line `@~/AGENTS.md`.

### 5. Choosing models (optional)

You never have to configure models. Name them when you want to: the closing prompt of `explore` and `explore-design` ends with a line such as

```
implement using <model-id> <effort> <chillin|vibin|supersoldiers>
```

and lists the model IDs installed on your machine. Fill it in, or delete it and the agent asks you (or uses your routing table, if you filled one in `skills-orchestration`). The auditor that reviews finished work is always yours to name or confirm.

### 6. Local settings (optional)

Some skills read an untracked `~/.agents/local/workcycle.md` when it exists, for settings that belong to your machine rather than to the skills. Example:

```markdown
## Projects root
`~/Projects/`

## No-project handoffs folder
`~/Projects/handoffs/`

## work-audit client roots
- `~/Projects/clients`

## /end extra steps
(any extra close steps `/end` should run, with which projects they apply to)
```

Sections: `Projects root` (prime, end), `No-project handoffs folder` (handoff, roadmap; default `~/.agents/handoffs/`), `Project rules` (end), `Mocks folders` (explore-design), `work-audit client roots` (work-audit triage), `/end extra steps` (end).

### 7. Verify

```sh
~/.agents/bundles/skills-workcycle/install.sh --check
cd ~/.agents/bundles/skills-workcycle
python3 -m unittest discover -s skills/work-audit/tests
CREATE_PLAN_GUARD_SCRIPT=$PWD/hooks/create-plan-no-implement.py python3 -m unittest discover -s hooks -p 'test_*.py'
```

The same suites run on GitHub Actions for every push and pull request to `main` (`.github/workflows/test.yml`).

### 8. Uninstall

Remove the hook entries from each host config, then every link that resolves into the bundle (including relative host links), then the clone:

```sh
python3 - <<'PY'
import glob, os
bundle = os.path.realpath(os.path.expanduser("~/.agents/bundles/skills-workcycle")) + os.sep
dirs = ["~/.agents/skills", "~/.agents/hooks", "~/.agents/scripts", "~/.claude/skills", "~/.hermes/skills", "~/.pi/agent/skills"]
links = [p for d in dirs for p in glob.glob(os.path.join(os.path.expanduser(d), "*"))
         if os.path.islink(p) and os.path.realpath(p).startswith(bundle)]
for p in links:
    os.remove(p)
print(f"removed {len(links)} links")
PY
rm -rf ~/.agents/bundles/skills-workcycle
```

## Dependencies

- Python 3 and git.
- `skills-orchestration` is optional. Without it, the Orchestration sections of `create-plan` and `implement` do not apply, `implement` runs single-agent in the session (Chillin semantics, no helpers, no routing table), and the create-plan hook skips launch detection.
- `scripts/wait-ci-deploy.sh` needs `gh`, and `jq` for the Netlify check.
- `explore-design` (refine step and decision pages) and `create-plan` decision pages need Node.js: they run the Lavish review tool with `npx -y lavish-axi@0.1.90` (pinned; bump every call site and `skills/lavish/NOTICE` together). The `/lavish` command is included as `skills/lavish`, adapted from Kun Chen's skill (see Credits and `skills/lavish/NOTICE`).

## Not in this repo

Secrets, runtime state (`~/.agents/state/`), the optional Netlify site map (`~/.agents/scripts/netlify-sites.json`), your policy file `~/AGENTS.md` (start from `AGENTS.example.md`) and your local settings `~/.agents/local/workcycle.md`.

## Credits

- The `lavish` skill is adapted from Kun Chen's [lavish-axi](https://github.com/kunchenguid/lavish-axi) skill (MIT; notice in `skills/lavish/NOTICE`). Lavish Editor itself is Kun Chen's npm package `lavish-axi`, run with `npx` and not redistributed here.
- The Lavish workflow here (the `lavish` skill plus explore-design's `lavish-review.md` and `decision-page.md`) also adapts four rules from Thariq Shihipar's [html-plan](https://github.com/anthropics/claude-plugins-community/tree/main/html-plan) skill (Claude Code team, Anthropic; [announcement](https://x.com/trq212/status/2107192901537329354)).

## License

MIT. See `LICENSE`.
