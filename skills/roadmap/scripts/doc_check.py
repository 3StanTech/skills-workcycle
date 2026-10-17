#!/usr/bin/env python3
"""Read-only checker for roadmap and handoff documents.

Finds the drift that makes a continuity doc lie to the next session:

  header    missing Status / Last updated, or Last updated older than the
            newest session-log date or the repo's newest commit
  sections  required headings missing
  resume    Resume here / Next actions empty or longer than 5 items
  size      doc over its byte budget (roadmap 16 KB, handoff 8 KB)
  secret    something that looks like a credential (always an error)
  path      a backticked ~/, /Users/ or doc-relative path that does not exist
  plan      a phase row whose status disagrees with its plan's **Status:**
  phase     readiness notes kept for a phase that already shipped
  log       session log not newest-first
  sha       a backticked commit SHA the repo does not know (needs --repo)
  decision  a Locked-decision ID (D<n>) used twice
  interrupt an urgent-stop "Interrupted" block (any heading level) with no
            next action or no `resume from` paste line; the block and its
            "Unverified (urgent stop)" subsection are otherwise optional

Prints one JSON object to stdout ({file, kind, errors, warnings, info}).
Exit 0 when there are no errors, 1 when there are errors, 2 on bad usage.
"""

import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys

BUDGET = {"roadmap": 16 * 1024, "handoff": 8 * 1024}

REQUIRED = {
    "roadmap": [
        "Resume here",
        "North star",
        "Locked decisions",
        "Guarantees",
        "Phase status",
        "Environments",
        "Session log",
    ],
    "handoff": ["Goal", "Next actions", "Current state"],
}

SECRET_PATTERNS = [
    (r"postgres(?:ql)?://[^\s:`]+:[^\s@`]+@", "a database URL with a password"),
    (r"mysql://[^\s:`]+:[^\s@`]+@", "a database URL with a password"),
    (r"\bsk-[A-Za-z0-9_-]{20,}", "an API key (sk-...)"),
    (r"\bgh[pousr]_[A-Za-z0-9]{30,}", "a GitHub token"),
    (r"\bxox[abpr]-[A-Za-z0-9-]{10,}", "a Slack token"),
    (r"\bAKIA[0-9A-Z]{16}\b", "an AWS access key"),
    (r"-----BEGIN [A-Z ]*PRIVATE KEY-----", "a private key"),
    (r"\beyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.", "a JWT"),
    (
        r"(?i)\b(?:password|passwd|secret|api[_-]?key|token)\s*[:=]\s*[\"']?(?![<`~/.])[A-Za-z0-9+/_\-]{12,}",
        "an inline credential",
    ),
]

SHIPPED = re.compile(r"\b(shipped|closed|live|done|implemented|dropped)\b", re.I)
UNSHIPPED = re.compile(r"\b(not started|planned|in progress|blocked)\b", re.I)
DATE = re.compile(r"\b(20\d\d-\d\d-\d\d)\b")
BACKTICK = re.compile(r"`([^`\n]+)`")
SHA = re.compile(r"^[0-9a-f]{7,12}$")


def parse_args():
    p = argparse.ArgumentParser(
        description="Check a roadmap or handoff Markdown doc for drift. Read-only.",
    )
    p.add_argument("file", help="path to ROADMAP.md or a handoff .md")
    p.add_argument(
        "--kind",
        choices=["auto", "roadmap", "handoff"],
        default="auto",
        help="doc kind (default: auto, from the filename and headings)",
    )
    p.add_argument(
        "--repo",
        help="git repo the doc describes; enables SHA and newest-commit checks",
    )
    p.add_argument("--max-kb", type=int, help="override the size budget in KB")
    p.add_argument(
        "--text", action="store_true", help="print a human summary instead of JSON"
    )
    return p.parse_args()


def sections(lines):
    """Map lowercase heading text -> (start, end) line indexes for ## headings."""
    heads = [(i, l[3:].strip()) for i, l in enumerate(lines) if l.startswith("## ")]
    out = {}
    for n, (i, title) in enumerate(heads):
        end = heads[n + 1][0] if n + 1 < len(heads) else len(lines)
        out[title.lower()] = (i, end)
    return out


def find_section(secs, prefix):
    prefix = prefix.lower()
    for title, span in secs.items():
        if title.startswith(prefix):
            return title, span
    return None, None


def header_field(text, name):
    m = re.search(rf"^\**{name}:?\**:?\s*(.+)$", text, re.I | re.M)
    return m.group(1).strip() if m else None


def git(repo, *args):
    try:
        r = subprocess.run(
            ["git", "-C", repo, *args], capture_output=True, text=True, timeout=20
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    return r.stdout.strip() if r.returncode == 0 else None


def main():
    a = parse_args()
    path = os.path.abspath(os.path.expanduser(a.file))
    if not os.path.isfile(path):
        print(f"error: no such file: {a.file}", file=sys.stderr)
        return 2
    with open(path, encoding="utf-8") as f:
        text = f.read()
    lines = text.splitlines()
    secs = sections(lines)
    base = os.path.dirname(path)

    kind = a.kind
    if kind == "auto":
        name = os.path.basename(path).lower()
        kind = "roadmap" if "roadmap" in name or "phase status" in secs else "handoff"

    errors, warnings, info = [], [], []

    # header
    status = header_field(text, "Status")
    updated = header_field(text, "Last updated")
    if not status:
        warnings.append("header: no 'Status:' line")
    else:
        info.append(f"status: {status}")
    updated_date = None
    if updated:
        m = DATE.search(updated)
        updated_date = m.group(1) if m else None
    if not updated_date:
        warnings.append("header: no 'Last updated: YYYY-MM-DD' line")

    # required sections
    for req in REQUIRED[kind]:
        if find_section(secs, req)[0] is None:
            warnings.append(f"sections: missing '## {req}'")

    # resume list length
    resume_name = "Resume here" if kind == "roadmap" else "Next actions"
    title, span = find_section(secs, resume_name)
    if span:
        items = [l for l in lines[span[0] + 1 : span[1]] if re.match(r"^\d+\.\s", l)]
        if not items:
            warnings.append(f"resume: '{title}' has no numbered actions")
        elif len(items) > 5:
            warnings.append(
                f"resume: '{title}' has {len(items)} actions; keep 2 to 5 and move the rest"
            )

    # size
    budget = (a.max_kb * 1024) if a.max_kb else BUDGET[kind]
    size = len(text.encode("utf-8"))
    info.append(f"size: {size} bytes (budget {budget})")
    if size > budget:
        fix = (
            "compact closed phases and prune the session log"
            if kind == "roadmap"
            else "cut history and keep only what the next session needs"
        )
        warnings.append(f"size: {size} bytes over the {budget}-byte budget; {fix}")

    # secrets
    for n, line in enumerate(lines, 1):
        for pat, label in SECRET_PATTERNS:
            if re.search(pat, line):
                errors.append(f"secret: line {n} looks like {label}; store a path instead")
                break

    # paths
    seen = set()
    for n, line in enumerate(lines, 1):
        for tok in BACKTICK.findall(line):
            tok = tok.strip()
            if tok in seen or " " in tok and not tok.startswith(("~/", "/")):
                continue
            if any(c in tok for c in "<>*…$|{}"):
                continue
            if tok.startswith(("~/", "/Users/")):
                cand = os.path.expanduser(tok.rstrip(".,;:)"))
            elif re.match(r"^(plans|runs|handoffs)/\S+$", tok):
                cand = os.path.join(base, tok)
            else:
                continue
            seen.add(tok)
            cand = re.sub(r":\d+(-\d+)?$", "", cand)
            if not os.path.exists(cand):
                warnings.append(f"path: line {n} `{tok}` does not exist")

    # phase table vs plan status, and shipped phases still carrying readiness notes
    shipped_phases = set()
    title, span = find_section(secs, "Phase status")
    if span:
        for line in lines[span[0] + 1 : span[1]]:
            if not line.startswith("|") or set(line) <= set("|-: "):
                continue
            cells = [c.strip() for c in line.strip("|").split("|")]
            if len(cells) < 2 or cells[0].lower() == "phase":
                continue
            m = re.match(r"\**\s*(\d+)", cells[0])
            row_status = cells[1]
            if m and SHIPPED.search(row_status) and not UNSHIPPED.search(row_status):
                shipped_phases.add(m.group(1))
            for tok in BACKTICK.findall(line):
                if not re.match(r"^plans/\S+\.md$", tok):
                    continue
                plan = os.path.join(base, tok)
                if not os.path.isfile(plan):
                    continue
                with open(plan, encoding="utf-8") as pf:
                    ps = header_field(pf.read(4000), "Status") or ""
                info.append(f"plan: {tok} Status {ps or 'unknown'}")
                if re.search(r"implemented", ps, re.I) and not SHIPPED.search(row_status):
                    warnings.append(
                        f"plan: {tok} says Implemented but its phase row says '{row_status}'"
                    )
                if re.search(r"draft|ready", ps, re.I) and SHIPPED.search(row_status):
                    warnings.append(
                        f"plan: {tok} says {ps} but its phase row says '{row_status}'"
                    )
    for title in secs:
        m = re.match(r"phase (\d+).*readiness", title)
        if m and m.group(1) in shipped_phases:
            warnings.append(
                f"phase: '## {title}' kept after Phase {m.group(1)} shipped; delete it"
                " (the plan consumed it)"
            )

    # decision IDs are unique
    title, span = find_section(secs, "Locked decisions")
    if span:
        ids = re.findall(r"^\s*-\s+\**(D\d+)\b", "\n".join(lines[span[0] + 1 : span[1]]), re.M)
        dupes = sorted({i for i in ids if ids.count(i) > 1}, key=lambda x: int(x[1:]))
        if dupes:
            warnings.append(f"decision: IDs used more than once: {', '.join(dupes)}")
        if ids:
            info.append(f"decisions: {len(ids)} (highest {max(ids, key=lambda x: int(x[1:]))})")

    # urgent-stop blocks must let the resume session start
    heads = [
        (i, len(m.group(1)), m.group(2))
        for i, l in enumerate(lines)
        if (m := re.match(r"^(#{2,6})\s+(.+?)\s*$", l))
    ]
    for n, (i, level, title) in enumerate(heads):
        if not title.lower().startswith("interrupted"):
            continue
        end = next((j for j, lv, _ in heads[n + 1 :] if lv <= level), len(lines))
        block = "\n".join(lines[i + 1 : end])
        info.append(f"interrupt: line {i + 1} '{title}'")
        if not re.search(r"(?im)^[-*\s]*\**next action\**:\**[ \t]*[^\s*]", block):
            warnings.append(f"interrupt: line {i + 1} '{title}' has no 'Next action:' line")
        if not re.search(r"(?i)resume from\s", block):
            warnings.append(
                f"interrupt: line {i + 1} '{title}' has no paste line (`resume from <path>`)"
            )

    # session log order and freshness
    title, span = find_section(secs, "Session log")
    newest_log = None
    if span:
        dates = []
        for line in lines[span[0] + 1 : span[1]]:
            if line.lstrip().startswith(("-", "*")):
                m = DATE.search(line)
                if m:
                    dates.append(m.group(1))
        if dates:
            newest_log = max(dates)
            if dates != sorted(dates, reverse=True):
                warnings.append("log: session log is not newest-first")
    if updated_date and newest_log and newest_log > updated_date:
        warnings.append(
            f"header: Last updated {updated_date} is older than the newest log entry {newest_log}"
        )

    # repo checks
    if a.repo:
        repo = os.path.abspath(os.path.expanduser(a.repo))
        head = git(repo, "log", "-1", "--format=%h %cs")
        if head is None:
            warnings.append(f"repo: {a.repo} is not a readable git repo; SHA checks skipped")
        else:
            h, hdate = head.split()
            info.append(f"repo HEAD: {h} ({hdate})")
            if updated_date and hdate > updated_date:
                warnings.append(
                    f"repo: HEAD {h} is dated {hdate}, after Last updated {updated_date};"
                    " the doc may be behind Git"
                )
            shas = {t for t in BACKTICK.findall(text) if SHA.match(t)}
            for s in sorted(shas):
                if git(repo, "cat-file", "-e", f"{s}^{{commit}}") is None:
                    warnings.append(f"sha: `{s}` is not a commit in {a.repo}")
            if shas and not any(h.startswith(s) or s.startswith(h) for s in shas):
                info.append(f"repo HEAD {h} is not mentioned in the doc")

    # a closed roadmap is history: compaction warnings no longer apply
    if kind == "roadmap" and status and status.lower().startswith("closed"):
        moot = ("size:", "phase:", "log:", "resume:")
        info.extend(f"(closed, not enforced) {w}" for w in warnings if w.startswith(moot))
        warnings = [w for w in warnings if not w.startswith(moot)]

    result = {
        "file": path,
        "kind": kind,
        "errors": errors,
        "warnings": warnings,
        "info": info,
    }
    if a.text:
        print(f"{kind}: {path}")
        for label, items in (("ERROR", errors), ("WARN", warnings), ("info", info)):
            for item in items:
                print(f"  {label:5} {item}")
        if not errors and not warnings:
            print("  clean")
    else:
        print(json.dumps(result, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
