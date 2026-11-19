"""Tests for publish_workcycle.py. Run: python3 -m unittest discover -s skills/handoff/tests"""

import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "..", "scripts", "publish_workcycle.py")


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


class PublishWorkcycle(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.env = {**os.environ, "HOME": self.tmp, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.com",
                    "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.com"}
        self.remote = os.path.join(self.tmp, "remote.git")
        self.root = os.path.join(self.tmp, "Workcycle Files")  # a space, like the real root
        self.git("init", "-q", "--bare", "-b", "main", self.remote, cwd=self.tmp)
        self.git("clone", "-q", self.remote, self.root, cwd=self.tmp)
        write(os.path.join(self.root, "README.md"), "# WF\n")
        self.git("add", "README.md")
        self.git("commit", "-q", "-m", "init")
        self.git("push", "-q", "-u", "origin", "main")
        self.work = os.path.join(self.root, "App's Site", "2026-11-20-demo")
        write(os.path.join(self.work, "plans", "2026-11-20-demo.md"), "# Plan\n")

    def git(self, *args, cwd=None):
        return subprocess.run(["git", *args], cwd=cwd or self.root, env=self.env, check=True,
                              capture_output=True, text=True).stdout.strip()

    def config(self, publish="standing go: commit and push the stage's work folder after the secret check"):
        text = f"# Local\n\n## Workcycle root\n\n`{self.root}`\n\n"
        if publish is not None:
            text += f"## Workcycle publish\n\n{publish}\n\n"
        write(os.path.join(self.tmp, ".agents", "local", "workcycle.md"), text + "## Other\n")

    def run_script(self, *args):
        r = subprocess.run([sys.executable, SCRIPT, "--stage", "plan", *args], env=self.env,
                           capture_output=True, text=True, timeout=30)
        return r.returncode, r.stdout

    def remote_files(self):
        return self.git("ls-tree", "-r", "--name-only", "main", cwd=self.remote).splitlines()

    def test_pushes_only_the_named_work_folder(self):
        self.config()
        write(os.path.join(self.root, "Other", "notes.md"), "untouched\n")
        code, out = self.run_script(self.work)
        self.assertEqual(code, 0, out)
        files = self.remote_files()
        self.assertIn("App's Site/2026-11-20-demo/plans/2026-11-20-demo.md", files)
        self.assertNotIn("Other/notes.md", files)
        self.assertIn("?? Other/", self.git("status", "--short"))

    def test_without_standing_go_asks(self):
        self.config(publish=None)
        code, out = self.run_script(self.work)
        self.assertEqual(code, 3)
        self.assertIn("ask the owner", out)
        self.assertEqual(self.remote_files(), ["README.md"])

    def test_refuses_secret_content(self):
        self.config()
        write(os.path.join(self.work, "handoffs", "h.md"), "token ghp_" + "a" * 36 + "\n")
        code, out = self.run_script(self.work)
        self.assertEqual(code, 5, out)
        self.assertEqual(self.remote_files(), ["README.md"])
        self.assertEqual(self.git("diff", "--cached", "--name-only"), "")  # nothing left staged

    def test_refuses_path_outside_root(self):
        self.config()
        outside = os.path.join(self.tmp, "elsewhere.md")
        write(outside, "x\n")
        self.assertEqual(self.run_script(outside)[0], 2)

    def test_pulls_before_commit_and_reports_nothing_new(self):
        self.config()
        other = os.path.join(self.tmp, "other-clone")
        self.git("clone", "-q", self.remote, other, cwd=self.tmp)
        write(os.path.join(other, "General", "x.md"), "from the cloud\n")
        self.git("add", "-A", cwd=other)
        self.git("commit", "-q", "-m", "cloud", cwd=other)
        self.git("push", "-q", cwd=other)
        code, out = self.run_script(self.work)
        self.assertEqual(code, 0, out)
        self.assertIn("General/x.md", self.remote_files())
        self.assertIn("App's Site/2026-11-20-demo/plans/2026-11-20-demo.md", self.remote_files())
        code, out = self.run_script(self.work)
        self.assertEqual(code, 0)
        self.assertIn("nothing to publish", out)


if __name__ == "__main__":
    unittest.main()
