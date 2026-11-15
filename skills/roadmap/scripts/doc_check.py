#!/usr/bin/env python3
"""Read-only checker for stage and continuity documents.

Kinds: explore (explore and explore-design docs), plan, pageplan (a landing-page
plan), mocks (a mocks folder
README), findings (a work-audit findings file), roadmap, handoff. --kind picks
one; omitted, the kind is detected from the title line, filename and headings.

Finds the drift that makes a doc lie to the next session:

  header    missing Status (all kinds but mocks); roadmap and handoff also need
            Last updated, not older than the newest session-log date or the
            repo's newest commit
  sections  required headings missing
  resume    Resume here / Next actions empty or longer than 5 items (roadmap,
            handoff)
  size      doc over its byte budget (roadmap 16 KB, handoff 8 KB, explore 20 KB,
            plan 40 KB, page plan 20 KB, findings 16 KB, mocks 16 KB)
  secret    something that looks like a credential (always an error)
  path      a backticked ~/, /Users/ or doc-relative path that does not exist;
            a line marked "(created by Step N)" is skipped
  starthere Start here lacks the goal, a dated Verified line, Read first, or a
            Next line with a backticked command (explore, plan, pageplan, mocks,
            findings)
  scratch   a session-scratchpad, /tmp or /private/tmp path (all kinds)
  stamp     no "cold-start pass YYYY-MM-DD" (all kinds but handoffs with an
            Interrupted block)
  prime     Start here does not say no /prime is needed (explore, plan, pageplan, mocks,
            findings)
  plan      a phase row whose status disagrees with its plan's **Status:**
  phase     readiness notes kept for a phase that already shipped
  log       session log not newest-first
  sha       a backticked commit SHA the repo does not know (needs --repo)
  handoff   the next stage is /create-plan (Start here Next, or the first
            command in a roadmap's Resume here) but the repo's HEAD is not a
            backticked SHA on a Verified line (roadmap: in Environments)
            (needs --repo)
  decision  a Locked-decision ID (D<n>) used twice
  interrupt an urgent-stop "Interrupted" block (any heading level) with no
            next action or no `resume from` paste line; the block and its
            "Unverified (urgent stop)" subsection are otherwise optional
  selfclose a Closed findings file whose fixes ran (any '## Fix…' section but
            a Fix queue holds more than a bare "None." / "N/A" / "No fixes") or
            that has a '## Re-check', unless: the re-check sections have a
            '### Verdicts' list ('<id> · <verdict>', the verdict as the first
            word, any bullet style); every
            PARTIAL, NOT FIXED or NEW id has a '### Leftovers' line; and every
            Leftovers line is FIXED with a Fixed by tier (not a role such as
            session or dispatcher) and a Verified by that is
            neither the fixer (same text, a word-prefix of it, or session /
            dispatcher / fixer / implementer / self), or is accepted open by the
            owner with a date. Prose is never read. Always an error; files dated
            before SELFCLOSE_FROM and those in SELFCLOSE_EXEMPT are skipped
  restatement a mocks README with a line naming the restatement followed, in
            the same cell or the next, by an affirmative decision (Matches,
            Confirmed, Approved, Agreed, Yes; the label "Stage 1 restatement
            confirmed" always counts), but no non-empty restatement.md beside
            it. "Not confirmed", "pending" and "Mostly, with corrections" do not
            count

A Closed (or Done) doc is history: starthere, prime and stamp are not enforced,
nor are a closed roadmap's size, phase, log and resume checks, nor a closed mocks
README's restatement check. selfclose applies only to Closed findings files.

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

KINDS = ["explore", "plan", "pageplan", "mocks", "findings", "roadmap", "handoff"]
STAGE = {"explore", "plan", "pageplan", "mocks", "findings"}  # docs with a Start here block

BUDGET = {
    "roadmap": 16 * 1024,
    "handoff": 8 * 1024,
    "explore": 20 * 1024,
    "plan": 40 * 1024,
    "pageplan": 20 * 1024,
    "findings": 16 * 1024,
    "mocks": 16 * 1024,
}

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
    "explore": ["Confirmed restatement", "Discovery Notes"],
    "plan": ["Design Decisions", "Step-by-Step Tasks", "Success Criteria"],
    "findings": ["Findings", "Open items"],
    "pageplan": [],
    "mocks": [],
}

SCRATCH = re.compile(
    r"(?:(?<![\w.~-])(?:/private)?/tmp/[^\s`'\")]+|/var/folders/\S+|\S*/scratchpad(?:/\S*)?)"
)
STAMP = re.compile(r"(?i)cold-start pass:?\s+20\d\d-\d\d-\d\d")

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

# selfclose: findings files dated before the rule, plus two archived same-day files
# that predate it and were later verified by their auditor, are history.
SELFCLOSE_FROM = "2026-11-15"
SELFCLOSE_EXEMPT = {
    "2026-11-14-design-motion-phase-1.md",
    "2026-11-15-design-motion-phase-2.md",
}
VERDICT = re.compile(r"^(NOT FIXED|FIXED|PARTIAL|NEW)\b", re.I)  # first word after '·'
# the whole Fixes section, Markdown emphasis removed, is only a no-fixes marker
NO_FIXES = re.compile(r"(?i)(?:none|n/a|no fix(?:es)?(?: needed| applied)?)[.!]?")
SELF_NAMES = {"session", "this session", "dispatcher", "fixer", "implementer", "self"}
# a line naming the restatement, then (same cell or the next) an affirmative decision
RESTATED = re.compile(
    r"(?i)\brestatement\b[\s:*_`|()\u2013\u2014-]*(?:matches|matched|confirmed|approved|agreed|yes)\b"
)


def parse_args():
    p = argparse.ArgumentParser(
        description="Check a stage or continuity Markdown doc for drift. Read-only.",
    )
    p.add_argument(
        "file", help="path to an explore doc, plan, mocks README, findings file, ROADMAP.md or handoff"
    )
    p.add_argument(
        "--kind",
        choices=["auto", *KINDS],
        default="auto",
        help="doc kind (default: auto, from the title line, filename and headings)",
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


def detect_kind(path, text, secs):
    name = os.path.basename(path).lower()
    parent = os.path.basename(os.path.dirname(path)).lower()
    title = next((l for l in text.splitlines() if l.startswith("# ")), "").lower()
    if title.startswith("# explore"):
        return "explore"
    if title.startswith("# page plan"):
        return "pageplan"
    if title.startswith("# plan"):
        return "plan"
    if title.startswith("# handoff"):
        return "handoff"
    # findings first: an explicit findings title, or any doc under audits/ other than
    # a ROADMAP.md, wins over the broad "roadmap" filename heuristic below
    in_audits = "audits" in os.path.normpath(path).lower().split(os.sep)
    if title.startswith(("# work-audit", "# findings")) or (in_audits and name != "roadmap.md"):
        return "findings"
    if "roadmap" in name or "phase status" in secs:
        return "roadmap"
    if "audit" in title or ("findings" in secs and "open items" in secs):
        return "findings"
    if parent.endswith("-mocks") or "mocks" in title:
        return "mocks"
    return "handoff"


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
        kind = detect_kind(path, text, secs)

    errors, warnings, info = [], [], []
    continuity = kind in ("roadmap", "handoff")

    # header
    status = header_field(text, "Status")
    updated = header_field(text, "Last updated")
    if not status:
        if kind != "mocks":
            warnings.append("header: no 'Status:' line")
    else:
        info.append(f"status: {status}")
    closed = bool(status and re.match(r"\W*(closed|done)\b", status, re.I))
    updated_date = None
    if updated:
        m = DATE.search(updated)
        updated_date = m.group(1) if m else None
    if not updated_date and continuity:
        warnings.append("header: no 'Last updated: YYYY-MM-DD' line")

    # required sections
    for req in REQUIRED[kind]:
        if find_section(secs, req)[0] is None:
            warnings.append(f"sections: missing '## {req}'")

    # resume list length
    resume_name = "Resume here" if kind == "roadmap" else "Next actions"
    title, span = find_section(secs, resume_name)
    if span and continuity:
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
        if re.search(r"(?i)\(created by\b", line):
            continue
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
                # a doc inside plans/ (or runs/, handoffs/) anchors to its parent folder
                if os.path.basename(base) in ("plans", "runs", "handoffs"):
                    up = os.path.join(os.path.dirname(base), tok)
                    if os.path.exists(re.sub(r":\d+(-\d+)?$", "", up)):
                        cand = up
            else:
                continue
            seen.add(tok)
            cand = re.sub(r":\d+(-\d+)?$", "", cand)
            if not os.path.exists(cand):
                warnings.append(f"path: line {n} `{tok}` does not exist")

    # scratchpad and temp paths vanish with the session
    for n, line in enumerate(lines, 1):
        m = SCRATCH.search(line)
        if m:
            warnings.append(
                f"scratch: line {n} `{m.group(0).strip('`')}` is a session or temp path;"
                " move what the next stage needs beside the doc"
            )

    # Start here: what a cold session needs to start the next stage
    title, span = find_section(secs, "Start here")
    start = "\n".join(lines[span[0] + 1 : span[1]]) if span else ""
    if kind in STAGE:
        if not span:
            warnings.append("starthere: no '## Start here' section")
        else:
            bullet = r"(?im)^\s*[-*]\s+\**\s*"
            if not re.search(bullet + r"goal", start):
                warnings.append("starthere: no Goal line")
            if not re.search(bullet + r"verified\b[^\n]*20\d\d-\d\d-\d\d", start):
                warnings.append("starthere: no dated 'Verified YYYY-MM-DD' line")
            if not re.search(bullet + r"read first", start):
                warnings.append("starthere: no 'Read first' line")
            nxt = re.search(bullet + r"next\b[^\n]*", start)
            if not nxt:
                warnings.append("starthere: no 'Next' line")
            elif not BACKTICK.search(nxt.group(0)):
                warnings.append("starthere: the 'Next' line has no backticked command to paste")
            if not re.search(r"(?i)\bno\b[\s`*]*/prime\b", start):
                warnings.append(
                    "prime: Start here does not say no `/prime` (or `/handoff`) is needed"
                )

    # cold-start stamp
    urgent = any(re.match(r"^#{2,6}\s+interrupted", l, re.I) for l in lines)
    if not (kind == "handoff" and urgent):
        m = STAMP.search(text)
        if m:
            info.append(f"stamp: {m.group(0)}")
        else:
            warnings.append(
                "stamp: no 'cold-start pass YYYY-MM-DD'; run the cold-start gate"
                " (handoff/references/cold-start-gate.md)"
            )

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

    # a Closed audit whose fixes were re-checked must show who else verified each leftover
    if kind == "findings" and closed:
        name = os.path.basename(path)
        fdate = re.match(r"(20\d\d-\d\d-\d\d)", name)
        # every section that records fixes (a "Fix queue" is only a plan) and every re-check
        # (scanned directly: a repeated heading must not hide an earlier section)
        h2 = [i for i, l in enumerate(lines) if l.startswith("## ")] + [len(lines)]
        parts = [(lines[a][3:].strip().lower(), lines[a + 1 : b]) for a, b in zip(h2, h2[1:])]
        fix_parts = [p for t, p in parts if t.startswith("fix") and not t.startswith("fix queue")]
        re_parts = [(t, p) for t, p in parts if re.match(r"re-?check", t)]

        def records_fixes(part):
            """A fixes section records repairs unless it is empty or a bare no-fixes marker."""
            text = "\n".join(part)
            marker = re.sub(r"[*_`]", "", re.sub(r"(?m)^\s*(?:(?:[-*+>]|\d+[.)])\s*)+", "", text))
            marker = re.sub(r"\s+", " ", marker).strip()
            return bool(marker) and not NO_FIXES.fullmatch(marker)

        # each section is classified on its own: two clean sections are still clean
        fixes_ran = any(records_fixes(p) for p in fix_parts)
        if name in SELFCLOSE_EXEMPT or (fdate and fdate.group(1) < SELFCLOSE_FROM):
            info.append(f"selfclose: {name} predates the rule ({SELFCLOSE_FROM}); not checked")
        elif fixes_ran or re_parts:
            body = [l for t, p in re_parts for l in [f"## {t}", *p]]
            bullet = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+(?=\S)")

            def block(heading):
                """Bullet lines under every '### <heading>' in the re-check sections."""
                out, inside = [], False
                for l in body:
                    if l.startswith("#"):
                        inside = bool(re.match(rf"(?i)^###\s+{heading}\b", l))
                    elif inside and bullet.match(l):
                        out.append([f.strip(" *`") for f in bullet.sub("", l).strip().split("·")])
                return out

            norm = lambda v: re.sub(r"\s+", " ", v.strip(" *`")).lower()
            verdicts, left = block("verdicts"), block("leftovers")
            if not verdicts:
                errors.append(
                    "selfclose: fixes or a re-check ran but '## Re-check' has no '### Verdicts' list"
                    " (one line per re-checked item: '<id> · <verdict>')"
                )
            failed = []
            for f in verdicts:
                m = VERDICT.match(f[1]) if len(f) > 1 else None
                if not m:
                    errors.append(f"selfclose: verdict line '{' · '.join(f)[:60]}' names no verdict")
                elif m.group(1).upper() != "FIXED":
                    failed.append(norm(f[0]))
            have = {norm(f[0]) for f in left}
            missing = [i for i in failed if i not in have]
            if missing:
                errors.append("selfclose: verdicts with no Leftovers line: " + ", ".join(missing))
            for f in left:
                line = " · ".join(f)
                label = line[:60]
                if re.search(r"(?i)accepted open by owner\s+20\d\d-\d\d-\d\d", line):
                    continue
                field = lambda k: next(
                    (norm(x.split(":", 1)[1]) for x in f if re.match(rf"(?i){k}\s*:", x)), ""
                )
                fixer, ver = field("fixed by"), field("verified by")
                if fixer in ("", "none"):
                    errors.append(f"selfclose: leftover '{label}' has no Fixed by")
                elif fixer in SELF_NAMES:
                    errors.append(
                        f"selfclose: leftover '{label}' has Fixed by '{fixer}'; name the"
                        " fixer's tier so it can be compared with the verifier"
                    )
                if ver in ("", "none"):
                    errors.append(f"selfclose: leftover '{label}' has no Verified by")
                elif ver in SELF_NAMES or (
                    fixer and (ver == fixer or ver.startswith(fixer + " ") or fixer.startswith(ver + " "))
                ):
                    errors.append(
                        f"selfclose: leftover '{label}' was verified by its fixer; the audit"
                        " stays Open until the auditor or an owner-named reviewer verifies it"
                    )
                if norm(f[-1]) != "fixed":
                    errors.append(
                        f"selfclose: leftover '{label}' is not FIXED or accepted open by the"
                        " owner, so the audit cannot be Closed"
                    )

    # a confirmed restatement must survive the session that confirmed it
    if kind == "mocks" and any(RESTATED.search(l) for l in lines):
        rpath = os.path.join(base, "restatement.md")
        empty = True
        if os.path.isfile(rpath):
            with open(rpath, encoding="utf-8") as rf:
                empty = not rf.read().strip()
        if empty:
            warnings.append(
                "restatement: the gate log records a confirmed restatement but"
                " restatement.md is missing or empty beside the README"
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
            def has_head(s):
                # only backticked SHAs count as commit evidence, never hex-looking prose
                return any(
                    re.fullmatch(r"[0-9a-f]{7,40}", x) and (h.startswith(x) or x.startswith(h))
                    for x in BACKTICK.findall(s)
                )

            # the next stage is create-plan: its Verified HEAD must be current
            plan_next = None
            if kind in STAGE:
                nxt = re.search(r"(?im)^\s*[-*]\s+\**\s*next\b[^\n]*", start)
                if nxt and "/create-plan" in nxt.group(0):
                    ver = re.findall(r"(?im)^\s*[-*]\s+\**\s*verified\b[^\n]*", start)
                    plan_next = has_head("\n".join(ver))
            elif kind == "roadmap":
                _, rspan = find_section(secs, "Resume here")
                acts = [l for l in lines[rspan[0] + 1 : rspan[1]] if re.match(r"^\d+\.\s", l)] if rspan else []
                # the first slash command in the first action that has one
                cmds = [c for l in acts for c in BACKTICK.findall(l) if c.startswith("/")]
                cmd = cmds[0] if cmds else ""
                if cmd.startswith("/create-plan"):
                    _, espan = find_section(secs, "Environments")
                    env = "\n".join(lines[espan[0] + 1 : espan[1]]) if espan else ""
                    plan_next = has_head(env)
            if plan_next is False:
                where = "on the Verified line" if kind in STAGE else "in Environments"
                warnings.append(
                    f"handoff: next stage is create-plan but repo HEAD {h} is not {where}"
                )
            elif shas and not any(h.startswith(s) or s.startswith(h) for s in shas):
                info.append(f"repo HEAD {h} is not mentioned in the doc")

    # a closed doc is history: gate and compaction warnings no longer apply
    if closed:
        moot = ("starthere:", "prime:", "stamp:", "handoff:", "restatement:")
        if kind == "roadmap":
            moot += ("size:", "phase:", "log:", "resume:")
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
