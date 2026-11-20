"""Tests for publish_workcycle.py. Run: python3 -m unittest discover -s skills/handoff/tests"""

import os
import shutil
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

    def remote_hook(self, name, body):
        path = os.path.join(self.remote, "hooks", name)
        write(path, "#!/bin/sh\n" + body + "\n")
        os.chmod(path, 0o755)

    def reject_pushes(self, on=True):
        """A push that fails at the remote while it is on (a server outage, a rejected hook)."""
        flag = os.path.join(self.tmp, "reject")
        if on:
            write(flag, "")
            self.remote_hook("pre-receive", f'[ -e "{flag}" ] && exit 1\nexit 0')
        elif os.path.exists(flag):
            os.remove(flag)

    def commit_all(self, msg):
        self.git("add", "-A")
        self.git("commit", "-q", "-m", msg)

    def test_pushes_only_the_named_work_folder(self):
        self.config()
        write(os.path.join(self.root, "Other", "notes.md"), "untouched\n")
        code, out = self.run_script(self.work)
        self.assertEqual(code, 0, out)
        files = self.remote_files()
        self.assertIn("App's Site/2026-11-20-demo/plans/2026-11-20-demo.md", files)
        self.assertNotIn("Other/notes.md", files)
        self.assertIn("?? Other/", self.git("status", "--short"))

    def test_detached_head_is_refused_before_committing(self):
        # a fresh cloud clone starts detached: a commit there never reaches the remote
        self.config()
        head = self.git("rev-parse", "HEAD")
        self.git("checkout", "-q", "--detach")
        code, out = self.run_script(self.work)
        self.assertEqual(code, 4, out)
        self.assertIn("HEAD is detached", out)
        self.assertEqual(self.git("rev-parse", "HEAD"), head)
        self.assertEqual(self.remote_files(), ["README.md"])

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


    def test_negated_or_vague_consent_asks(self):
        for text in ("No standing go. Ask me first.", "standing go is off", "ask first; not a standing go"):
            self.config(publish=text)
            code, out = self.run_script(self.work)
            self.assertEqual(code, 3, (text, out))
        self.assertEqual(self.remote_files(), ["README.md"])

    def test_one_time_owner_approval_publishes(self):
        self.config(publish=None)
        code, out = self.run_script("--owner-approved", self.work)
        self.assertEqual(code, 0, out)
        self.assertIn("App's Site/2026-11-20-demo/plans/2026-11-20-demo.md", self.remote_files())

    def test_refuses_the_whole_root(self):
        self.config()
        code, out = self.run_script(self.root)
        self.assertEqual(code, 2, out)
        self.assertEqual(self.remote_files(), ["README.md"])

    def test_pathspec_characters_are_literal(self):
        self.config()
        literal = os.path.join(self.root, "App's Site", "2026-11-20-[x]*")
        write(os.path.join(literal, "a.md"), "inside\n")
        write(os.path.join(self.root, "App's Site", "2026-11-20-xy", "b.md"), "a glob would catch this\n")
        code, out = self.run_script(literal)
        self.assertEqual(code, 0, out)
        files = self.remote_files()
        self.assertIn("App's Site/2026-11-20-[x]*/a.md", files)
        self.assertNotIn("App's Site/2026-11-20-xy/b.md", files)

    def test_existing_staging_is_refused_and_kept(self):
        self.config()
        write(os.path.join(self.root, "Other", "staged.md"), "mine\n")
        self.git("add", "Other/staged.md")
        code, out = self.run_script(self.work)
        self.assertEqual(code, 4, out)
        self.assertIn("already staged", out)
        self.assertEqual(self.git("diff", "--cached", "--name-only"), "Other/staged.md")
        self.assertEqual(self.remote_files(), ["README.md"])

    def test_dry_run_and_refusal_leave_the_index_empty(self):
        self.config()
        self.assertEqual(self.run_script("--dry-run", self.work)[0], 0)
        self.assertEqual(self.git("diff", "--cached", "--name-only"), "")
        write(os.path.join(self.work, "handoffs", "h.md"), "password = " + "x" * 16 + "\n")
        self.assertEqual(self.run_script(self.work)[0], 5)
        self.assertEqual(self.git("diff", "--cached", "--name-only"), "")

    def test_refuses_secret_forms_and_binary_files(self):
        self.config()
        for name, data in (("db.md", b"postgres://app:hunter2hunter2@db.example.com/x\n"),
                           ("shot.png", b"\x89PNG\x00\x00 token=" + b"A" * 20 + b"\x00")):
            path = os.path.join(self.work, "runs", name)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "wb") as f:
                f.write(data)
            code, out = self.run_script(self.work)
            self.assertEqual(code, 5, (name, out))
            os.remove(path)
        self.assertEqual(self.remote_files(), ["README.md"])

    def test_earlier_commit_outside_scope_is_refused(self):
        self.config()
        write(os.path.join(self.root, "Other", "private.md"), "not this stage\n")
        self.git("add", "Other/private.md")
        self.git("commit", "-q", "-m", "unrelated local work")
        code, out = self.run_script(self.work)
        self.assertEqual(code, 4, out)
        self.assertIn("Other/private.md", out)
        self.assertEqual(self.remote_files(), ["README.md"])

    def test_retry_after_failed_push_pushes_the_stranded_commit(self):
        self.config()
        self.reject_pushes()
        code, out = self.run_script(self.work)
        self.assertEqual(code, 4, out)
        self.assertIn("push failed", out)
        self.reject_pushes(False)
        code, out = self.run_script(self.work)
        self.assertEqual(code, 0, out)
        self.assertIn("App's Site/2026-11-20-demo/plans/2026-11-20-demo.md", self.remote_files())

    def test_push_goes_to_the_upstream_branch_only(self):
        self.config()
        self.git("config", "remote.origin.push", "refs/heads/main:refs/heads/elsewhere")
        code, out = self.run_script(self.work)
        self.assertEqual(code, 0, out)
        self.assertIn("App's Site/2026-11-20-demo/plans/2026-11-20-demo.md", self.remote_files())
        branches = self.git("branch", "--list", cwd=self.remote)
        self.assertNotIn("elsewhere", branches)

    # Re-check 1 leftovers (SW1, SW2, SW3, SW7, SW8, SW-NEW-1, SW-NEW-2, SW-NEW-4)

    def test_consent_needs_a_positive_line_in_the_section(self):
        for text in ("standing go: no", "- standing go: off, ask me first", "Standing go: NONE", "standing go: false",
                     "standing go: disabled", "standing go:", "```\nstanding go: yes\n```",
                     "### standing go: yes", "standing go: yes\nstanding go: no"):
            self.config(publish=text)
            code, out = self.run_script(self.work)
            self.assertEqual(code, 3, (text, out))
        path = os.path.join(self.tmp, ".agents", "local", "workcycle.md")
        write(path, f"## Workcycle root\n\n`{self.root}`\n\n## Workcycle publish\n\nask first\n\n"
                    "## Other\n\nstanding go: yes\n")  # the line outside its section
        self.assertEqual(self.run_script(self.work)[0], 3)
        self.assertEqual(self.remote_files(), ["README.md"])
        self.config(publish="- standing go: commit and push the stage's work folder")
        self.assertEqual(self.run_script(self.work)[0], 0)

    def test_ambiguous_push_destination_is_refused(self):
        self.config()
        head = self.git("rev-parse", "HEAD")
        other = os.path.join(self.tmp, "other.git")
        self.git("init", "-q", "--bare", "-b", "main", other, cwd=self.tmp)
        for urls in ([other], [self.remote, other]):
            self.git("config", "--unset-all", "remote.origin.pushurl", cwd=self.root) if urls != [other] else None
            for u in urls:
                self.git("config", "--add", "remote.origin.pushurl", u)
            code, out = self.run_script(self.work)
            self.assertEqual(code, 4, (urls, out))
            self.assertIn("push destination", out)
        self.assertEqual(self.git("rev-parse", "HEAD"), head)  # nothing committed
        self.assertEqual(self.remote_files(), ["README.md"])

    def test_push_is_confirmed_on_the_remote_not_the_tracking_ref(self):
        self.config()
        old = self.git("rev-parse", "HEAD")
        self.remote_hook("post-receive", f"git update-ref refs/heads/main {old}")  # accepted, then undone
        code, out = self.run_script(self.work)
        self.assertEqual(code, 4, out)
        self.assertIn("does not show", out)

    def test_each_outgoing_commit_is_checked(self):
        self.config()
        write(os.path.join(self.root, "Other", "a.md"), "pushed before\n")
        self.git("add", "Other/a.md")
        self.git("commit", "-q", "-m", "other")
        self.git("push", "-q")
        start = self.git("rev-parse", "HEAD")
        cases = (
            ("added then removed outside", lambda: (write(os.path.join(self.root, "Other", "x.md"), "private\n"),
                                                    self.commit_all("add"), os.remove(os.path.join(self.root, "Other", "x.md")),
                                                    self.commit_all("remove")), 4),
            ("secret added then removed", lambda: (write(os.path.join(self.work, "h.md"), "token ghp_" + "a" * 36 + "\n"),
                                                   self.commit_all("add"), write(os.path.join(self.work, "h.md"), "clean\n"),
                                                   self.commit_all("clean")), 5),
            ("renamed from outside", lambda: (self.git("mv", "Other/a.md", os.path.join("App's Site", "2026-11-20-demo", "a.md")),
                                              self.git("commit", "-q", "-m", "move")), 4),
        )
        for name, make, expected in cases:
            make()
            code, out = self.run_script(self.work)
            self.assertEqual(code, expected, (name, out))
            self.git("reset", "-q", "--hard", start)
            write(os.path.join(self.work, "plans", "2026-11-20-demo.md"), "# Plan\n")
        self.assertEqual(sorted(self.remote_files()), ["Other/a.md", "README.md"])

    def test_incoming_commits_are_not_outgoing(self):
        self.config()
        other = os.path.join(self.tmp, "other-clone")
        self.git("clone", "-q", self.remote, other, cwd=self.tmp)
        write(os.path.join(other, "General", "x.md"), "from the cloud\n")
        self.git("add", "-A", cwd=other)
        self.git("commit", "-q", "-m", "cloud", cwd=other)
        self.git("push", "-q", cwd=other)
        self.git("fetch", "-q")  # behind by one; nothing local is unpushed
        code, out = self.run_script("--dry-run", self.work)
        self.assertEqual(code, 0, out)
        self.assertNotIn("earlier commit", out)

    def test_user_diff_config_cannot_hide_a_secret(self):
        self.config()
        write(os.path.join(self.work, "handoffs", "h.md"), "token ghp_" + "a" * 36 + "\n")
        write(os.path.join(self.root, ".git", "info", "attributes"), "* diff=hide\n")
        for key, value in (("color.ui", "always"), ("diff.external", "true"), ("diff.hide.textconv", "true"),
                           ("diff.noprefix", "true")):
            self.git("config", key, value)
            code, out = self.run_script(self.work)
            self.assertEqual(code, 5, (key, out))
            self.git("config", "--unset", key)
        self.assertEqual(self.remote_files(), ["README.md"])

    def test_retry_of_an_archive_move_accepts_the_old_path(self):
        self.config()
        self.assertEqual(self.run_script(self.work)[0], 0)
        archive = os.path.join(self.root, "App's Site", "_archive", "2026-11-20-demo")
        os.makedirs(os.path.dirname(archive))
        shutil.move(self.work, archive)
        self.reject_pushes()
        self.assertEqual(self.run_script(self.work, archive)[0], 4)
        self.reject_pushes(False)
        code, out = self.run_script(self.work, archive)  # the old path is gone and no longer tracked
        self.assertEqual(code, 0, out)
        files = self.remote_files()
        self.assertIn("App's Site/_archive/2026-11-20-demo/plans/2026-11-20-demo.md", files)
        self.assertNotIn("App's Site/2026-11-20-demo/plans/2026-11-20-demo.md", files)

    def test_head_moving_during_the_publish_is_refused(self):
        # a fake git runs a concurrent commit (outside the stage's paths) just before the publish commits
        self.config()
        bindir, mark = os.path.join(self.tmp, "bin"), os.path.join(self.tmp, "moved")
        write(os.path.join(self.root, "Other", "c.md"), "concurrent\n")
        real = shutil.which("git")
        write(os.path.join(bindir, "git"), f"""#!/bin/sh
case " $* " in *" commit "*|*" commit-tree "*)
  if [ ! -e "{mark}" ]; then : > "{mark}"
    env -u GIT_INDEX_FILE "{real}" -C "{self.root}" add Other/c.md
    env -u GIT_INDEX_FILE "{real}" -C "{self.root}" commit -q -m concurrent
  fi;;
esac
exec "{real}" "$@"
""")
        os.chmod(os.path.join(bindir, "git"), 0o755)
        self.env["PATH"] = bindir + os.pathsep + self.env["PATH"]
        code, out = self.run_script(self.work)
        self.assertEqual(code, 4, out)
        self.assertIn("HEAD moved", out)
        self.assertIn("Other/c.md", self.git("ls-tree", "-r", "--name-only", "HEAD"))  # the concurrent work kept
        self.assertEqual(self.remote_files(), ["README.md"])

    def test_commit_hooks_run_and_can_refuse(self):
        self.config()
        hook = os.path.join(self.root, ".git", "hooks", "pre-commit")
        write(hook, "#!/bin/sh\necho 'blocked by the root hook' >&2\nexit 1\n")
        os.chmod(hook, 0o755)
        code, out = self.run_script(self.work)
        self.assertEqual(code, 4, out)
        self.assertIn("blocked by the root hook", out)
        self.assertEqual(self.git("diff", "--cached", "--name-only"), "")
        self.assertEqual(self.remote_files(), ["README.md"])

    def test_carriage_return_cannot_hide_a_secret(self):
        self.config()
        path = os.path.join(self.work, "runs", "log.md")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        for sep in (b"\r", b"\x0c"):
            with open(path, "wb") as f:
                f.write(b"ok" + sep + b"token = " + b"A" * 20 + b"\n")
            code, out = self.run_script(self.work)
            self.assertEqual(code, 5, (sep, out))

    def test_consent_needs_an_explicit_yes_outside_code(self):
        for text in ("standing go: ask me first", "standing go: not granted", "    standing go: yes (indented code)",
                     "```md\nstanding go: yes\n```text\nstanding go: yes\n```"):
            self.config(publish=text)
            code, out = self.run_script(self.work)
            self.assertEqual(code, 3, (text, out))
        self.config(publish="standing go: yes")
        self.assertEqual(self.run_script(self.work)[0], 0)

    def test_commit_is_verified_after_hooks_run(self):
        self.config()
        write(os.path.join(self.root, "Other", "swept.md"), "not this stage\n")
        hook = os.path.join(self.root, ".git", "hooks", "pre-commit")
        write(hook, "#!/bin/sh\ngit add Other/swept.md\n")  # a hook that stages more than the stage's paths
        os.chmod(hook, 0o755)
        code, out = self.run_script(self.work)
        self.assertEqual(code, 4, out)
        self.assertIn("Other/swept.md", out)
        self.assertEqual(self.remote_files(), ["README.md"])

    def test_added_line_that_looks_like_a_header_is_scanned(self):
        self.config()
        write(os.path.join(self.work, "plans", "notes.md"), "++ token = " + "B" * 20 + "\n")  # "+" + this = "+++ "
        code, out = self.run_script(self.work)
        self.assertEqual(code, 5, out)

    def test_never_tracked_missing_path_is_skipped(self):
        self.config()
        gone = os.path.join(self.root, "App's Site", "2026-11-01-old")  # an archive source that was never committed
        code, out = self.run_script(gone, self.work)
        self.assertEqual(code, 0, out)
        self.assertIn("skipped", out)
        self.assertIn("App's Site/2026-11-20-demo/plans/2026-11-20-demo.md", self.remote_files())

    def test_failed_cleanup_is_reported(self):
        self.config()
        bindir = os.path.join(self.tmp, "bin")
        real = shutil.which("git")
        write(os.path.join(bindir, "git"), f"""#!/bin/sh
case " $* " in *" reset "*) echo "fatal: index.lock exists" >&2; exit 128;; esac
exec "{real}" "$@"
""")
        os.chmod(os.path.join(bindir, "git"), 0o755)
        self.env["PATH"] = bindir + os.pathsep + self.env["PATH"]
        code, out = self.run_script("--dry-run", self.work)
        self.assertIn("could not unstage", out)

    def test_consent_ignores_comments_nested_code_and_partial_grants(self):
        for text in ("<!-- standing go: yes -->", "- ```\n  standing go: yes\n  ```",
                     "standing go: commit locally, but ask before you push"):
            self.config(publish=text)
            code, out = self.run_script(self.work)
            self.assertEqual(code, 3, (text, out))

if __name__ == "__main__":
    unittest.main()
