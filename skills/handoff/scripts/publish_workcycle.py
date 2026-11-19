#!/usr/bin/env python3
"""Commit and push workcycle docs at the end of a stage (cold-start gate step 8).

Usage: publish_workcycle.py [--stage NAME] [--dry-run] PATH [PATH ...]

Each PATH is a work folder or file inside the workcycle root (`## Workcycle root` in
~/.agents/local/workcycle.md), which must be the top of a git work tree. Only those paths are
staged and committed; anything else already staged or changed in the repo is left alone.

Runs only when ~/.agents/local/workcycle.md has a `## Workcycle publish` section that grants a
standing go (its text contains "standing go"); otherwise it exits 3 and the skill asks the owner.
Steps: pull --ff-only when an upstream exists, stage the paths, refuse secrets, commit, push
(never force).

Exit codes: 0 published or nothing to publish · 2 bad usage or a path outside the root ·
3 not configured (ask the owner) · 4 pull or push failed (ask the owner) · 5 secret found.
"""

import argparse
import os
import re
import subprocess
import sys

CONFIG = os.path.join(os.path.expanduser("~"), ".agents", "local", "workcycle.md")
SECRET_NAME = re.compile(r"(^|/)(\.env(\..*)?|\.secrets-[^/]*/.*|.*\.(pem|key)|.*secret.*|.*api[- ]?key.*)$", re.I)
SECRET_TEXT = re.compile(
    r"(sk-[A-Za-z0-9_-]{20,}|sk-ant-[A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}"
    r"|AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY-----|xox[abpr]-[A-Za-z0-9-]{10,})")


def section(text, name):
    m = re.search(rf"^## {re.escape(name)}[ \t]*\n(.*?)(?=^## |\Z)", text, re.M | re.S)
    return m.group(1) if m else ""


def load():
    try:
        with open(CONFIG, encoding="utf-8") as f:
            text = f.read()
    except OSError:
        return None, False
    m = re.search(r"`([^`]*)`", section(text, "Workcycle root"))
    root = os.path.realpath(os.path.expanduser(m.group(1).strip())) if m and m.group(1).strip() else None
    granted = "standing go" in section(text, "Workcycle publish").lower()
    return root, granted


def git(root, *args, check=False):
    r = subprocess.run(["git", "-C", root, *args], capture_output=True, text=True)
    if check and r.returncode != 0:
        raise RuntimeError((r.stderr or r.stdout).strip())
    return r


def say(msg):
    print(f"publish: {msg}")


def main(argv=None):
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("--stage", default="stage")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("paths", nargs="+")
    a = ap.parse_args(argv)

    root, granted = load()
    if not root:
        say("no workcycle root configured; nothing to publish")
        return 3
    if not granted:
        say("no standing go in workcycle.md → Workcycle publish; ask the owner before pushing")
        return 3
    top = git(root, "rev-parse", "--show-toplevel")
    if top.returncode != 0 or os.path.realpath(top.stdout.strip()) != root:
        say(f"workcycle root {root} is not the top of a git work tree")
        return 3

    rel = []
    for p in a.paths:
        real = os.path.realpath(os.path.expanduser(p))
        if real != root and not real.startswith(root + os.sep):
            say(f"refusing a path outside the workcycle root: {p}")
            return 2
        if not os.path.exists(real) and git(root, "ls-files", "--error-unmatch", "--", os.path.relpath(real, root)).returncode:
            say(f"no such path: {p}")
            return 2
        rel.append(os.path.relpath(real, root))

    upstream = git(root, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}").returncode == 0
    if upstream and not a.dry_run:
        pull = git(root, "pull", "--ff-only", "--quiet")
        if pull.returncode != 0:
            say("pull --ff-only failed (diverged or conflicting); ask the owner:\n" + (pull.stderr or pull.stdout).strip())
            return 4

    git(root, "add", "-A", "--", *rel, check=True)
    changed = [l for l in git(root, "diff", "--cached", "--name-only", "--", *rel).stdout.splitlines() if l]
    if not changed:
        say("nothing to publish in " + ", ".join(rel))
        return 0
    bad = [f for f in changed if SECRET_NAME.search(f)]
    diff = git(root, "diff", "--cached", "-U0", "--", *rel).stdout
    hits = [l for l in diff.splitlines() if l.startswith("+") and SECRET_TEXT.search(l)]
    if bad or hits:
        git(root, "reset", "-q", "--", *rel)
        say("refused: possible secret staged; nothing committed. "
            + (f"files: {', '.join(bad)}. " if bad else "") + (f"{len(hits)} line(s) look like a key or token." if hits else ""))
        return 5
    if a.dry_run:
        git(root, "reset", "-q", "--", *rel)
        say(f"dry run: would commit {len(changed)} file(s): " + ", ".join(changed[:10]))
        return 0

    msg = f"{a.stage}: {', '.join(rel)}"
    commit = git(root, "commit", "-q", "-m", msg, "--", *rel)
    if commit.returncode != 0:
        say("commit failed: " + (commit.stderr or commit.stdout).strip())
        return 4
    sha = git(root, "rev-parse", "--short", "HEAD").stdout.strip()
    if not upstream:
        say(f"committed {sha} ({len(changed)} file(s)); no upstream, not pushed")
        return 0
    push = git(root, "push", "--quiet")
    if push.returncode != 0:
        say(f"committed {sha} but push failed; ask the owner:\n" + (push.stderr or push.stdout).strip())
        return 4
    say(f"pushed {sha} ({len(changed)} file(s)): {msg}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
