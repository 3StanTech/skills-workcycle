#!/usr/bin/env python3
"""Block implementer launches while the current user turn is create-plan or explore.

Incident 2026-09-19: /create-plan ... orchestrate grok 4.6 medium supersoldiers
still launched Wave 0. Same-message implementer roster does not waive plan-only.
A later /implement (or explicit now-implement) is a new turn and is allowed.

Mock round: a typed /explore-design turn sets the flag to "mocks". Subagents are then
allowed, and headless launches only with --cwd set to an existing folder outside every
git work tree (mocks never touch product source). A later /implement clears the flag.
An /explore turn whose owner answers explore's step-0 question with "Switch to
explore-design" is upgraded to the mock round the same way.

Incident 2026-10-14: the turn text read from the transcript is the expanded skill body,
which quotes "/create-plan"; a typed /explore-design turn was blocked. The flag written
from the typed prompt decides the mode; transcript text is only a fallback without one.
Incident 2026-10-14 (later): hand-back text read as the typed prompt; the fallback now skips injected records.

Incident INC-3 (2026-10-14): the flag is session-wide, so read-only research launches
were blocked too. Read-only launches (a wrapper run with --lane A, or a wrapper help or
version call) now pass in plan-only turns. A typed /work-audit clears the flag like
/implement, flags older than 7 days are pruned, and CREATE_PLAN_STATE_DIR moves the
state directory (tests use a temp dir).
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

STATE_DIR = Path(os.environ.get("CREATE_PLAN_STATE_DIR", Path.home() / ".agents" / "state" / "create-plan-active"))
STALE_SECONDS = 7 * 24 * 3600
# /explore is plan-only as well: it writes a discovery doc, never code.
CREATE_PLAN = re.compile(
    r"(?:^|[\s\"'`])(?:/|\$|\\)(?:create-plan|explore(?!-design))\b",
    re.IGNORECASE,
)
IMPLEMENT = re.compile(
    r"(?:^|[\s\"'`])(?:/|\$|\\)implement\b"
    r"|(?:^|[\s\"'`])(?:now implement|implement the plan|execute the plan)\b",
    re.IGNORECASE,
)
WORK_AUDIT = re.compile(r"(?:^|[\s\"'`])(?:/|\$|\\)work-audit\b", re.IGNORECASE)
EXPLORE_DESIGN = re.compile(r"(?:^|[\s\"'`])(?:/|\$|\\)explore-design\b", re.IGNORECASE)
EXPLORE = re.compile(r"(?:^|[\s\"'`])(?:/|\$|\\)explore(?!-design)\b", re.IGNORECASE)
# The option label explore's step 0 offers; the owner's pick of it opens the mock round.
SWITCH_ANSWER = re.compile(r"^\s*switch to /?explore-design\b", re.IGNORECASE)
WRAPPER = re.compile(r"^run-(?:grok|codex|claude)\.sh$")
# Read-only research subagents stay allowed while planning; anything that can write or launch does not.
READ_ONLY_AGENTS = {"Explore", "Plan"}


def _launch_guard():
    """Reuse the headless launch guard's command parser (segments, heredoc handling); None when it is not installed."""
    import importlib.util
    # Installed, the parser is a sibling; a staged copy resolves it from the real hooks dir.
    path = Path(__file__).with_name("headless-launch-guard.py")
    if not path.exists():
        path = Path.home() / ".agents" / "hooks" / "headless-launch-guard.py"
    if not path.exists():
        return None  # Workcycle without Orchestration: no launch detection
    spec = importlib.util.spec_from_file_location("headless_launch_guard", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def launch_segments(cmd: str) -> list[list[str]]:
    """Token lists of the segments that launch a wrapper or raw engine CLI."""
    guard = _launch_guard()
    if guard is None:
        return []
    found = []
    for segment in guard.segments(guard.strip_data_heredocs(cmd)):
        toks = guard.words(segment)
        while toks and (toks[0] in guard.KEYWORDS or toks[0] in guard.PREFIXES or guard.ASSIGN.match(toks[0])):
            toks.pop(0)
        if not toks:
            continue
        exe = os.path.basename(toks[0])
        if exe in guard.SHELLS and len(toks) > 1 and WRAPPER.match(os.path.basename(toks[1])):
            found.append(toks)
        elif WRAPPER.match(exe) or guard.verdict(segment):
            found.append(toks)
    return found


def is_launch(cmd: str) -> bool:
    return bool(launch_segments(cmd))


def read_only_launch(cmd: str) -> bool:
    """Every launching segment runs a wrapper directly with --lane A, or only asks it for help/version."""
    for toks in launch_segments(cmd):
        if not WRAPPER.match(os.path.basename(toks[0])):
            return False  # raw engine CLI, or a wrapper run through a shell
        args = toks[1:]
        if {"-h", "--help", "--version"} & set(args) and not any(a.startswith("--prompt") for a in args):
            continue
        lanes = [args[i + 1] for i, a in enumerate(args[:-1]) if a == "--lane"]
        if not lanes or lanes[-1] != "A":  # the wrappers keep the last --lane value
            return False
    return True


def in_git_tree(path: str) -> bool:
    try:
        out = subprocess.run(["git", "-C", os.path.expanduser(path), "rev-parse", "--is-inside-work-tree"],
                             capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.TimeoutExpired):
        return True
    return out.returncode == 0 and out.stdout.strip() == "true"


def mock_launch_allowed(cmd: str) -> bool:
    """Every launching segment must name a --cwd that exists outside any git work tree."""
    for toks in launch_segments(cmd):
        cwd = None
        for i, tok in enumerate(toks):
            if tok == "--cwd" and i + 1 < len(toks):
                cwd = toks[i + 1]
            elif tok.startswith("--cwd="):
                cwd = tok.split("=", 1)[1]
        if not cwd or not os.path.isdir(os.path.expanduser(cwd)) or in_git_tree(cwd):
            return False
    return True


def flag_path(session_id: str) -> Path:
    safe = re.sub(r"[^A-Za-z0-9._-]", "_", session_id or "unknown")
    return STATE_DIR / safe


def prune_stale_flags() -> None:
    cutoff = time.time() - STALE_SECONDS
    for flag in STATE_DIR.iterdir():
        try:
            if flag.is_file() and flag.stat().st_mtime < cutoff:
                flag.unlink()
        except OSError:
            pass


HARNESS_WRAPPERS = ("<system-reminder", "<agent-message", "<task-notification", "<cross-session-message")
COMMAND_NAME = re.compile(r"<command-name>(.*?)</command-name>", re.DOTALL)
COMMAND_ARGS = re.compile(r"<command-args>(.*?)</command-args>", re.DOTALL)


def typed_text(rec: dict) -> str | None:
    """The owner's typed prompt in a transcript user record, or None for anything the harness injected."""
    if rec.get("isMeta") or rec.get("toolUseResult") is not None:
        return None
    msg = rec.get("message") or rec.get("content") or rec
    content = msg.get("content", "") if isinstance(msg, dict) else msg
    if isinstance(content, list):
        parts = []
        for part in content:
            if isinstance(part, dict) and part.get("type") in {"tool_result", "function_call_output"}:
                return None  # a tool or subagent hand-back, not a prompt
            if isinstance(part, dict) and part.get("type") in {"text", "input_text"}:
                parts.append(str(part.get("text") or ""))
            elif isinstance(part, str):
                parts.append(part)
        content = "\n".join(parts)
    text = str(content).strip()
    if text.startswith("<command-message>") or text.startswith("<command-name>"):
        name = COMMAND_NAME.search(text)
        if not name:
            return None
        args = COMMAND_ARGS.search(text)
        return (name.group(1).strip() + " " + (args.group(1).strip() if args else "")).strip()
    if not text or text.startswith(HARNESS_WRAPPERS) or text.startswith("Base directory for this skill"):
        return None
    return text


def last_user_text(data: dict) -> str:
    """The payload's typed prompt, else the newest typed prompt in the transcript (never injected text)."""
    prompt = data.get("prompt") or data.get("user_prompt") or ""
    if isinstance(prompt, str) and prompt.strip():
        return prompt
    path = data.get("transcript_path")
    if not path:
        return ""
    try:
        with open(path, encoding="utf-8") as f:
            lines = f.readlines()
    except OSError:
        return ""
    for line in reversed(lines):
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(rec, dict):
            continue
        role = str(rec.get("role") or rec.get("type") or "").lower()
        if role in {"user", "human"}:
            text = typed_text(rec)
            if text is not None:
                return text
    return ""


def owner_switched_to_design(data: dict) -> bool:
    """True when, since the last typed prompt, the owner answered AskUserQuestion with the switch."""
    path = data.get("transcript_path")
    if not path:
        return False
    try:
        with open(path, encoding="utf-8") as f:
            lines = f.readlines()
    except OSError:
        return False
    for line in reversed(lines):
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        if rec.get("type") != "user":
            continue
        result = rec.get("toolUseResult")
        if isinstance(result, dict) and isinstance(result.get("answers"), dict):
            if any(SWITCH_ANSWER.search(str(v)) for v in result["answers"].values()):
                return True
            continue
        content = (rec.get("message") or {}).get("content")
        if isinstance(content, str) and not rec.get("isMeta"):
            return False  # reached the typed prompt that opened this turn
    return False


def command_text(data: dict) -> str:
    tool_input = data.get("tool_input") or {}
    if isinstance(tool_input, dict):
        return str(tool_input.get("command") or tool_input.get("prompt") or "")
    return ""


def is_create_plan_turn(text: str, session_id: str) -> bool:
    """The session's flag decides; without one, only a typed plan-only command counts."""
    if flag_path(session_id).exists():
        return True
    return bool(CREATE_PLAN.search(text or "") or EXPLORE_DESIGN.search(text or ""))


def block(msg: str) -> None:
    sys.stderr.write(msg.rstrip() + "\n")
    sys.exit(2)


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    event = str(data.get("hook_event_name") or data.get("event") or "")
    session_id = str(data.get("session_id") or "")
    text = last_user_text(data)
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    path = flag_path(session_id)

    if event in {"UserPromptSubmit", "user_prompt_submit", "beforeSubmitPrompt"}:
        prune_stale_flags()
        if EXPLORE_DESIGN.search(text):
            path.write_text("mocks\n", encoding="utf-8")
        elif EXPLORE.search(text):
            path.write_text("explore\n", encoding="utf-8")
        elif CREATE_PLAN.search(text):
            path.write_text("create-plan\n", encoding="utf-8")
        elif (IMPLEMENT.search(text) or WORK_AUDIT.search(text)) and path.exists():
            path.unlink()
        sys.exit(0)

    if event and event not in {
        "PreToolUse",
        "preToolUse",
        "beforeShellExecution",
        "beforeMCPExecution",
    }:
        sys.exit(0)

    cmd = command_text(data)
    tool = str(data.get("tool_name") or "")
    # Patch contents are file data, even when the host calls the field command.
    # This guard prevents worker launches, not the writing of a plan document.
    if tool in {"apply_patch", "functions.apply_patch"}:
        sys.exit(0)
    if not cmd and "subagent" not in tool.lower() and "Agent" not in tool:
        sys.exit(0)

    if not is_create_plan_turn(text, session_id):
        sys.exit(0)

    # Same-message /implement does not waive create-plan on this turn.
    tool_input = data.get("tool_input") or {}
    if "subagent" in tool.lower() or tool in {"Agent", "Task"}:
        kind = tool_input.get("subagent_type") if isinstance(tool_input, dict) else None
        launch = kind not in READ_ONLY_AGENTS
    else:
        launch = is_launch(str(tool_input.get("command") or "") if isinstance(tool_input, dict) else cmd)
    if not launch:
        sys.exit(0)

    mode = path.read_text(encoding="utf-8").strip() if path.exists() else ""
    if mode == "explore" and owner_switched_to_design(data):
        path.write_text("mocks\n", encoding="utf-8")
        mode = "mocks"
    # A typed prompt in the payload re-arms plan-only; transcript text (skill bodies) never does.
    typed = data.get("prompt") or data.get("user_prompt") or ""
    typed = typed if isinstance(typed, str) else ""
    if (mode == "mocks" and not CREATE_PLAN.search(typed)) or (
        not mode and EXPLORE_DESIGN.search(text) and not CREATE_PLAN.search(text)
    ):
        if "subagent" in tool.lower() or tool in {"Agent", "Task"}:
            sys.exit(0)
        if mock_launch_allowed(str(tool_input.get("command") or "") if isinstance(tool_input, dict) else cmd):
            sys.exit(0)
        block(
            "BLOCKED: explore-design mock round. Headless launches must use a wrapper with --cwd set to "
            "an existing mocks folder outside every git work tree. Product source waits for /implement.\n"
            "Do not strip this guard or edit the flag file to bypass it."
        )

    if not ("subagent" in tool.lower() or tool in {"Agent", "Task"}) and read_only_launch(
        str(tool_input.get("command") or "") if isinstance(tool_input, dict) else cmd
    ):
        sys.exit(0)

    block(
        "BLOCKED: create-plan is plan-only. A same-message implementer roster "
        "(model, effort, supersoldiers, orchestrate) names who should implement later; "
        "it does not start code. Finish the plan, then run /implement <path> in a new turn.\n"
        "Read-only launches (wrapper --lane A, Explore/Plan agents) are allowed; "
        "writes wait for a later /work-audit or /implement prompt.\n"
        "Do not strip this guard or edit the flag file to bypass it."
    )


if __name__ == "__main__":
    main()
