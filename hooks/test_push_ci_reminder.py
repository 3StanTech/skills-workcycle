#!/usr/bin/env python3
"""Candidate commands are data; none is executed."""
import json
import subprocess
import unittest
from pathlib import Path

HOOK = Path(__file__).with_name("push-ci-reminder.py")


def run(payload: str) -> subprocess.CompletedProcess:
    return subprocess.run(["python3", str(HOOK)], input=payload, text=True, capture_output=True)


def reminds(command: str, response=None) -> bool:
    event = {"tool_input": {"command": command}}
    if response is not None:
        event["tool_response"] = response
    r = run(json.dumps(event))
    assert r.returncode == 0, r.stderr
    if not r.stdout.strip():
        return False
    out = json.loads(r.stdout)["hookSpecificOutput"]
    assert out["hookEventName"] == "PostToolUse"
    return "wait-ci-deploy.sh" in out["additionalContext"]


class Pushes(unittest.TestCase):
    def test_reminds(self):
        for c in ["git push", "git push origin main", "npm test && git push origin main",
                  "git -C /repo push", "GIT_SSH_COMMAND=x git push", "git add -A; git commit -m x; git push"]:
            self.assertTrue(reminds(c), c)

    def test_silent(self):
        for c in ["git status", "git pushd", "echo git push", "git push --dry-run origin main",
                  "gh pr create", "git log --oneline"]:
            self.assertFalse(reminds(c), c)

    def test_failed_push_is_silent(self):
        self.assertFalse(reminds("git push", {"is_error": True}))

    def test_malformed_input(self):
        for payload in ["", "not json", "[]", json.dumps({"tool_input": {"command": 5}})]:
            r = run(payload)
            self.assertEqual(r.returncode, 0)
            self.assertEqual(r.stdout.strip(), "")


if __name__ == "__main__":
    unittest.main()
