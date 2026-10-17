#!/usr/bin/env python3
"""SessionStart: surface the project's active roadmap (and newest open handoff).

Finds the project from the session cwd (nearest master.md and/or git root), then:
  1. roadmaps listed under `## Active roadmaps` in master.md (not marked Closed)
  2. <handoffs-root>/roadmap-*/ROADMAP.md whose header says `Status: Active`
  3. the newest open handoff in <handoffs-root>/ (not Superseded, not Done)
  4. due reminders in master.md `## Reminders` (when: next session, or a passed date)

<handoffs-root> is <repo-parent>/<repo-name>-handoffs/ for a git repo, or
<project>/handoffs/ for a non-git project folder (roadmap and handoff skills).

Emits Claude Code / Codex SessionStart JSON with additionalContext, or nothing when
the project has neither. Read-only, no network, never blocks: any error exits 0.
"""

import datetime
import glob
import json
import os
import re
import sys

HOME = os.path.expanduser("~")
RESUME_CAP = 1500
HANDOFF_NAME = re.compile(r"^\d{4}-\d\d-\d\d-.+\.md$")
PATH_IN_LINE = re.compile(r"`([^`]+\.md)`|:\s*(\S+\.md)\s*$")
STATUS_VALUE = re.compile(r"\bStatus\**:\**\s*(.*)", re.I)


def walk_up(start):
    d = os.path.abspath(start)
    while True:
        yield d
        parent = os.path.dirname(d)
        if parent == d or d == HOME:
            return
        d = parent


def find_project(cwd):
    master_dir = git_root = None
    for d in walk_up(cwd):
        if git_root is None and os.path.exists(os.path.join(d, ".git")):
            git_root = d
        if master_dir is None and os.path.isfile(os.path.join(d, "master.md")):
            master_dir = d
        if master_dir and git_root:
            break
    return master_dir, git_root


def handoff_roots(master_dir, git_root):
    roots = []
    if git_root:
        roots.append(os.path.join(os.path.dirname(git_root), os.path.basename(git_root) + "-handoffs"))
    if master_dir and master_dir != git_root:
        roots.append(os.path.join(master_dir, "handoffs"))
    return [r for r in roots if os.path.isdir(r)]


def section(text, name):
    m = re.search(rf"^## {re.escape(name)}[^\n]*\n(.*?)(?=^## |\Z)", text, re.M | re.S)
    return m.group(1).strip() if m else ""


def header(text, field):
    m = re.search(rf"^\**{field}:?\**:?\s*(.+)$", text[:3000], re.I | re.M)
    return m.group(1).strip() if m else ""


def header_block(text):
    """Text before the first `## ` heading, capped like header()."""
    m = re.search(r"^## ", text, re.M)
    return (text[:m.start()] if m else text)[:3000]


def closed_in_header(text):
    """Any Status: value in the header block that starts with "closed" wins over an earlier Active."""
    return any(v.strip("*` ").lower().startswith("closed") for v in STATUS_VALUE.findall(header_block(text)))


def read(path):
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except OSError:
        return ""


def active_roadmaps(master_dir, roots):
    found = []
    if master_dir:
        for line in section(read(os.path.join(master_dir, "master.md")), "Active roadmaps").splitlines():
            if "closed" in line.lower():
                continue
            m = PATH_IN_LINE.search(line)
            if m:
                found.append(os.path.expanduser(m.group(1) or m.group(2)))
    for root in roots:
        found.extend(sorted(glob.glob(os.path.join(root, "roadmap-*", "ROADMAP.md"))))
    out, seen = [], set()
    for p in found:
        p = os.path.realpath(p)
        if p in seen or not os.path.isfile(p):
            continue
        seen.add(p)
        text = read(p)
        status = header(text, "Status")
        if closed_in_header(text) or (status and not status.lower().startswith("active")):
            continue
        out.append(p)
    return out


def newest_open_handoff(roots):
    best = None
    for root in roots:
        for name in os.listdir(root):
            if not HANDOFF_NAME.match(name):
                continue
            p = os.path.join(root, name)
            head = read(p)[:1500]
            if "superseded" in head.lower() or header(head, "Status").lower().startswith("done"):
                continue
            if best is None or name > os.path.basename(best):
                best = p
    return best


def due_reminders(master_dir):
    if not master_dir:
        return []
    today = datetime.date.today().isoformat()
    due = []
    for line in section(read(os.path.join(master_dir, "master.md")), "Reminders").splitlines():
        m = re.search(r"when:\s*(next session|on (\d{4}-\d\d-\d\d))", line)
        if m and (m.group(2) is None or m.group(2) <= today):
            due.append(line.strip())
    return due


def build(cwd):
    master_dir, git_root = find_project(cwd)
    if not master_dir and not git_root:
        return ""
    roots = handoff_roots(master_dir, git_root)
    parts = []
    for p in active_roadmaps(master_dir, roots):
        text = read(p)
        resume = section(text, "Resume here")
        if len(resume) > RESUME_CAP:
            resume = resume[:RESUME_CAP].rsplit("\n", 1)[0] + "\n…"
        parts.append(
            f"Active roadmap: {p} (Last updated: {header(text, 'Last updated') or 'unknown'}).\n"
            "If the user's first message names a plan, explore doc or handoff path, that file is the "
            "resume point: start from it and open this roadmap only at the sections it cites. "
            "Otherwise, before acting on this initiative, read it fully and follow the roadmap skill's "
            "Resume step; do not re-read older handoffs or plans it supersedes. Update it last.\n"
            f"Resume here:\n{resume or '(empty)'}"
        )
    handoff = newest_open_handoff(roots)
    if handoff:
        parts.append(
            f"Newest open handoff: {handoff} (handoff skill). Read it only if the user resumes that thread."
        )
    due = due_reminders(master_dir)
    if due:
        parts.append("Due reminders (remind skill; show them to the user now, do not act on them):\n" + "\n".join(due))
    return "\n\n".join(parts)


def main():
    try:
        raw = sys.stdin.read() if not sys.stdin.isatty() else ""
        data = json.loads(raw) if raw.strip() else {}
        context = build(data.get("cwd") or os.getcwd())
    except Exception:
        return 0
    if context:
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": context,
            }
        }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
