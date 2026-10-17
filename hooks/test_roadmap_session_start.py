"""Tests for roadmap-session-start.py. Run: python3 -m unittest test_roadmap_session_start"""

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "roadmap-session-start.py")
spec = importlib.util.spec_from_file_location("rss", SCRIPT)
rss = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rss)


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


ROADMAP = """# Demo roadmap: App

Status: {status}
Last updated: 2026-10-01 (created)

## Resume here

1. **Agent:** plan Phase 2. No approval needed.

## North star
"""


class RoadmapSessionStart(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.repo = os.path.join(self.tmp, "App")
        os.makedirs(os.path.join(self.repo, ".git"))
        write(os.path.join(self.repo, "master.md"), "# App\n")
        self.root = os.path.join(self.tmp, "App-handoffs")

    def run_hook(self, cwd):
        r = subprocess.run(
            [sys.executable, SCRIPT],
            input=json.dumps({"cwd": cwd, "hook_event_name": "SessionStart"}),
            capture_output=True, text=True, timeout=10,
        )
        self.assertEqual(r.returncode, 0)
        return json.loads(r.stdout)["hookSpecificOutput"]["additionalContext"] if r.stdout.strip() else ""

    def test_silent_without_roadmap_or_handoff(self):
        self.assertEqual(self.run_hook(self.repo), "")

    def test_active_roadmap_by_glob(self):
        write(os.path.join(self.root, "roadmap-demo", "ROADMAP.md"), ROADMAP.format(status="Active"))
        ctx = self.run_hook(os.path.join(self.repo))
        self.assertIn("Active roadmap:", ctx)
        self.assertIn("plan Phase 2", ctx)

    def test_closed_roadmap_ignored(self):
        write(os.path.join(self.root, "roadmap-demo", "ROADMAP.md"), ROADMAP.format(status="Closed 2026-10-01"))
        self.assertEqual(self.run_hook(self.repo), "")

    def test_closed_anywhere_in_header_skipped(self):
        text = ROADMAP.format(status="Active").replace(
            "Last updated: 2026-10-01 (created)",
            "Last updated: 2026-10-05 · Status: Closed 2026-10-05 · Final SHA `abc1234`")
        write(os.path.join(self.root, "roadmap-demo", "ROADMAP.md"), text)
        self.assertEqual(self.run_hook(self.repo), "")

    def test_message_defers_to_named_file(self):
        write(os.path.join(self.root, "roadmap-demo", "ROADMAP.md"), ROADMAP.format(status="Active"))
        self.assertIn("resume point", self.run_hook(self.repo))

    def test_master_pointer_legacy_path(self):
        legacy = os.path.join(self.tmp, "elsewhere", "ROADMAP-STATE.md")
        write(legacy, "# Legacy\n\n## Resume here\n\n- do the thing\n")
        write(os.path.join(self.repo, "master.md"),
              f"# App\n\n## Active roadmaps\n\n- Demo (Active, Phase 2): `{legacy}`\n\n## Other\n")
        ctx = self.run_hook(self.repo)
        self.assertIn("ROADMAP-STATE.md", ctx)
        self.assertIn("do the thing", ctx)

    def test_newest_open_handoff_skips_superseded(self):
        write(os.path.join(self.root, "2026-09-01-old.md"), "> **Superseded:** resume from x\n")
        write(os.path.join(self.root, "2026-09-02-done.md"), "# H\n\nStatus: Done\n")
        write(os.path.join(self.root, "2026-08-30-open.md"), "# H\n\nStatus: Open\n")
        ctx = self.run_hook(self.repo)
        self.assertIn("2026-08-30-open.md", ctx)
        self.assertNotIn("2026-09-01-old.md", ctx)

    def test_due_reminders_only(self):
        write(os.path.join(self.repo, "master.md"),
              "# App\n\n## Reminders\n\n- rotate key (when: on 2000-01-01; added 1999-12-01)\n"
              "- later thing (when: on 2999-01-01; added 2026-10-01)\n"
              "- check logs (when: next session; added 2026-10-01)\n"
              "- at close (when: next close; added 2026-10-01)\n\n## Other\n")
        ctx = self.run_hook(self.repo)
        self.assertIn("rotate key", ctx)
        self.assertIn("check logs", ctx)
        self.assertNotIn("later thing", ctx)
        self.assertNotIn("at close", ctx)

    def test_bad_input_never_fails(self):
        r = subprocess.run([sys.executable, SCRIPT], input="not json", capture_output=True, text=True)
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout, "")


if __name__ == "__main__":
    unittest.main()
