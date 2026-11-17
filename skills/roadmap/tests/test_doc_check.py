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

    def test_hex_word_in_prose_is_not_head_evidence(self):
        repo, head = self.git_repo()
        doc = self.explore_verified(f"abc1234 (word {head} in prose)")
        _, out = self.run_check(self.write(doc, "explore-x.md"), "--repo", repo)
        self.assertEqual(len(self.warns(out, "handoff:")), 1)

    def test_head_on_second_verified_bullet_passes(self):
        repo, head = self.git_repo()
        doc = self.explore_verified("`abc1234` (repo A)").replace(
            "- **Read first:**", f"- **Verified 2026-10-28 15:40 (repo B):** HEAD `{head}`\n- **Read first:**"
        )
        _, out = self.run_check(self.write(doc, "explore-x.md"), "--repo", repo)
        self.assertEqual(self.warns(out, "handoff:"), [])

    def test_roadmap_head_only_in_session_log_still_warns(self):
        repo, head = self.git_repo()
        doc = ROADMAP.replace(
            "run `/implement plans/p.md`", "paste `/create-plan plans/explore-x.md Phase 2 only`"
        ).replace("- 2026-10-28 created", f"- 2026-10-28 created at `{head}`")
        _, out = self.run_check(self.write(doc, "ROADMAP.md"), "--repo", repo)
        self.assertEqual(len(self.warns(out, "handoff:")), 1)

    def test_roadmap_create_plan_after_first_action_is_not_next(self):
        repo, _ = self.git_repo()
        doc = ROADMAP.replace(
            "1. **Owner:** run `/implement plans/p.md`.",
            "1. **Owner:** run `/implement plans/p.md`.\n2. After that, `/create-plan plans/explore-x.md Phase 2 only`.",
        )
        _, out = self.run_check(self.write(doc, "ROADMAP.md"), "--repo", repo)
        self.assertEqual(self.warns(out, "handoff:"), [])

    def test_full_length_head_passes(self):
        repo, _ = self.git_repo()
        full = subprocess.run(["git", "-C", repo, "rev-parse", "HEAD"],
                              capture_output=True, text=True, check=True).stdout.strip()
        doc = self.explore_verified(f"`{full}`")
        _, out = self.run_check(self.write(doc, "explore-x.md"), "--repo", repo)
        self.assertEqual(self.warns(out, "handoff:"), [])

    def test_roadmap_model_token_before_create_plan_still_checked(self):
        repo, _ = self.git_repo()
        doc = ROADMAP.replace(
            "run `/implement plans/p.md`",
            "in a session running `claude-opus-5-5`, paste `/create-plan plans/explore-x.md Phase 2 only`",
        )
        _, out = self.run_check(self.write(doc, "ROADMAP.md"), "--repo", repo)
        self.assertEqual(len(self.warns(out, "handoff:")), 1)

    def test_page_plan_detected_and_gate_checked(self):
        doc = "# Page plan: widget page\n\n**Status:** Approved\n\n" + start("/landing-page plans/page-plan-x.md")
        _, out = self.run_check(self.write(doc, "page-plan-x.md"))
        self.assertEqual(out["kind"], "pageplan")
        self.assertEqual(self.warns(out, "starthere:") + self.warns(out, "sections:"), [])

    def test_implement_next_with_stale_head_is_only_info(self):
        repo, _ = self.git_repo()
        doc = PLAN.format(start=start()).replace(
            "- **Verified 2026-10-28 15:40:** not a git repo",
            "- **Verified 2026-10-28 15:40:** HEAD `abc1234`",
        )
        _, out = self.run_check(self.write(doc), "--repo", repo)
        self.assertEqual(self.warns(out, "handoff:"), [])
        self.assertTrue(any("is not mentioned in the doc" in i for i in out["info"]))

    # selfclose (findings) ------------------------------------------------

    AUDITOR = "gpt-6.1-sol high"
    FIXER = "claude-opus-5-5 medium"

    def closed_findings(self, recheck=None, fixes="1. Repaired finding 2.\n",
                        name="2026-11-20-widget.md", status="Closed"):
        doc = FINDINGS.format(start=start()).replace("Status: Open", f"Status: {status}")
        if fixes is not None:
            doc += "\n## Fixes\n\n" + fixes
        if recheck is not None:
            doc += "\n## Re-check\n\n" + recheck
        return self.write(doc, name=name, sub="audits")

    def selfclose(self, out):
        return [e for e in out["errors"] if e.startswith("selfclose:")]

    def recheck(self, verdicts=("1 · FIXED", "2 · PARTIAL"), leftovers=None):
        if leftovers is None:
            leftovers = [f"2 · PARTIAL · Fixed by: {self.FIXER} · Verified by: {self.AUDITOR} · FIXED"]
        text = "Auditor re-check.\n\n### Verdicts\n" + "".join(f"- {v}\n" for v in verdicts)
        if leftovers:
            text += "\n### Leftovers\n" + "".join(f"- {l}\n" for l in leftovers)
        return text

    def leftover(self, fixed=None, verified=None, result="FIXED", fid="2"):
        return [f"{fid} · PARTIAL · Fixed by: {self.FIXER if fixed is None else fixed}"
                f" · Verified by: {self.AUDITOR if verified is None else verified} · {result}"]

    def check_selfclose(self, recheck, **kw):
        code, out = self.run_check(self.closed_findings(recheck, **kw), "--kind", "findings")
        return code, " | ".join(self.selfclose(out))

    def test_selfclose_clean_audit_without_fixes_passes(self):
        self.assertEqual(self.check_selfclose(None, fixes="None.\n"), (0, ""))
        self.assertEqual(self.check_selfclose(None, fixes=None), (0, ""))

    def test_selfclose_no_fixes_marker_is_the_whole_section(self):
        for marker in ("None.", "_None._", "**None**", "N/A", "No fixes needed."):
            self.assertEqual(self.check_selfclose(None, fixes=marker + "\n"), (0, ""), marker)
        prose = ("None of the initial repairs held. Finding 2 remained partial; the"
                 " dispatcher repaired and self-verified it.\n")
        code, msg = self.check_selfclose(None, fixes=prose)
        self.assertEqual(code, 1)
        self.assertIn("no '### Verdicts' list", msg)

    def test_selfclose_no_fixes_marker_in_any_list_form(self):
        for marker in ("+ None.", "+ **No fixes applied.**", "1. None", "> - N/A"):
            self.assertEqual(self.check_selfclose(None, fixes=marker + "\n"), (0, ""), marker)

    def test_selfclose_fix_queue_does_not_hide_fixes(self):
        repaired = "Finding 2 remained partial; dispatcher repaired and self-verified it.\n"
        for queue_first in (True, False):
            doc = FINDINGS.format(start=start()).replace("Status: Open", "Status: Closed")
            queue, fixes = "\n## Fix queue\n\nNone.\n", "\n## Fixes\n\n" + repaired
            doc += queue + fixes if queue_first else fixes + queue
            code, out = self.run_check(self.write(doc, name="2026-11-20-q.md", sub="audits"),
                                       "--kind", "findings")
            self.assertEqual(code, 1, queue_first)
            self.assertIn("no '### Verdicts' list", " ".join(self.selfclose(out)))

    def test_selfclose_repeated_fixes_heading_does_not_hide_fixes(self):
        doc = FINDINGS.format(start=start()).replace("Status: Open", "Status: Closed")
        doc += "\n## Fixes\n\n1. Repaired 2.\n\n## Fixes\n\nNone.\n"
        code, _ = self.run_check(self.write(doc, name="2026-11-20-r.md", sub="audits"),
                                 "--kind", "findings")
        self.assertEqual(code, 1)

    def test_selfclose_several_clean_fixes_sections_pass(self):
        # each section is judged alone: two bare markers are still a clean audit
        for extra in ("\n## Fixes\n\nNone.\n", "\n## Fix-up notes\n\nNo fixes needed.\n"):
            doc = FINDINGS.format(start=start()).replace("Status: Open", "Status: Closed")
            doc += "\n## Fixes\n\nNone.\n" + extra
            code, out = self.run_check(self.write(doc, name="2026-11-20-c.md", sub="audits"),
                                       "--kind", "findings")
            self.assertEqual((code, self.selfclose(out)), (0, []), extra)

    def test_selfclose_any_bullet_style_in_verdicts_and_leftovers(self):
        # a failed verdict in a '+' or numbered bullet is still read
        hidden = self.recheck(verdicts=("1 · FIXED",), leftovers=[]) .replace(
            "- 1 · FIXED\n", "- 1 · FIXED\n+ 2 · PARTIAL\n3) 4 · NEW\n")
        code, msg = self.check_selfclose(hidden)
        self.assertEqual(code, 1)
        self.assertIn("no Leftovers line: 2, 4", msg)
        ok = (self.recheck(verdicts=("2 · PARTIAL",), leftovers=[])
              + "\n### Leftovers\n1. " + self.leftover()[0] + "\n")
        self.assertEqual(self.check_selfclose(ok), (0, ""))

    def test_selfclose_verdicts_across_recheck_sections_are_all_read(self):
        recheck = (self.recheck(verdicts=("2 · FIXED",), leftovers=[])
                   + "\n## Re-check 2\n\n### Verdicts\n- 4 · PARTIAL\n")
        code, msg = self.check_selfclose(recheck)
        self.assertEqual(code, 1)
        self.assertIn("no Leftovers line: 4", msg)

    def test_selfclose_fixer_named_by_role_errors(self):
        for role in ("session", "Dispatcher", "this session", "implementer"):
            recheck = self.recheck(leftovers=self.leftover(fixed=role, verified=self.FIXER))
            code, msg = self.check_selfclose(recheck)
            self.assertEqual(code, 1, role)
            self.assertIn("name the fixer's tier", msg)

    def test_selfclose_all_fixed_verdicts_pass(self):
        recheck = self.recheck(verdicts=("1 · FIXED", "2 · fixed"), leftovers=[])
        self.assertEqual(self.check_selfclose(recheck), (0, ""))

    def test_selfclose_fixes_without_recheck_section_errors(self):
        # a real self-closed audit's shape: the re-check written inside Fixes, lowercase
        fixes = "1. Repaired 2.\n\nRe-check: 1 FIXED; 2 partial; the dispatcher verified the rest.\n"
        code, msg = self.check_selfclose(None, fixes=fixes)
        self.assertEqual(code, 1)
        self.assertIn("no '### Verdicts' list", msg)

    def test_selfclose_recheck_prose_without_verdicts_errors(self):
        for prose in ("2 PARTIAL; one NEW. The dispatcher verified them.\n",
                      "All 5 FIXED.\n", "nothing new or partial remains\n"):
            code, msg = self.check_selfclose(prose)
            self.assertEqual(code, 1, prose)
            self.assertIn("no '### Verdicts' list", msg)

    def test_selfclose_verdict_line_without_verdict_errors(self):
        code, msg = self.check_selfclose(self.recheck(verdicts=("2 · looks fine",), leftovers=[]))
        self.assertEqual(code, 1)
        self.assertIn("names no verdict", msg)

    def test_selfclose_verdict_is_the_first_word(self):
        # "FIXED (was PARTIAL)" is fixed; "partial" in any case is a failure
        ok = self.recheck(verdicts=("2 · FIXED (was PARTIAL)",), leftovers=[])
        self.assertEqual(self.check_selfclose(ok), (0, ""))
        bad = self.recheck(verdicts=("2 · partial (fixed later)",), leftovers=[])
        code, msg = self.check_selfclose(bad)
        self.assertEqual(code, 1)
        self.assertIn("no Leftovers line: 2", msg)

    def test_selfclose_failed_verdict_without_leftover_line_errors(self):
        good = self.leftover()[0]
        for leftovers in ([good], [good, good]):  # missing, and a duplicated row
            recheck = self.recheck(verdicts=("2 · PARTIAL", "4 · PARTIAL", "N1 · NEW"),
                                   leftovers=leftovers)
            code, msg = self.check_selfclose(recheck)
            self.assertEqual(code, 1, leftovers)
            self.assertIn("no Leftovers line: 4, n1", msg)

    def test_selfclose_repeated_verdict_in_prose_passes(self):
        recheck = ("2 PARTIAL. Finding 2 was PARTIAL before the auditor verified its repair.\n\n"
                   + self.recheck(verdicts=("2 · PARTIAL",)).split("\n\n", 1)[1])
        self.assertEqual(self.check_selfclose(recheck), (0, ""))

    def test_selfclose_different_verifier_passes(self):
        self.assertEqual(self.check_selfclose(self.recheck()), (0, ""))

    def test_selfclose_verifier_is_the_fixer_errors(self):
        for fixed, verified in (
            (self.FIXER, self.FIXER),
            ("Claude-Opus-5-5  Medium", "claude-opus-5-5 medium "),
            ("claude-opus-5-5 medium", "claude-opus-5-5"),  # word-prefix
            ("claude-opus-5-5", "claude-opus-5-5 medium"),
            (self.FIXER, "dispatcher"),  # wording from a real self-closed audit
            (self.FIXER, "Session"),
            (self.FIXER, "fixer"),
        ):
            code, msg = self.check_selfclose(self.recheck(leftovers=self.leftover(fixed, verified)))
            self.assertEqual(code, 1, (fixed, verified))
            self.assertIn("verified by its fixer", msg)

    def test_selfclose_similar_but_different_tier_passes(self):
        # a word-prefix needs a whole word: claude-opus-5 is not claude-opus-5-5
        recheck = self.recheck(leftovers=self.leftover("claude-opus-5-5 medium", "claude-opus-5 high"))
        self.assertEqual(self.check_selfclose(recheck), (0, ""))

    def test_selfclose_missing_fixer_or_verifier_errors(self):
        for fixed, verified, want in (
            ("", self.AUDITOR, "no Fixed by"), ("none", self.AUDITOR, "no Fixed by"),
            (self.FIXER, "", "no Verified by"), (self.FIXER, "none", "no Verified by"),
        ):
            code, msg = self.check_selfclose(self.recheck(leftovers=self.leftover(fixed, verified)))
            self.assertEqual(code, 1, (fixed, verified))
            self.assertIn(want, msg)
        line = f"2 · PARTIAL · Verified by: {self.AUDITOR} · FIXED"  # field absent
        code, msg = self.check_selfclose(self.recheck(leftovers=[line]))
        self.assertIn("no Fixed by", msg)

    def test_selfclose_open_result_errors(self):
        code, msg = self.check_selfclose(self.recheck(leftovers=self.leftover(result="Open")))
        self.assertEqual(code, 1)
        self.assertIn("not FIXED", msg)

    def test_selfclose_owner_accepted_passes(self):
        recheck = self.recheck(leftovers=self.leftover(
            fixed="none", verified="none", result="Accepted open by owner 2026-11-20"))
        self.assertEqual(self.check_selfclose(recheck), (0, ""))

    def test_selfclose_open_status_is_not_checked(self):
        self.assertEqual(self.check_selfclose("2 PARTIAL.\n", status="Open"), (0, ""))

    def test_selfclose_file_before_cutoff_is_exempt(self):
        path = self.closed_findings("2 PARTIAL.\n", name="2026-10-01-widget.md")
        code, out = self.run_check(path, "--kind", "findings")
        self.assertEqual((code, self.selfclose(out)), (0, []))
        self.assertTrue(any(i.startswith("selfclose:") for i in out["info"]))

    def test_selfclose_undated_file_is_checked(self):
        code, _ = self.check_selfclose("2 PARTIAL.\n", name="widget-audit.md")
        self.assertEqual(code, 1)

    # restatement (mocks) -------------------------------------------------

    def mocks_readme(self, row="| 2026-11-20 | Stage 1 restatement confirmed | Matches | Owner |"):
        return self.write(MOCKS.format(start=start()) + row + "\n", name="README.md", sub="w-mocks")

    def restatement_warns(self, row):
        _, out = self.run_check(self.mocks_readme(row), "--kind", "mocks")
        return len(self.warns(out, "restatement:"))

    def test_restatement_confirmed_rows_warn_without_file(self):
        for row in (
            "| 2026-11-20 | Stage 1 restatement confirmed | Matches | Owner |",
            "| 2026-11-20 | Stage 1 restatement | Confirmed | Owner |",
            "| 2026-11-20 | Stage 1 restatement | **Matches, plus a résumé update** | Owner |",
            "| 2026-11-20 | Stage 1 restatement | Approved | Owner |",
            "- Stage 1 Restatement CONFIRMED (2026-11-20)",
            "- Restatement: matches (owner, 2026-11-20)",
            # another clause pending must not cancel the restatement's own confirmation
            "| 2026-11-20 | Stage 1 restatement confirmed | Matches; awaiting confirmation of launch date | Owner |",
        ):
            self.assertEqual(self.restatement_warns(row), 1, row)

    def test_restatement_unconfirmed_rows_are_quiet(self):
        for row in (
            "",
            "| 2026-11-20 | Stage 1 restatement | Not confirmed | Owner |",
            "| 2026-11-20 | Stage 1 restatement | Not yet confirmed | Owner |",
            "| 2026-11-20 | Stage 1 restatement | Confirmation pending | Owner |",
            "| 2026-11-20 | Stage 1 restatement | Pending confirmation | Owner |",
            "| 2026-11-20 | Stage 1 restatement | Has not been confirmed | Owner |",
            "| 2026-11-20 | Stage 1 restatement | Mostly, with corrections | Owner |",
            "| 2026-11-20 | Stage 1 restatement | Shown, unconfirmed | Agent |",
            "- Read first: `restatement.md` (the confirmed restatement)",
        ):
            self.assertEqual(self.restatement_warns(row), 0, row)

    def test_restatement_present_is_quiet(self):
        path = self.mocks_readme()
        self.write("Goals: ship it. Owner: matches.\n", name="restatement.md", sub="w-mocks")
        _, out = self.run_check(path, "--kind", "mocks")
        self.assertEqual(self.warns(out, "restatement:"), [])

    def test_restatement_empty_file_warns(self):
        path = self.mocks_readme()
        self.write("  \n", name="restatement.md", sub="w-mocks")
        _, out = self.run_check(path, "--kind", "mocks")
        self.assertEqual(len(self.warns(out, "restatement:")), 1)

    # viewer (mocks) ------------------------------------------------------

    def test_viewer_needs_its_sandbox_test(self):
        def viewer_warns(sub, viewer, test):
            path = self.write(MOCKS.format(start=start()), name="README.md", sub=sub)
            if viewer:
                self.write("<!doctype html>\n", name="compare.html", sub=sub)
            if test:
                self.write("// test\n", name="sandbox-e2e.mjs", sub=os.path.join(sub, "tools"))
            _, out = self.run_check(path, "--kind", "mocks")
            return len(self.warns(out, "viewer:"))
        self.assertEqual(viewer_warns("v-with", True, True), 0)
        self.assertEqual(viewer_warns("v-without", True, False), 1)
        self.assertEqual(viewer_warns("v-none", False, False), 0)

    def test_restatement_closed_readme_is_not_enforced(self):
        path = self.write(
            MOCKS.format(start=start()).replace("# Widget mocks\n", "# Widget mocks\n\nStatus: Closed\n")
            + "| 2026-11-20 | Stage 1 restatement confirmed | Matches | Owner |\n",
            name="README.md", sub="c-mocks",
        )
        _, out = self.run_check(path, "--kind", "mocks")
        self.assertEqual(self.warns(out, "restatement:"), [])

    def test_missing_file_exits_2(self):
        code, _ = self.run_check(os.path.join(self.dir, "nope.md"))
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
