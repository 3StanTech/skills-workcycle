"""Boundary tests for work-audit triage rules, against throwaway git repos (no mocks)."""
import json
import os
import subprocess
import sys
import tempfile
import unittest

SCRIPT = os.path.join(os.path.dirname(__file__), "..", "scripts", "triage.py")
NO_CLIENT = ["--client-root", "/nonexistent-client-root"]


def run(*args):
    p = subprocess.run([sys.executable, SCRIPT, *args], capture_output=True, text=True)
    return p.returncode, p.stdout, p.stderr


def git(repo, *args):
    subprocess.run(["git", "-C", repo, "-c", "user.name=t", "-c", "user.email=t@t", *args],
                   check=True, capture_output=True)


class TriageTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def make_repo(self, name=None):
        self.n = getattr(self, "n", 0) + 1
        repo = os.path.join(self.tmp.name, name or f"r{self.n}")
        os.makedirs(repo)
        git(repo, "init", "-q")
        self.write(repo, "README.md", "base\n")
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "-m", "base")
        return repo

    def write(self, repo, rel, text):
        path = os.path.join(repo, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(text)

    def change(self, files):
        """files: {path: line_count_or_text}; returns (repo, range)."""
        repo = self.make_repo()
        for rel, body in files.items():
            self.write(repo, rel, body if isinstance(body, str) else "x\n" * body)
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "-m", "change")
        return repo, "HEAD~1..HEAD"

    def verdict(self, repo, rng, *extra):
        code, out, err = run("--repo", repo, "--range", rng, *NO_CLIENT, *extra)
        self.assertEqual(code, 0, err)
        return out

    def test_size_files_boundary(self):
        repo, rng = self.change({f"docs/f{i}.md": 1 for i in range(24)})
        self.assertIn("VERDICT: LIGHT", self.verdict(repo, rng))
        repo, rng = self.change({f"docs/f{i}.md": 1 for i in range(25)})
        out = self.verdict(repo, rng)
        self.assertIn("VERDICT: FULL", out)
        self.assertIn("size:", out)

    def test_size_lines_boundary(self):
        repo, rng = self.change({"docs/a.md": 799})
        self.assertIn("VERDICT: LIGHT", self.verdict(repo, rng))
        repo, rng = self.change({"docs/a.md": 800})
        self.assertIn("VERDICT: FULL", self.verdict(repo, rng))

    def test_docs_only_light(self):
        repo, rng = self.change({"docs/guide.md": 5})
        out = self.verdict(repo, rng)
        self.assertIn("VERDICT: LIGHT", out)
        self.assertIn("REASONS: none — no Full trigger", out)
        self.assertIn("files=1 lines=5 scope=range", out)

    def test_risky_categories(self):
        cases = {"data": "db/migrations/001.sql", "auth": "app/auth/login.ts",
                 "payments": "lib/stripe.ts", "secrets": ".env.example",
                 "deploy": ".github/workflows/ci.yml"}
        for cat, path in cases.items():
            with self.subTest(cat=cat):
                repo, rng = self.change({path: 1})
                out = self.verdict(repo, rng)
                self.assertIn("VERDICT: FULL", out)
                self.assertIn(f"{cat}: ", out)

    def test_near_misses_stay_light(self):
        repo, rng = self.change({"docs/authoring.md": 1, "src/components/Author.astro": 1})
        self.assertIn("VERDICT: LIGHT", self.verdict(repo, rng))

    def test_two_repos_full(self):
        a, rng = self.change({"docs/a.md": 1})
        b = self.make_repo("r2")
        code, out, _ = run("--repo", a, "--repo", b, "--range", rng, *NO_CLIENT)
        self.assertEqual(code, 2)  # r2 has no HEAD~1: bad range for the second repo
        self.write(b, "docs/b.md", "x\n")
        git(b, "add", "-A")
        git(b, "commit", "-q", "-m", "c")
        code, out, _ = run("--repo", a, "--repo", b, "--range", rng, *NO_CLIENT)
        self.assertEqual(code, 0)
        self.assertIn("VERDICT: FULL", out)
        self.assertIn("scope: 2 repos", out)

    def test_roadmap_scope_full(self):
        repo, rng = self.change({"docs/a.md": 1})
        out = self.verdict(repo, rng, "--scope-kind", "roadmap")
        self.assertIn("VERDICT: FULL", out)
        self.assertIn("scope: roadmap scope", out)

    def test_client_root_full(self):
        repo, rng = self.change({"docs/a.md": 1})
        code, out, _ = run("--repo", repo, "--range", rng, "--client-root", self.tmp.name)
        self.assertEqual(code, 0)
        self.assertIn("VERDICT: FULL", out)
        self.assertIn("client: ", out)

    def test_worktree_counts_untracked(self):
        repo = self.make_repo()
        self.write(repo, "docs/new.md", "a\nb\nc\n")
        code, out, _ = run("--repo", repo, "--worktree", *NO_CLIENT)
        self.assertEqual(code, 0)
        self.assertIn("files=1 lines=3 scope=session", out)

    def test_files_mode(self):
        a = os.path.join(self.tmp.name, "a.md")
        with open(a, "w") as f:
            f.write("1\n2\n")
        missing = os.path.join(self.tmp.name, "gone.md")
        code, out, _ = run("--files", a, missing, *NO_CLIENT)
        self.assertEqual(code, 0)
        self.assertIn("VERDICT: LIGHT", out)
        self.assertIn("files=2 lines=n/a", out)

    def test_files_no_base_dir_count_only_boundary(self):
        def files(n):
            out = []
            for i in range(n):
                p = os.path.join(self.tmp.name, f"d{n}", f"f{i}.md")
                os.makedirs(os.path.dirname(p), exist_ok=True)
                with open(p, "w") as f:
                    f.write("x\n" * 1000)
                out.append(p)
            return out
        _, out, _ = run("--files", *files(24), *NO_CLIENT)
        self.assertIn("VERDICT: LIGHT", out)
        _, out, _ = run("--files", *files(25), *NO_CLIENT)
        self.assertIn("VERDICT: FULL", out)
        self.assertIn("n/a changed lines", out)

    def test_files_base_dir_counts_real_diff(self):
        root = os.path.join(self.tmp.name, "root")
        base = os.path.join(self.tmp.name, "base")
        self.write(root, "a/one.md", "1\n2\n3\nEDIT\n5\n")
        self.write(base, "a/one.md", "1\n2\n3\n4\n5\n")      # 1 removed + 1 added = 2
        self.write(root, "two.md", "n1\nn2\n")                 # new file: 2
        self.write(base, "gone.md", "o1\no2\no3\n")           # deleted: 3
        paths = [os.path.join(root, "a/one.md"), os.path.join(root, "two.md"),
                 os.path.join(root, "gone.md")]
        code, out, err = run("--files", *paths, "--files-root", root, "--base-dir", base, *NO_CLIENT)
        self.assertEqual(code, 0, err)
        self.assertIn("files=3 lines=7", out)
        self.assertIn("VERDICT: LIGHT", out)

    def test_files_mode_client_rule(self):
        a = os.path.join(self.tmp.name, "a.md")
        with open(a, "w") as f:
            f.write("x\n")
        _, out, _ = run("--files", a, "--client-root", self.tmp.name)
        self.assertIn("VERDICT: FULL", out)
        self.assertIn("client: ", out)

    def test_worktree_from_subdirectory(self):
        repo = self.make_repo()
        self.write(repo, "sub/keep.txt", "k\n")
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "-m", "sub")
        self.write(repo, "sub/new.md", "a\nb\n")
        code, out, err = run("--repo", os.path.join(repo, "sub"), "--worktree", *NO_CLIENT)
        self.assertEqual(code, 0, err)
        self.assertIn("files=1 lines=2", out)

    def test_json_output(self):
        repo, rng = self.change({"lib/stripe.ts": 1})
        code, out, _ = run("--repo", repo, "--range", rng, "--json", *NO_CLIENT)
        data = json.loads(out)
        self.assertEqual(data["verdict"], "FULL")
        self.assertEqual(data["reasons"][0]["rule"], "payments")

    def test_bad_range_exit_2(self):
        repo = self.make_repo()
        code, _, err = run("--repo", repo, "--range", "nope..alsonope", *NO_CLIENT)
        self.assertEqual(code, 2)
        self.assertIn(repo, err)


if __name__ == "__main__":
    unittest.main()
