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

Hooks (`hooks/`) and `scripts/wait-ci-deploy.sh` (bounded wait for CI and deploy after a push) ship with it.

## Install

```sh
git clone git@github.com:3StanTech/skills-workcycle.git ~/.agents/bundles/skills-workcycle
~/.agents/bundles/skills-workcycle/install.sh
~/.agents/scripts/link-hosts.sh
```

`install.sh` symlinks each skill, hook and script into `~/.agents/skills`, `~/.agents/hooks` and `~/.agents/scripts`; it never replaces a real file or a link pointing elsewhere (reported as `conflict`). `install.sh --check` changes nothing and exits 1 on any finding. `link-hosts.sh` is machine tooling that lives outside this repo; it exposes the skills to Claude, Hermes and Pi.

## Hook registration

`install.sh` only places the hook files. Register them in each host's own config (Claude Code: `~/.claude/settings.json`; Codex: `~/.codex/hooks.json`; Grok: `~/.grok/hooks/`). Matchers differ per host, as configured today:

| Event | Claude Code | Codex | Grok | Script |
| ----- | ----------- | ----- | ---- | ------ |
| `PreToolUse` | `Bash\|Agent` | no matcher | `Bash\|run_terminal_command\|spawn_subagent` | `~/.agents/hooks/create-plan-no-implement.sh` |
| `UserPromptSubmit` | no matcher | no matcher | no matcher | `~/.agents/hooks/create-plan-no-implement.sh` |
| `SessionStart` | no matcher | no matcher | not registered | `~/.agents/hooks/roadmap-session-start.sh` |
| `PostToolUse` | `Bash` | not registered | not registered | `~/.agents/hooks/push-ci-reminder.sh` |

Run the hook tests from the bundle (this includes the create-plan guard cases): `CREATE_PLAN_GUARD_SCRIPT=<bundle>/hooks/create-plan-no-implement.py python3 -m unittest discover -v -s <bundle>/hooks -p 'test_*.py'`.

## Dependencies

- Python 3 and git.
- `skills-orchestration` is optional. Without it, the Orchestration sections of `create-plan` and `implement` do not apply, `implement` runs single-agent in the session (Chillin semantics, no helpers, no routing table), and the create-plan hook skips launch detection.
- `scripts/wait-ci-deploy.sh` needs `gh`, and `jq` for the Netlify check.
- `explore-design` (refine step and decision pages) and `create-plan` decision pages need Node.js: they run the Lavish review tool with `npx -y lavish-axi`, which downloads on first use. The optional `/lavish` command is a separate third-party skill (`github.com/kunchenguid/lavish-axi`, MIT), not included here.

## Not in this repo

Secrets, runtime state (`~/.agents/state/`), the personal Netlify site map (`~/.agents/scripts/netlify-sites.json`), and the owner policy file `~/AGENTS.md`.

## Your policy file

The skills refer to `~/AGENTS.md` for personal rules (how to address you, testing and publication policy, which models to delegate to). It is not part of this repo: write your own, or remove those references. Without it the skills still run; they just have no personal rules to defer to.

## License

MIT. See `LICENSE`.
