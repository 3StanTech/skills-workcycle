#!/usr/bin/env python3
"""SessionStart: surface the project's active roadmap (and newest open handoff).

Finds the project from the session cwd (nearest master.md and/or git root), then:
  0. urgent stops: any doc under <handoffs-root> with an `## Interrupted` heading (first)
  1. roadmaps listed under `## Active roadmaps` in master.md (not marked Closed)
  2. <handoffs-root>/*/ROADMAP.md (roadmap-*/ROADMAP.md without a workcycle root) whose header
     says `Status: Active`
  3. the newest open handoff in <handoffs-root>/ or <handoffs-root>/*/handoffs/ (not Superseded, not Done)
  4. due reminders in master.md `## Reminders` (when: next session, or a passed date)
  5. one line when git is ahead of the docs (uncommitted changes, or HEAD newer than the
     active roadmap's Last updated)

<handoffs-root> follows the handoff skill's Paths: with a `## Workcycle root` in
~/.agents/local/workcycle.md it is <root>/<name> (the overrides table, else the basename of the
master.md folder, else of the git root, else General when no project is found); without one it
is <repo-parent>/<repo-name>-handoffs/ for a git repo, or <project>/handoffs/ for a non-git
project folder.

Emits Claude Code / Codex SessionStart JSON with additionalContext, or nothing when
the project has neither. Read-only, no network, never blocks: any error exits 0.
"""

import datetime
import glob
import json
import os
import re
import subprocess
import sys

HOME = os.path.expanduser("~")
RESUME_CAP = 1500
CONFIG = os.path.join(HOME, ".agents", "local", "workcycle.md")
INTERRUPTED = re.compile(r"^#{2,6} Interrupted", re.M)
SKIP_DIRS = {"runs", "_archive", "mocks", "node_modules", ".git"}  # a mocks/README.md is still read
DATE = re.compile(r"\d{4}-\d\d-\d\d")
HANDOFF_NAME = re.compile(r"^\d{4}-\d\d-\d\d-.+\.md$")
PATH_IN_LINE = re.compile(r"`([^`]+\.md)`|:\s*((?:~|/)[^`]*?\.md|\S+\.md)\s*$")  # absolute paths may hold spaces
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


def load_config():
    """(root, overrides) from workcycle.md; root None means the old -handoffs rule.
    Headings must match exactly (`## Workcycle root (disabled)` is not the setting); a blank
    root counts as unset, and override rows without both a path and a folder are skipped."""
    text = read(CONFIG)
    m = re.search(r"`([^`]*)`", section(text, "Workcycle root", exact=True))
    value = m.group(1).strip() if m else ""
    root = os.path.realpath(os.path.expanduser(value)) if value else None
    overrides = []
    for line in section(text, "Workcycle folders (overrides)", exact=True).splitlines():
        cells = [c.strip().strip("`").strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 2 or not cells[0] or set(cells[0]) <= set("-: ") or cells[0].lower() == "project path":
            continue
        name = cells[1].strip("/").strip()
        if not name:
            continue
        overrides.append((os.path.realpath(os.path.expanduser(cells[0])), name))
    overrides.sort(key=lambda o: len(o[0]), reverse=True)
    return root, overrides


def workcycle_folder(cwd, master_dir, git_root, root, overrides):
    real = os.path.realpath(cwd)
    for path, name in overrides:
        if real == path or real.startswith(path + os.sep):
            return os.path.join(root, name)
    base = master_dir or git_root
    return os.path.join(root, os.path.basename(base)) if base else os.path.join(root, "General")


def handoff_roots(master_dir, git_root, cwd=None, config=(None, [])):
    root, overrides = config
    if root:
        folder = workcycle_folder(cwd or master_dir or git_root, master_dir, git_root, root, overrides)
        return [folder] if os.path.isdir(folder) else []
    roots = []
    if git_root:
        roots.append(os.path.join(os.path.dirname(git_root), os.path.basename(git_root) + "-handoffs"))
    if master_dir and master_dir != git_root:
        roots.append(os.path.join(master_dir, "handoffs"))
    return [r for r in roots if os.path.isdir(r)]


def section(text, name, exact=False):
    tail = r"[ \t]*\n" if exact else r"[^\n]*\n"
    m = re.search(rf"^## {re.escape(name)}{tail}(.*?)(?=^## |\Z)", text, re.M | re.S)
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


def active_roadmaps(master_dir, roots, folder_glob="*"):
    found = []
    if master_dir:
        for line in section(read(os.path.join(master_dir, "master.md")), "Active roadmaps").splitlines():
            if "closed" in line.lower():
                continue
            m = PATH_IN_LINE.search(line)
            if m:
                p = os.path.expanduser(m.group(1) or m.group(2))
                found.append(p if os.path.isabs(p) else os.path.join(master_dir, p))
    for root in roots:
        found.extend(sorted(glob.glob(os.path.join(glob.escape(root), folder_glob, "ROADMAP.md"))))
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
        candidates = [os.path.join(root, n) for n in os.listdir(root)]
        candidates += glob.glob(os.path.join(glob.escape(root), "*", "handoffs", "*.md"))
        for p in candidates:
            name = os.path.basename(p)
            if not HANDOFF_NAME.match(name) or not os.path.isfile(p):
                continue
            head = read(p)[:1500]
            if "superseded" in head.lower() or header(head, "Status").lower().startswith("done"):
                continue
            if best is None or name > os.path.basename(best):
                best = p
    return best


def urgent_stops(roots, limit=2000):
    hits, seen = [], 0
    for root in roots:
        base_depth = root.rstrip(os.sep).count(os.sep)
        for d, dirs, files in os.walk(root):
            # an urgent stop in a mock round lives in the owning mocks/README.md (handoff skill)
            paths = [os.path.join(d, f) for f in files if f.endswith(".md")]
            if "mocks" in dirs:
                paths.append(os.path.join(d, "mocks", "README.md"))
            dirs[:] = [x for x in dirs if x not in SKIP_DIRS and not x.startswith(".")]
            if d.count(os.sep) - base_depth >= 4:
                dirs[:] = []
            for p in paths:
                if not os.path.isfile(p):
                    continue
                seen += 1
                if seen > limit:
                    return hits
                if INTERRUPTED.search(read(p)[:65536]):
                    hits.append(p)
    return hits


def git_out(git_root, *args):
    r = subprocess.run(["git", "--no-optional-locks", "-C", git_root, *args],
                       capture_output=True, text=True, timeout=2)
    return r.stdout.strip() if r.returncode == 0 else ""


def git_ahead(git_root, roadmap_paths):
    if not git_root:
        return ""
    try:
        dirty = len([l for l in git_out(git_root, "status", "--porcelain").splitlines() if l.strip()])
        head = git_out(git_root, "log", "-1", "--format=%cs %h")
    except (OSError, subprocess.TimeoutExpired):
        return ""
    newer = False
    if head and roadmap_paths:
        m = DATE.search(header(read(roadmap_paths[0]), "Last updated"))
        newer = bool(m) and head.split()[0] > m.group(0)
    if not dirty and not newer:
        return ""
    bits = []
    if dirty:
        bits.append(f"{dirty} uncommitted change(s)")
    if newer:
        bits.append(f"HEAD {head.split()[1]} ({head.split()[0]}) is newer than the roadmap's Last updated")
    return "Git is ahead of the docs: " + "; ".join(bits) + ". Check before trusting the docs' state."


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
    config = load_config()
    if not master_dir and not git_root and not config[0]:
        return ""  # no project and no workcycle root: nothing to look in (General needs a root)
    roots = handoff_roots(master_dir, git_root, cwd, config)
    parts = []
    stops = urgent_stops(roots)
    if stops:
        parts.append("URGENT STOP (handoff skill §4): resume from " + ", ".join(stops)
                     + " first; run its Unverified (urgent stop) steps before anything else.")
    roadmaps = active_roadmaps(master_dir, roots, "*" if config[0] else "roadmap-*")
    for p in roadmaps:
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
    if parts:
        ahead = git_ahead(git_root, roadmaps)
        if ahead:
            parts.append(ahead)
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
