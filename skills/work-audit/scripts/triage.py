#!/usr/bin/env python3
"""Light/Full audit triage verdict for work-audit (stdlib only, any host).

  triage.py --repo <path> [--repo <path> ...]
            (--range <base>..<head> | --worktree | --files <path> [<path> ...])
            [--files-root <dir>] [--base-dir <dir>]      (--files only)
            [--scope-kind session|range|plan|roadmap]   (default: session; range with --range)
            [--client-root <dir> ...]                   (repeatable; no default)
            [--json]

Sources: --range runs `git diff --numstat <base>..<head>` per repo; --worktree runs
`git diff --numstat HEAD` plus untracked files per repo (run from the repo toplevel, paths relative
to it); --files takes explicit paths (non-git work). With --base-dir, changed lines per file = added
+ removed lines (difflib) against `<base-dir>/<path relative to --files-root>` (default root: the
common path of the files); a missing base file is new (all lines count), a missing current file is
deleted (base lines count). Without --base-dir the size rule uses file count only and lines=n/a.
Binary files count as files with 0 lines. In --files mode each file path is also tested against the
client roots.

Any one Full trigger gives FULL, otherwise LIGHT: size (>= 25 files or >= 800 changed lines),
scope (more than one --repo, or --scope-kind roadmap), client (a repo under a client root),
and risky paths by category (data, auth, payments, secrets, deploy).

Output: VERDICT / REASONS / STATS lines (or --json). Exit 0 on a verdict; 2 on bad usage or git error.
"""
from __future__ import annotations

import argparse
import difflib
import json
import os
import re
import subprocess
import sys

MAX_FILES = 25
MAX_LINES = 800

RISKY = {
    "data": [r"(^|/)migrations?/", r"(^|/)schema\.", r"\.sql$", r"(^|/)prisma/", r"drizzle",
             r"(^|/)supabase/", r"\.rules$", r"(^|/)db/", r"(^|/)queries\."],
    "auth": [r"(^|/)auth(/|\.|$)", r"(^|/)login", r"middleware\.", r"(^|/)permissions?\."],
    "payments": [r"payment", r"stripe", r"checkout", r"billing"],
    "secrets": [r"(^|/)\.env", r"secret", r"credential"],
    "deploy": [r"vercel\.json$", r"netlify\.toml$", r"(^|/)\.github/workflows/", r"wrangler\.toml$",
               r"firebase\.json$", r"(^|/)Dockerfile$"],
}
RISKY_RE = {cat: [re.compile(p, re.IGNORECASE) for p in pats] for cat, pats in RISKY.items()}


class UsageError(Exception):
    pass


def git(repo: str, *args: str) -> str:
    cmd = ["git", "-C", repo, *args]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    except OSError as e:
        raise UsageError(f"{repo}: `{' '.join(cmd)}` failed: {e}")
    if proc.returncode != 0:
        raise UsageError(f"{repo}: `{' '.join(cmd)}` failed: {proc.stderr.strip()}")
    return proc.stdout


def parse_numstat(out: str) -> list[tuple[str, int]]:
    rows = []
    for line in out.splitlines():
        parts = line.split("\t", 2)
        if len(parts) != 3:
            continue
        added, deleted, path = parts
        n = 0 if added == "-" or deleted == "-" else int(added) + int(deleted)
        rows.append((path, n))
    return rows


def count_lines(path: str) -> int:
    try:
        with open(path, "rb") as f:
            data = f.read()
    except OSError:
        return 0
    if b"\0" in data:
        return 0
    return data.count(b"\n") + (1 if data and not data.endswith(b"\n") else 0)


def read_lines(path: str) -> list[str] | None:
    try:
        with open(path, "rb") as f:
            data = f.read()
    except OSError:
        return None
    if b"\0" in data:
        return []
    return data.decode("utf-8", "replace").splitlines()


def diff_lines(path: str, base: str) -> int:
    cur, old = read_lines(path), read_lines(base)
    cur, old = cur or [], old or []
    return sum(1 for d in difflib.ndiff(old, cur) if d[:2] in ("+ ", "- "))


def repo_changes(repo: str, args) -> list[tuple[str, int]]:
    if args.range:
        return parse_numstat(git(repo, "diff", "--no-renames", "--numstat", args.range))
    top = git(repo, "rev-parse", "--show-toplevel").strip()
    rows = parse_numstat(git(top, "diff", "--no-renames", "--numstat", "HEAD"))
    seen = {p for p, _ in rows}
    for path in git(top, "ls-files", "--others", "--exclude-standard", "-z").split("\0"):
        if path and path not in seen:
            rows.append((path, count_lines(os.path.join(top, path))))
    return rows


def under(path: str, root: str) -> bool:
    path, root = os.path.realpath(path), os.path.realpath(os.path.expanduser(root))
    return path == root or path.startswith(root + os.sep)


def triage(args) -> dict:
    changes: list[tuple[str, int | None]] = []
    if args.files:
        root = args.files_root or os.path.commonpath([os.path.abspath(p) for p in args.files])
        if not args.files_root and len(args.files) == 1:
            root = os.path.dirname(os.path.abspath(args.files[0]))
        for p in args.files:
            if args.base_dir:
                rel = os.path.relpath(os.path.abspath(p), os.path.abspath(root))
                changes.append((p, diff_lines(p, os.path.join(args.base_dir, rel))))
            else:
                changes.append((p, None))
    else:
        for repo in args.repo:
            changes += repo_changes(repo, args)
    files = len(changes)
    lines = None if args.files and not args.base_dir else sum(n for _, n in changes)
    scope_kind = args.scope_kind or ("range" if args.range else "session")
    reasons = []
    if files >= MAX_FILES or (lines is not None and lines >= MAX_LINES):
        shown = "n/a" if lines is None else lines
        reasons.append({"rule": "size", "detail": f"{files} files, {shown} changed lines "
                        f"(Full at >= {MAX_FILES} files or >= {MAX_LINES} lines)"})
    if len(args.repo) > 1 or scope_kind == "roadmap":
        why = f"{len(args.repo)} repos" if len(args.repo) > 1 else "roadmap scope"
        reasons.append({"rule": "scope", "detail": why})
    roots = args.client_root or []
    hits = [r for r in [*args.repo, *(args.files or [])] if any(under(r, c) for c in roots)]
    if hits:
        reasons.append({"rule": "client", "detail": ", ".join(hits)})
    for cat, regexes in RISKY_RE.items():
        paths = [p for p, _ in changes if any(rx.search(p) for rx in regexes)]
        if paths:
            reasons.append({"rule": cat, "detail": ", ".join(sorted(set(paths)))})
    return {"verdict": "FULL" if reasons else "LIGHT", "reasons": reasons,
            "stats": {"repos": len(args.repo), "files": files, "lines": "n/a" if lines is None else lines, "scope": scope_kind}}


def parse(argv):
    p = argparse.ArgumentParser(prog="triage.py", description="Light/Full audit triage verdict")
    p.add_argument("--repo", action="append", default=[])
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--range")
    src.add_argument("--worktree", action="store_true")
    src.add_argument("--files", nargs="+")
    p.add_argument("--files-root")
    p.add_argument("--base-dir")
    p.add_argument("--scope-kind", choices=["session", "range", "plan", "roadmap"])
    p.add_argument("--client-root", action="append")
    p.add_argument("--json", action="store_true")
    args = p.parse_args(argv)
    if (args.range or args.worktree) and not args.repo:
        p.error("--range and --worktree need at least one --repo")
    if (args.files_root or args.base_dir) and not args.files:
        p.error("--files-root and --base-dir apply to --files only")
    return args


def main(argv=None) -> int:
    try:
        args = parse(argv)
        result = triage(args)
    except UsageError as e:
        print(f"triage: {e}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(result))
    else:
        reasons = "; ".join(f"{r['rule']}: {r['detail']}" for r in result["reasons"]) \
            or "none — no Full trigger"
        s = result["stats"]
        print(f"VERDICT: {result['verdict']}")
        print(f"REASONS: {reasons}")
        print(f"STATS: repos={s['repos']} files={s['files']} lines={s['lines']} scope={s['scope']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
