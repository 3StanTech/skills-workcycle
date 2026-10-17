#!/usr/bin/env python3
"""PostToolUse/Bash: after a successful `git push`, tell the agent to wait for CI and deploy.

The wait itself is ~/.agents/scripts/wait-ci-deploy.sh (full SHA, bounded). This hook only
adds context so a push outside /implement or develop is still followed by the wait.
Prints nothing and exits 0 for anything else, including malformed input.
"""
from __future__ import annotations

import json
import re
import sys

PUSH = re.compile(r"(?:^|[;&|]\s*|\n\s*)(?:\S+=\S+\s+)*git\s+(?:-C\s+\S+\s+)?push\b(?![^\n;&|]*--dry-run)")
NOTE = ("A git push just ran. Before reporting it done, run ~/.agents/scripts/wait-ci-deploy.sh "
        "in the foreground (from the pushed repo) and report its result; none-found or timeout is not a pass.")


def main() -> int:
    try:
        event = json.load(sys.stdin)
        command = event.get("tool_input", {}).get("command", "")
    except Exception:
        return 0
    if not isinstance(command, str) or not PUSH.search(command):
        return 0
    response = event.get("tool_response")
    if isinstance(response, dict) and (response.get("interrupted") or response.get("is_error")):
        return 0
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": NOTE}}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
