#!/usr/bin/env python3
"""Commit and push workcycle docs at the end of a stage (cold-start gate step 8).

Usage: publish_workcycle.py [--stage NAME] [--dry-run] [--owner-approved] PATH [PATH ...]

Each PATH is a work folder or file inside the workcycle root (`## Workcycle root` in
~/.agents/local/workcycle.md), which must be the top of a git work tree; the root itself is not a
valid PATH. Only those paths are committed.

Consent: a line `standing go: yes …` or `standing go: commit and push …` in the `## Workcycle publish`
section (not indented code, a fenced block or an HTML comment) grants a standing go; any other value on a
`standing go:` line there withholds it. Otherwise the script exits 3 and the skill asks the owner,
then runs it again with --owner-approved for that one publish.

Steps: refuse unless the upstream remote has exactly one push URL, equal to its fetch URL; refuse
if anything is already staged in the root (so nothing of the user's is ever swept in or lost);
pull --ff-only; check each earlier unpushed commit (renames as both paths, merges against each
parent): it must touch only PATH and pass the secret scan; stage PATH; refuse secrets (names, and
every added line of content incl. binary files, read as bytes); `git commit` (the root's commit
hooks run); push that commit to the upstream branch with an explicit, non-forced refspec; confirm
with ls-remote that the remote branch is that commit. A repo with a remote but no upstream (e.g. a
detached HEAD in a fresh cloud clone) is refused before committing; a repo with no remote commits
locally (the owner's root may be local-only). A PATH that no longer exists is accepted, after the
pull, when it is tracked or an unpushed commit touches it (a retry); one git never knew is skipped
with a note. The commit itself is checked again (paths and secrets) before it is pushed, since a
commit hook or another process may have staged more after the scan.

Exit codes: 0 published, committed locally (no remote) or nothing to publish · 2 bad usage or a
path outside the root · 3 not configured (ask the owner) · 4 pull, push, scope or commit problem,
or something already staged (ask the owner) · 5 secret found.
"""

import argparse
import os
import re
import subprocess
import sys

CONFIG = os.path.join(os.path.expanduser("~"), ".agents", "local", "workcycle.md")
SECRET_NAME = re.compile(r"(^|/)(\.env(\..*)?|\.secrets-[^/]*/.*|.*\.(pem|key)|.*secret.*|.*api[- ]?key.*)$", re.I)
# Same credential forms as roadmap/scripts/doc_check.py, plus Anthropic and fine-grained GitHub keys.
SECRET_TEXT = re.compile(
    r"(postgres(?:ql)?://[^\s:`]+:[^\s@`]+@|mysql://[^\s:`]+:[^\s@`]+@|\bsk-[A-Za-z0-9_-]{20,}"
    r"|\bgh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|\bxox[abpr]-[A-Za-z0-9-]{10,}"
    r"|\bAKIA[0-9A-Z]{16}\b|-----BEGIN [A-Z ]*PRIVATE KEY-----|\beyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\."
    r"|(?i:\b(?:password|passwd|secret|api[_-]?key|token)\s*[:=]\s*[\"']?(?![<`~/.])[A-Za-z0-9+/_\-]{12,}))")
ENV = {**os.environ, "GIT_LITERAL_PATHSPECS": "1"}  # a validated path is a path, never pathspec magic
# Every diff the scanner reads: user config (color, external diff, textconv, prefixes, renames) must not reshape it.
DIFF = ["--no-color", "--no-ext-diff", "--no-textconv", "--src-prefix=a/", "--dst-prefix=b/", "--no-renames"]
GRANT = re.compile(r"(yes\b|commit and push\b)", re.I)


class Stop(Exception):
    def __init__(self, code, msg):
        super().__init__(msg)
        self.code = code


def section(text, name):
    """The lines under `## <name>`, up to the next `#`/`##` heading, without fenced code blocks."""
    out, inside_sec, fence = [], False, None
    text = re.sub(r"<!--.*?(-->|\Z)", "", text, flags=re.S)  # HTML comments say nothing
    for line in text.splitlines():
        if fence:
            if re.fullmatch(rf"[ \t]*{re.escape(fence[0])}{{{len(fence)},}}[ \t]*", line):
                fence = None  # a closing fence carries no info string
            continue
        m = re.match(r"[ \t]*(?:[-*+][ \t]+|\d+[.)][ \t]+)?(`{3,}|~{3,})", line)  # also fences nested in lists
        if m:
            fence = m.group(1)
            continue
        if re.match(r"#{1,2}[ \t]", line):
            inside_sec = re.fullmatch(rf"## {re.escape(name)}[ \t]*", line) is not None
        elif inside_sec:
            out.append(line)
    return "\n".join(out)


def granted_by(text):
    """True when the publish section has a `standing go:` line and every such line says yes or commit and push."""
    values = [v.strip() for v in re.findall(r"^ {0,3}(?:[-*][ \t]+)?standing go:(.*)$",  # not indented code
                                            section(text, "Workcycle publish"), re.M | re.I)]
    return bool(values) and all(GRANT.match(v) for v in values)


def load():
    try:
        with open(CONFIG, encoding="utf-8") as f:
            text = f.read()
    except OSError:
        return None, False
    m = re.search(r"`([^`]*)`", section(text, "Workcycle root"))
    root = os.path.realpath(os.path.expanduser(m.group(1).strip())) if m and m.group(1).strip() else None
    return root, granted_by(text)


def git(root, *args, check=False):
    r = subprocess.run(["git", "-C", root, *args], capture_output=True, text=True, encoding="utf-8",
                       errors="replace", env=ENV)
    if check and r.returncode != 0:
        raise Stop(4, f"git {args[0]} failed: " + (r.stderr or r.stdout).strip())
    return r


def git_bytes(root, *args):
    r = subprocess.run(["git", "-C", root, *args], capture_output=True, env=ENV)
    if r.returncode != 0:
        raise Stop(4, f"git {args[0]} failed: " + r.stderr.decode("utf-8", "replace").strip())
    return r.stdout


def say(msg):
    print(f"publish: {msg}")


def inside(path, rel):
    return any(path == r or path.startswith(r.rstrip("/") + "/") for r in rel)


def names(root, *args):
    return [f for f in git(root, *args, "--name-only", "-z", *DIFF, check=True).stdout.split("\0") if f]


def secret_check(root, diff_cmd, files, where=""):
    """Refuse secret-looking file names and added lines. The patch is read as bytes and split only at
    git's own LF, so a CR or form feed inside a line cannot cut a key off from its `+` marker."""
    bad = [f for f in files if SECRET_NAME.search(f)]
    patch = git_bytes(root, *diff_cmd, "-p", "--text", "-U0", *DIFF)
    hits, in_hunk = [], False
    for l in patch.split(b"\n"):  # added lines are the `+` lines inside hunks; file headers sit before `@@`
        if l.startswith(b"diff --git ") or l.startswith(b"diff --cc ") or l.startswith(b"diff --combined "):
            in_hunk = False
        elif l.startswith(b"@@"):
            in_hunk = True
        elif in_hunk and l.startswith(b"+") and SECRET_TEXT.search(l.decode("utf-8", "replace")):
            hits.append(l)
    if bad or hits:
        raise Stop(5, f"refused: possible secret{where}; nothing committed or pushed. "
                   + (f"files: {', '.join(bad)}. " if bad else "")
                   + (f"{len(hits)} line(s) look like a key or token." if hits else ""))


def publish(a, root, rel):
    branch = git(root, "symbolic-ref", "-q", "--short", "HEAD").stdout.strip()
    remotes = git(root, "remote").stdout.split()
    upstream = git(root, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}").stdout.strip() if branch else ""
    if remotes and not upstream:
        why = "HEAD is detached" if not branch else "the branch has no upstream"
        raise Stop(4, f"not published: {why}, so a push would go nowhere; nothing committed. Check out the "
                      "default branch (git checkout main) or set its upstream, then run this again; ask the owner if unsure")
    remote = git(root, "config", f"branch.{branch}.remote").stdout.strip() if upstream else ""
    merge = git(root, "config", f"branch.{branch}.merge").stdout.strip() if upstream else ""
    if upstream:
        if git(root, "config", "--bool", f"remote.{remote}.mirror").stdout.strip() == "true":
            raise Stop(4, f"not published: remote {remote} is a mirror; ask the owner")
        fetch_url = git(root, "remote", "get-url", "--", remote)
        push_urls = git(root, "remote", "get-url", "--push", "--all", "--", remote)
        if (fetch_url.returncode or push_urls.returncode or not merge.startswith("refs/heads/")
                or push_urls.stdout.split("\n")[:-1] != [fetch_url.stdout.strip()]):
            raise Stop(4, f"not published: the push destination of {upstream} is ambiguous (it needs exactly one push "
                          f"URL, equal to the fetch URL, and a branch upstream); nothing committed. Ask the owner")
    has_head = git(root, "rev-parse", "--verify", "-q", "HEAD").returncode == 0
    if git(root, "diff", "--cached", "--quiet", *(["HEAD"] if has_head else []), "--").returncode != 0:
        raise Stop(4, "not published: something is already staged in the workcycle root; commit or unstage it "
                      "(git restore --staged <path>), then run this again. Nothing was changed")

    if upstream and not a.dry_run:
        pull = git(root, "pull", "--ff-only", "--quiet")
        if pull.returncode != 0:
            raise Stop(4, "pull --ff-only failed (diverged or conflicting); ask the owner:\n" + (pull.stderr or pull.stdout).strip())
        has_head = git(root, "rev-parse", "--verify", "-q", "HEAD").returncode == 0
    base = git(root, "rev-parse", "HEAD", check=True).stdout.strip() if has_head else ""

    known = []
    for r in rel:  # checked after the pull, so a retry sees the remote's real state
        if not os.path.lexists(os.path.join(root, r)) and git(root, "ls-files", "--error-unmatch", "--", r).returncode \
                and not (upstream and git(root, "log", "-1", "--format=%H", f"{upstream}..{base}", "--", r).stdout.strip()):
            say(f"skipped {r}: not on disk, not tracked, not in an unpushed commit (nothing of it to publish)")
            continue
        known.append(r)
    if not known:
        say("nothing to publish in " + ", ".join(rel))
        return 0

    # Earlier unpushed commits ride along on the push: each must stay inside the same paths and pass the
    # secret scan on its own (a file added then removed, or a rename, still leaves the history).
    outgoing = git(root, "rev-list", "--reverse", f"{upstream}..{base}", check=True).stdout.split() if upstream else []
    for c in outgoing:
        touched = names(root, "diff-tree", "-r", "-m", "--root", "--no-commit-id", c)
        stray = [f for f in touched if not inside(f, rel)]
        if stray:
            raise Stop(4, f"not published: earlier unpushed commit {c[:7]} (of {len(outgoing)}) touches files outside "
                          f"{', '.join(rel)}: {', '.join(stray[:5])}. Review and push it, or ask the owner")
        secret_check(root, ["diff-tree", "-r", "-m", "--root", c], touched, where=f" in earlier commit {c[:7]}")

    rel = known
    present = [r for r in rel if os.path.lexists(os.path.join(root, r))
               or git(root, "ls-files", "--error-unmatch", "--", r).returncode == 0]
    if present:
        git(root, "add", "-A", "--", *present, check=True)
    cached = ["diff", "--cached"] + (["HEAD"] if has_head else [])
    def unstage():
        r = git(root, "reset", "-q", "--", *present) if has_head else \
            git(root, "rm", "-q", "-r", "--cached", "--ignore-unmatch", "--", *present)
        if r.returncode:
            say(f"warning: could not unstage {', '.join(present)} (run `git restore --staged` on them in the root "
                f"before the next publish): {(r.stderr or r.stdout).strip()}")
    try:
        changed = names(root, *cached)
        if changed:
            secret_check(root, cached, changed)
    except Stop:
        unstage()  # the index was empty before, so this restores it exactly
        raise
    if a.dry_run:
        unstage()
        say(f"dry run: would commit {len(changed)} file(s)" + (": " + ", ".join(changed[:10]) if changed else "")
            + (f" and push {len(outgoing)} earlier commit(s)" if outgoing else ""))
        return 0
    if not changed and not outgoing:
        say("nothing to publish in " + ", ".join(rel))
        return 0
    msg = f"{a.stage}: {', '.join(rel)}"
    sha = base
    if changed:
        moved = ("not published: HEAD moved while publishing (another commit or a branch switch); nothing "
                 "pushed. Check `git log` in the root, then run this again")
        head = lambda: git(root, "rev-parse", "-q", "--verify", "HEAD").stdout.strip()
        if git(root, "symbolic-ref", "-q", "--short", "HEAD").stdout.strip() != branch or head() != base:
            unstage()
            raise Stop(4, moved)
        commit = git(root, "commit", "-q", "-m", msg)  # commits only the index, which holds only PATH; hooks run
        if commit.returncode != 0:
            unstage()
            raise Stop(4, moved if head() != base else "commit refused (a commit hook, or git); nothing committed. "
                       "Ask the owner:\n" + (commit.stderr or commit.stdout).strip())
        sha = head()
        parent = git(root, "rev-parse", "-q", "--verify", "HEAD^").stdout.strip()
        if parent != base or git(root, "symbolic-ref", "-q", "--short", "HEAD").stdout.strip() != branch:
            raise Stop(4, moved)  # never push a commit that is not exactly the base plus PATH
        # Check the commit itself, not the earlier scan: a commit hook or another process may have staged more.
        final = names(root, "diff-tree", "-r", "--root", "--no-commit-id", sha)
        stray = [f for f in final if not inside(f, rel)]
        if stray:
            raise Stop(4, f"not published: commit {sha[:7]} also holds {', '.join(stray[:5])} (staged by a commit hook or "
                          "another process); it stays local, nothing pushed. Review it, or ask the owner")
        secret_check(root, ["diff-tree", "-r", "--root", sha], final, where=f" in commit {sha[:7]}; it stays local")
    short = sha[:7]
    if not remotes:
        say(f"committed {short} ({len(changed)} file(s)); the repo has no remote, so nothing to push")
        return 0
    push = git(root, "push", "--quiet", "--no-follow-tags", "--recurse-submodules=no", remote, f"{sha}:{merge}")
    if push.returncode != 0:
        raise Stop(4, f"committed {short} but push failed; run this again once fixed, or ask the owner:\n"
                      + (push.stderr or push.stdout).strip())
    seen = [l.split("\t")[0] for l in git(root, "ls-remote", "--", remote, merge).stdout.splitlines()
            if l.endswith("\t" + merge)]
    if seen != [sha]:
        raise Stop(4, f"pushed, but {remote} {merge} does not show {short}; check the remote, or ask the owner")
    say(f"pushed {short} ({len(changed)} file(s)" + (f", {len(outgoing)} earlier commit(s)" if outgoing else "") + f"): {msg}")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("--stage", default="stage")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--owner-approved", action="store_true",
                    help="the owner approved this one publish in chat (no standing go configured)")
    ap.add_argument("paths", nargs="+")
    a = ap.parse_args(argv)

    root, granted = load()
    if not root:
        say("no workcycle root configured; nothing to publish")
        return 3
    if not (granted or a.owner_approved):
        say("no standing go in workcycle.md → Workcycle publish; ask the owner, then rerun with --owner-approved")
        return 3
    top = git(root, "rev-parse", "--show-toplevel")
    if top.returncode != 0 or os.path.realpath(top.stdout.strip()) != root:
        say(f"workcycle root {root} is not the top of a git work tree")
        return 3

    rel = []
    for p in a.paths:
        real = os.path.realpath(os.path.expanduser(p))
        if real == root:
            say("refusing the whole workcycle root; name the stage's work folder or files")
            return 2
        if not real.startswith(root + os.sep):
            say(f"refusing a path outside the workcycle root: {p}")
            return 2
        rel.append(os.path.relpath(real, root))

    try:
        return publish(a, root, rel)
    except Stop as e:
        say(str(e))
        return e.code


if __name__ == "__main__":
    sys.exit(main())
