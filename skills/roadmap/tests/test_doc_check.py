"""Behaviour tests for doc_check.py: kind detection, the cold-start gate checks
(starthere, scratch, stamp, prime), paths and exit codes. Each test writes a
small doc into a temp folder and runs the checker as a user would."""

import json
import os
import subprocess
import sys
import tempfile
import unittest

SCRIPT = os.path.join(os.path.dirname(__file__), "..", "scripts", "doc_check.py")

START = """## Start here (cold start)

- **Goal and where this sits:** ship the widget; Phase 1 of the widget roadmap
- **Verified 2026-10-28 15:40:** not a git repo
- **Read first:** this doc only
- **Next:** `{next}`
- No `/prime` or `/handoff` needed. cold-start pass 2026-10-28
"""

EXPLORE = """# Explore: Widget

**Created:** 2026-10-28
**Status:** Explored

{start}
## Confirmed restatement

Goals.

## Discovery Notes

Notes.
"""

PLAN = """# Plan: Widget

**Created:** 2026-10-28
**Status:** Ready

{start}
## Design Decisions

One.

## Step-by-Step Tasks

### Step 1: build

## Success Criteria

1. Works.
"""

FINDINGS = """# Work-audit: widget

Status: Open

{start}
## Findings

None.

## Open items

None.
"""

MOCKS = """# Widget mocks

{start}
## Gate log

- G1 type picked (2026-10-28)
"""

ROADMAP = """# Widget roadmap: Shop

Status: Active
Last updated: 2026-10-28 (created) · cold-start pass 2026-10-28

## Resume here

1. **Owner:** run `/implement plans/p.md`.

## North star

## Locked decisions

- **D1 Budget:** none (2026-10-28)

## Guarantees

## Phase status

| Phase | Status |
| ----- | ------ |
| 1 | Planned |

## Environments

## Session log

- 2026-10-28 created
"""

HANDOFF = """# Handoff: widget (2026-10-28)

Status: Open
Last updated: 2026-10-28 10:00
Paste in the new session: `resume from here` · cold-start pass 2026-10-28

## Goal

Ship it.

## Next actions

1. Run the tests.

## Current state

Clean.
"""


def start(next_cmd="/implement plans/p.md"):
    return START.format(next=next_cmd)


class DocCheck(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = os.path.realpath(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, text, name="doc.md", sub=""):
        folder = os.path.join(self.dir, sub)
        os.makedirs(folder, exist_ok=True)
        path = os.path.join(folder, name)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        return path

    def run_check(self, path, *args):
        r = subprocess.run(
            [sys.executable, SCRIPT, *args, path], capture_output=True, text=True
        )
        out = json.loads(r.stdout) if r.stdout.strip().startswith("{") else None
        return r.returncode, out

    def warns(self, out, prefix):
        return [w for w in out["warnings"] if w.startswith(prefix)]

    # kind detection -------------------------------------------------------

    def test_kind_auto_detected_for_every_kind(self):
        cases = {
            "explore": self.write(EXPLORE.format(start=start()), "explore-2026-10-28-w.md"),
            "plan": self.write(PLAN.format(start=start()), "2026-10-28-w.md"),
            "findings": self.write(FINDINGS.format(start=start()), "2026-10-28-w.md", "audits"),
            "mocks": self.write(MOCKS.format(start=start()), "README.md", "widget-mocks"),
            "roadmap": self.write(ROADMAP, "ROADMAP.md", "roadmap-w"),
            "handoff": self.write(HANDOFF, "2026-10-28-w.md", "handoffs"),
        }
        for kind, path in cases.items():
            with self.subTest(kind=kind):
                code, out = self.run_check(path)
                self.assertEqual(out["kind"], kind)
                self.assertEqual(code, 0)
                self.assertEqual(out["warnings"], [], out["warnings"])

    def test_findings_named_roadmap_is_findings(self):
        doc = FINDINGS.format(start=start())
        cases = {
            "audits dir": self.write(doc, "2026-10-28-roadmap.md", "audits"),
            "work-audit title": self.write(doc, "roadmap-audit.md", "notes"),
        }
        for label, path in cases.items():
            with self.subTest(case=label):
                code, out = self.run_check(path)
                self.assertEqual(out["kind"], "findings")
                self.assertEqual(code, 0)
                self.assertEqual(out["warnings"], [], out["warnings"])

    def test_explicit_kind_overrides_detection(self):
        path = self.write(PLAN.format(start=start()), "notes.md")
        code, out = self.run_check(path, "--kind", "explore")
        self.assertEqual(out["kind"], "explore")
        self.assertIn("sections: missing '## Confirmed restatement'", out["warnings"])

    # starthere ------------------------------------------------------------

    def test_starthere_next_without_command_warns(self):
        doc = PLAN.format(start=start()).replace(
            "- **Next:** `/implement plans/p.md`", "- **Next:** implement it"
        )
        _, out = self.run_check(self.write(doc))
        self.assertEqual(
            self.warns(out, "starthere:"),
            ["starthere: the 'Next' line has no backticked command to paste"],
        )

    def test_starthere_missing_parts_warn(self):
        doc = EXPLORE.format(start="## Start here\n\n- **Next:** `/create-plan x`\n- No `/prime` needed\n")
        _, out = self.run_check(self.write(doc, "explore-x.md"))
        self.assertEqual(
            sorted(self.warns(out, "starthere:")),
            [
                "starthere: no 'Read first' line",
                "starthere: no Goal line",
                "starthere: no dated 'Verified YYYY-MM-DD' line",
            ],
        )

    def test_starthere_section_missing_warns_once(self):
        doc = PLAN.format(start="")
        _, out = self.run_check(self.write(doc))
        self.assertEqual(self.warns(out, "starthere:"), ["starthere: no '## Start here' section"])
        self.assertEqual(self.warns(out, "prime:"), [])

    # scratch --------------------------------------------------------------

    def test_scratch_path_warns(self):
        for bad in ("/tmp/s1-home/log.txt", "/private/tmp/claude-501/x/scratchpad/notes.md"):
            with self.subTest(bad=bad):
                doc = PLAN.format(start=start()) + f"\nEvidence at `{bad}`.\n"
                _, out = self.run_check(self.write(doc))
                self.assertEqual(len(self.warns(out, "scratch:")), 1)

    def test_scratch_prose_mention_passes(self):
        doc = PLAN.format(start=start()) + "\nNo `/tmp` or session scratchpad path stays here.\n"
        _, out = self.run_check(self.write(doc))
        self.assertEqual(self.warns(out, "scratch:"), [])

    # stamp ----------------------------------------------------------------

    def test_missing_stamp_warns(self):
        doc = EXPLORE.format(start=start()).replace(" cold-start pass 2026-10-28", "")
        _, out = self.run_check(self.write(doc, "explore-x.md"))
        self.assertEqual(len(self.warns(out, "stamp:")), 1)

    def test_urgent_handoff_needs_no_stamp(self):
        doc = HANDOFF.replace(" · cold-start pass 2026-10-28", "") + (
            "\n## Interrupted 2026-10-28 11:00 (urgent stop)\n\n"
            "- **Next action:** rerun\n- **Paste:** `resume from here`\n"
        )
        _, out = self.run_check(self.write(doc, "h.md", "handoffs"))
        self.assertEqual(self.warns(out, "stamp:"), [])

    # prime ----------------------------------------------------------------

    def test_missing_no_prime_line_warns(self):
        doc = FINDINGS.format(start=start()).replace(
            "- No `/prime` or `/handoff` needed. ", "- "
        )
        _, out = self.run_check(self.write(doc, "f.md", "audits"))
        self.assertEqual(len(self.warns(out, "prime:")), 1)

    def test_closed_doc_skips_gate_checks(self):
        doc = FINDINGS.format(start="").replace("Status: Open", "Status: Closed")
        _, out = self.run_check(self.write(doc, "f.md", "audits"))
        self.assertEqual(
            [w for w in out["warnings"] if w.startswith(("starthere:", "prime:", "stamp:"))], []
        )

    # paths ----------------------------------------------------------------

    def test_nonexistent_path_warns_existing_passes(self):
        os.makedirs(os.path.join(self.dir, "runs", "r1"))
        doc = PLAN.format(start=start()) + "\nSee `runs/r1` and `runs/missing.md`.\n"
        _, out = self.run_check(self.write(doc, "p.md", "plans"))
        self.assertEqual(self.warns(out, "path:"), [
            f"path: line {doc.count(chr(10))} `runs/missing.md` does not exist"
        ])

    def test_path_marked_created_by_step_passes(self):
        doc = PLAN.format(start=start()) + "\nWrites `runs/new.md` (created by Step 2).\n"
        _, out = self.run_check(self.write(doc))
        self.assertEqual(self.warns(out, "path:"), [])

    # size and exit codes --------------------------------------------------

    def test_size_budget_per_kind(self):
        doc = EXPLORE.format(start=start()) + ("x" * 21 * 1024)
        _, out = self.run_check(self.write(doc, "explore-x.md"))
        self.assertEqual(len(self.warns(out, "size:")), 1)
        _, out = self.run_check(self.write(PLAN.format(start=start()) + "x" * 21 * 1024))
        self.assertEqual(self.warns(out, "size:"), [])

    def test_secret_is_an_error_and_exits_1(self):
        doc = PLAN.format(start=start()) + "\npostgres://user:hunter2pass@db.example.com/x\n"
        code, out = self.run_check(self.write(doc))
        self.assertEqual(code, 1)
        self.assertTrue(out["errors"][0].startswith("secret:"))

    # handoff: a create-plan hand-off carries the current HEAD -------------

    def git_repo(self):
        repo = os.path.join(self.dir, "repo")
        os.makedirs(repo)
        git = ["git", "-C", repo, "-c", "user.name=t", "-c", "user.email=t@t"]
        subprocess.run(git + ["init", "-q"], check=True)
        subprocess.run(git + ["commit", "-q", "--allow-empty", "-m", "x"], check=True)
        head = subprocess.run(
            ["git", "-C", repo, "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
        return repo, head

    def explore_verified(self, verified, next_cmd="/create-plan plans/explore-x.md Phase 2 only"):
        return EXPLORE.format(start=start(next_cmd)).replace(
            "- **Verified 2026-10-28 15:40:** not a git repo",
            f"- **Verified 2026-10-28 15:40:** repo `main`, HEAD {verified}",
        )

    def test_create_plan_next_with_current_head_passes(self):
        repo, head = self.git_repo()
        doc = self.explore_verified(f"`{head}`")
        _, out = self.run_check(self.write(doc, "explore-x.md"), "--repo", repo)
        self.assertEqual(self.warns(out, "handoff:"), [])

    def test_create_plan_next_with_stale_head_warns(self):
        repo, head = self.git_repo()
        doc = self.explore_verified("abc1234")
        _, out = self.run_check(self.write(doc, "explore-x.md"), "--repo", repo)
        self.assertEqual(
            self.warns(out, "handoff:"),
            [f"handoff: next stage is create-plan but repo HEAD {head} is not on the Verified line"],
        )

    def test_roadmap_resume_create_plan_without_head_warns(self):
        repo, head = self.git_repo()
        doc = ROADMAP.replace(
            "run `/implement plans/p.md`", "paste `/create-plan plans/explore-x.md Phase 2 only`"
        )
        _, out = self.run_check(self.write(doc, "ROADMAP.md"), "--repo", repo)
        self.assertEqual(len(self.warns(out, "handoff:")), 1)
        _, out = self.run_check(
            self.write(doc.replace("## Environments\n", f"## Environments\n\n- HEAD `{head}`\n"), "ROADMAP.md"),
            "--repo", repo,
        )
        self.assertEqual(self.warns(out, "handoff:"), [])

    def test_implement_next_with_stale_head_is_only_info(self):
        repo, _ = self.git_repo()
        doc = PLAN.format(start=start()).replace(
            "- **Verified 2026-10-28 15:40:** not a git repo",
            "- **Verified 2026-10-28 15:40:** HEAD `abc1234`",
        )
        _, out = self.run_check(self.write(doc), "--repo", repo)
        self.assertEqual(self.warns(out, "handoff:"), [])
        self.assertTrue(any("is not mentioned in the doc" in i for i in out["info"]))

    def test_missing_file_exits_2(self):
        code, _ = self.run_check(os.path.join(self.dir, "nope.md"))
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
