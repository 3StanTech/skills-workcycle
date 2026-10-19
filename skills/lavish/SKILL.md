---
name: lavish
description: >
  Open an agent-written HTML artifact in Lavish Editor so the user can annotate
  it and send feedback. Use only when the user types /lavish or explicitly asks
  to review or iterate on HTML in Lavish. Not for ordinary plans, tables,
  diagrams, markdown answers, or production site pages.
license: MIT
when-to-use: Use when the user types /lavish or explicitly asks to review HTML in Lavish Editor.
argument-hint: <what the artifact should show, or the HTML file to review>
disable-model-invocation: true
user-invocable: true
metadata:
  author: Tristan Dolfo, adapted from Kun Chen (kunchenguid/lavish-axi)
  hermes-tags: html, review, artifacts, visualization
  hermes-category: productivity
---

# Lavish Editor

Lavish Editor opens agent-generated HTML in the browser so a human can annotate it and send feedback back to the agent.

## Invoke only on request, but offer it

Do not start a Lavish session unless the user typed `/lavish` or clearly asked to review or iterate on HTML in Lavish. Ordinary plans, comparisons, diagrams, tables, and chat answers stay in the current medium.

This skill is hidden from the model's skill list on purpose (`disable-model-invocation`), so a missing entry does not mean Lavish is unavailable. explore-design opens Lavish itself (mock refinement and decision pages) per `~/.agents/skills/explore-design/references/lavish-review.md`. Elsewhere, start only on `/lavish` or an explicit request.

If `$ARGUMENTS` is non-empty, it is the artifact brief or the file to review. If it is empty, use an HTML file already produced in this session (for example the mocks just built), or ask what to review. Do not invent a visualization uninvited.

## Artifact location

- **Existing mocks or artifacts:** open them in place when their folder is outside every git working tree (for example `Clients/<client>/redesign-mocks/mock-a.html`). Lavish serves the HTML's own folder, so relative asset paths like `assets/img/hero.webp` keep working. Never use root-relative `/` paths.
- **New standalone artifacts:** write them under `~/.lavish-axi/artifacts/`, with a dated slug filename such as `2026-09-18-plan-review.html`. Copy any local assets beside the file.
- Never write Lavish artifacts into a git working tree.

## Design reviews and polling

Follow `~/.agents/skills/explore-design/references/lavish-review.md` for design reviews (project design system, `input` playbook picks, targeted element edits) and for polling on each host (Claude Code: tracked background `poll`; Codex and Grok: foreground `poll`; never `nohup`, `&` or `disown`).

## Local-only

Do not run `lavish-axi share`. Do not publish to ht-ml.app.

## Not for production sites

Do not use Lavish as an editor for project source pages. It is an annotation loop for agent-written HTML artifacts and mocks.

## Current guidance lives in the CLI

Workflow, design and playbook details come from the CLI, not this file, because installed copies go stale. The local rules above (invocation, location, local-only, production) still apply.

- `npx -y lavish-axi@0.1.90 --help` for commands and the review-loop workflow.
- `npx -y lavish-axi@0.1.90 reply --help` to post an agent reply and exit once the server accepts it, when you are not about to long-poll.
- `npx -y lavish-axi@0.1.90 design` for design-direction priority and current snippets.
- `npx -y lavish-axi@0.1.90 playbook <id>` for focused artifact guidance (`npx -y lavish-axi@0.1.90 playbook` lists the ids; use `input` and `comparison` for design picks).

You do not need lavish-axi installed globally. Invoke it with `npx -y lavish-axi@0.1.90 <html-file>`. If lavish-axi output shows a follow-up command starting with `lavish-axi`, run it as `npx -y lavish-axi@0.1.90 ...` instead.

**Origin:** adapted from Kun Chen's lavish-axi skill; see `NOTICE`. The Lavish workflow here (this skill plus explore-design's `lavish-review.md` and `decision-page.md`) also adapts four rules from Thariq Shihipar's html-plan skill; the decision page ([decision-page.md](../explore-design/references/decision-page.md)) carries them. Update this skill with `python3 ~/.agents/scripts/skill-upstream-merge.py lavish` (dry run first), never `npx skills update`. The editor version is pinned (`lavish-axi@0.1.90`); bump it in every call site and in `NOTICE` together.

## Request

$ARGUMENTS
