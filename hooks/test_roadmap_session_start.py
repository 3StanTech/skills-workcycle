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
            env={**os.environ, "HOME": self.tmp},  # never read the real workcycle.md
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

    # Workcycle root (handoff skill → Paths)

    def config(self, root, overrides=()):
        rows = "".join(f"| `{p}` | `{n}` |\n" for p, n in overrides)
        write(os.path.join(self.tmp, ".agents", "local", "workcycle.md"),
              f"# Local\n\n## Workcycle root\n\n`{root}`\n\n## Workcycle folders (overrides)\n\n"
              f"| Project path | Workcycle folder |\n|---|---|\n{rows}\n## Other\n")

    def test_workcycle_root_with_symlinked_master(self):
        wf = os.path.join(self.tmp, "Workcycle Files")
        self.config(wf)
        os.remove(os.path.join(self.repo, "master.md"))
        write(os.path.join(wf, "App", "master.md"), "# App\n")
        os.symlink(os.path.join(wf, "App", "master.md"), os.path.join(self.repo, "master.md"))
        work = os.path.join(wf, "App", "2026-11-19-demo")
        write(os.path.join(work, "ROADMAP.md"), ROADMAP.format(status="Active"))
        write(os.path.join(work, "handoffs", "2026-11-19-demo-pause.md"), "# Handoff\n\nStatus: Open\n")
        write(os.path.join(self.root, "roadmap-old", "ROADMAP.md"), ROADMAP.format(status="Active"))
        ctx = self.run_hook(self.repo)
        self.assertIn(os.path.join(work, "ROADMAP.md"), ctx)
        self.assertIn("2026-11-19-demo-pause.md", ctx)
        self.assertNotIn("roadmap-old", ctx)  # the old -handoffs folder is ignored once a root is set

    def test_workcycle_override_maps_client_path(self):
        wf = os.path.join(self.tmp, "WF")
        site = os.path.join(self.tmp, "Biz", "Websites", "(DEMO) Acme Site")
        os.makedirs(os.path.join(site, ".git"))
        write(os.path.join(self.tmp, "Biz", "master.md"), "# Biz\n")
        self.config(wf, [(site, "Biz/Acme")])
        write(os.path.join(wf, "Biz", "Acme", "2026-11-19-redesign", "ROADMAP.md"), ROADMAP.format(status="Active"))
        ctx = self.run_hook(site)
        self.assertIn(os.path.join(wf, "Biz", "Acme", "2026-11-19-redesign", "ROADMAP.md"), ctx)

    def test_master_pointer_path_with_spaces(self):
        rm = os.path.join(self.tmp, "Workcycle Files", "App", "2026-11-19-demo", "ROADMAP.md")
        write(rm, ROADMAP.format(status="Active"))
        write(os.path.join(self.repo, "master.md"),
              f"# App\n\n## Active roadmaps\n\n- Demo (Active, Phase 1): {rm}\n")
        self.assertIn(rm, self.run_hook(self.repo))

    def test_urgent_stop_comes_first(self):
        write(os.path.join(self.root, "roadmap-demo", "ROADMAP.md"), ROADMAP.format(status="Active"))
        write(os.path.join(self.root, "roadmap-demo", "plans", "2026-11-19-x.md"), "# Plan\n\n## Interrupted\n\n- step\n")
        write(os.path.join(self.root, "roadmap-demo", "runs", "log.md"), "## Interrupted\n")  # runs/ is skipped
        ctx = self.run_hook(self.repo)
        self.assertTrue(ctx.startswith("URGENT STOP"), ctx[:80])
        self.assertIn("2026-11-19-x.md", ctx)
        self.assertNotIn("log.md", ctx)

    def test_git_ahead_line_only_when_dirty(self):
        repo = os.path.join(self.tmp, "Real")
        subprocess.run(["git", "init", "-q", repo], check=True)
        write(os.path.join(repo, "master.md"), "# Real\n")
        write(os.path.join(repo, ".gitignore"), "master.md\n")
        git = ["git", "-C", repo, "-c", "user.name=t", "-c", "user.email=t@example.com"]
        subprocess.run(git + ["add", ".gitignore"], check=True)
        subprocess.run(git + ["commit", "-q", "-m", "init", "--date", "2026-01-01T00:00:00"], check=True,
                       env={**os.environ, "GIT_COMMITTER_DATE": "2026-01-01T00:00:00"})
        write(os.path.join(self.tmp, "Real-handoffs", "roadmap-r", "ROADMAP.md"), ROADMAP.format(status="Active"))
        self.assertNotIn("Git is ahead", self.run_hook(repo))
        write(os.path.join(repo, "new.txt"), "x\n")
        self.assertIn("Git is ahead of the docs: 1 uncommitted change(s)", self.run_hook(repo))

    def test_bad_input_never_fails(self):
        r = subprocess.run([sys.executable, SCRIPT], input="not json", capture_output=True, text=True)
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout, "")


if __name__ == "__main__":
    unittest.main()
