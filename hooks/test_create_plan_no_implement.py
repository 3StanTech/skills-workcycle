#!/usr/bin/env python3
import json
import os
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

SOURCE = Path(os.environ.get("CREATE_PLAN_GUARD_SCRIPT", Path.home() / ".agents/hooks/create-plan-no-implement.py"))
SCRIPT = SOURCE  # each test class points this at a copy with its own dependency setup
TEST_HOME = None  # HOME for the guard process; None keeps the real one
WRAPPER = str(Path.home() / ".agents/skills/headless/scripts/run-grok.sh")
CODEX = str(Path.home() / ".agents/skills/headless/scripts/run-codex.sh")
# Every case runs against a temp state dir; the real create-plan-active dir is never touched.
# Each test class owns its own (see Setup), so nothing outlives the class that created it.
STATE = None
state_dir = None


def run(payload):
    proc = subprocess.run(
        ["python3", str(SCRIPT)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        env={**os.environ, "CREATE_PLAN_STATE_DIR": STATE.name, **({"HOME": TEST_HOME} if TEST_HOME else {})},
    )
    return proc.returncode, proc.stderr


def main():
    code, err = run(
        {
            "hook_event_name": "PreToolUse",
            "session_id": "test-create-plan-hook",
            "prompt": "/create-plan compile lavish. orchestrate to grok 4.6 medium supersoldiers",
            "tool_name": "Bash",
            "tool_input": {"command": WRAPPER + " --model grok-4.6 --effort medium"},
        }
    )
    assert code == 2, (code, err)
    assert "plan-only" in err, err

    code, err = run(
        {
            "hook_event_name": "PreToolUse",
            "session_id": "test-create-plan-hook-2",
            "prompt": "/implement plans/2026-09-19-look-and-study-ux.md",
            "tool_name": "Bash",
            "tool_input": {"command": WRAPPER + " --model grok-4.6 --effort medium"},
        }
    )
    assert code == 0, (code, err)

    code, err = run(
        {
            "hook_event_name": "UserPromptSubmit",
            "session_id": "test-create-plan-flag",
            "prompt": "/create-plan foo",
        }
    )
    assert code == 0, (code, err)
    code, err = run(
        {
            "hook_event_name": "PreToolUse",
            "session_id": "test-create-plan-flag",
            "prompt": "",
            "tool_name": "Bash",
            "tool_input": {"command": WRAPPER + " --model grok-4.6 --effort medium"},
        }
    )
    assert code == 2, (code, err)

    # A roster phrased as "implement using <tier> <stance>" is still plan-only.
    for sid, prompt in (
        ("test-create-plan-roster", "/create-plan tidy nav. implement using grok 4.6 medium supersoldiers"),
        ("test-create-plan-explore", "/explore pricing page idea, implement using gpt-5.6-terra high chillin"),
    ):
        code, err = run(
            {
                "hook_event_name": "PreToolUse",
                "session_id": sid,
                "prompt": prompt,
                "tool_name": "Bash",
                "tool_input": {"command": WRAPPER + " --model grok-4.6 --effort medium"},
            }
        )
        assert code == 2, (prompt, code, err)

    planning = "/create-plan tidy nav"
    def pre(sid, tool, tool_input):
        return run({"hook_event_name": "PreToolUse", "session_id": sid, "prompt": planning,
                    "tool_name": tool, "tool_input": tool_input})

    # Read-only commands that merely mention a wrapper or engine are allowed.
    for i, command in enumerate((
        "grep -rn run-grok.sh ~/.agents/skills",
        'rg "codex exec" notes.md',
        "python3 - <<'PY'\nprint('claude -p x')\nPY",
        "cat ~/.agents/skills/headless/scripts/run-claude.sh",
    )):
        code, err = pre(f"test-create-plan-ro-{i}", "Bash", {"command": command})
        assert code == 0, (command, code, err)

    # Raw engine launches and wrapper launches via a shell are still blocked.
    for tool in ("apply_patch", "functions.apply_patch"):
        code, err = pre("test-create-plan-patch", tool, {"command":
            "*** Begin Patch\n*** Add File: plan.md\n+Use `codex` here.\n*** End Patch"})
        assert code == 0, (tool, code, err)
    code, err = pre("test-create-plan-shell-patch", "Bash", {"command":
        'echo "*** Begin Patch `codex` *** End Patch"'})
    assert code == 2, (code, err)

    for i, command in enumerate(('codex exec "x"', "sh " + WRAPPER + " --lane A", 'claude -p "x"')):
        code, err = pre(f"test-create-plan-raw-{i}", "Bash", {"command": command})
        assert code == 2, (command, code, err)

    # Read-only research subagents pass; general-purpose ones stay blocked.
    code, err = pre("test-create-plan-explore-agent", "Agent", {"subagent_type": "Explore", "prompt": "map files"})
    assert code == 0, (code, err)
    code, err = pre("test-create-plan-gp-agent", "Agent", {"subagent_type": "general-purpose", "prompt": "edit"})
    assert code == 2, (code, err)
    code, err = pre("test-create-plan-no-type", "Agent", {"prompt": "edit"})
    assert code == 2, (code, err)

    # Mock round: /explore-design sets mocks mode; launches allowed only outside git.
    sid = "test-create-plan-mocks"
    code, err = run({"hook_event_name": "UserPromptSubmit", "session_id": sid, "prompt": "/explore-design redesign the site"})
    assert code == 0, (code, err)
    assert (state_dir / sid).read_text(encoding="utf-8").strip() == "mocks"
    outside = tempfile.mkdtemp()
    repo = str(Path.home() / "Workspace/Projects/Personal/Reviewer+")
    def mock_pre(tool, tool_input, prompt=""):
        return run({"hook_event_name": "PreToolUse", "session_id": sid, "prompt": prompt,
                    "tool_name": tool, "tool_input": tool_input})
    code, err = mock_pre("Bash", {"command": WRAPPER + " --cwd " + outside + " --lane B --model grok-4.6 --effort medium"})
    assert code == 0, (code, err)
    code, err = mock_pre("Bash", {"command": WRAPPER + " --cwd '" + repo + "' --lane B --model grok-4.6 --effort medium"})
    assert code == 2 and "explore-design mock round" in err, (code, err)
    code, err = mock_pre("Bash", {"command": WRAPPER + " --lane B --model grok-4.6 --effort medium"})
    assert code == 2, (code, err)
    code, err = mock_pre("Agent", {"subagent_type": "general-purpose", "prompt": "build mock-a.html"})
    assert code == 0, (code, err)
    # The /explore-design prompt itself counts as a mock-round turn.
    code, err = run({"hook_event_name": "PreToolUse", "session_id": "test-create-plan-mocks-noflag",
                     "prompt": "/explore-design hero options", "tool_name": "Bash",
                     "tool_input": {"command": WRAPPER + " --cwd '" + repo + "' --lane B"}})
    assert code == 2 and "explore-design mock round" in err, (code, err)
    # A fresh /explore or /create-plan turn re-arms strict plan-only.
    code, err = mock_pre("Bash", {"command": WRAPPER + " --cwd " + outside + " --lane B"}, prompt="/explore next idea")
    assert code == 2 and "plan-only" in err, (code, err)
    # /explore alone still blocks launches, even outside git.
    sid2 = "test-create-plan-explore-only"
    run({"hook_event_name": "UserPromptSubmit", "session_id": sid2, "prompt": "/explore pricing idea"})
    assert (state_dir / sid2).read_text(encoding="utf-8").strip() == "explore"
    code, err = run({"hook_event_name": "PreToolUse", "session_id": sid2, "prompt": "", "tool_name": "Bash",
                     "tool_input": {"command": WRAPPER + " --cwd " + outside + " --lane B"}})
    assert code == 2 and "plan-only" in err, (code, err)
    # /explore-design followed by /implement clears the flag.
    run({"hook_event_name": "UserPromptSubmit", "session_id": sid, "prompt": "/implement plans/explore-x.md"})
    assert not (state_dir / sid).exists()
    os.rmdir(outside)
    print("ok")


def new_cases():
    outside = tempfile.mkdtemp(prefix="guard-mocks-")
    launch = {"command": WRAPPER + " --cwd " + outside + " --lane B --model grok-4.6 --effort medium"}
    # 1. Typed /explore-design; transcript's last user record is the skill body quoting /create-plan.
    sid = "test-guard-skill-body"
    run({"hook_event_name": "UserPromptSubmit", "session_id": sid, "prompt": "/explore-design moods"})
    tr = Path(outside) / "t1.jsonl"
    tr.write_text(json.dumps({"type": "user", "isMeta": True, "message": {"content": "End with /create-plan plans/x.md"}}) + "\n")
    code, err = run({"hook_event_name": "PreToolUse", "session_id": sid, "transcript_path": str(tr), "tool_name": "Bash", "tool_input": launch})
    assert code == 0, ("skill body", code, err)
    # 2. /explore turn, owner picks the switch: allowed outside git, still blocked inside one.
    sid = "test-guard-switch"
    run({"hook_event_name": "UserPromptSubmit", "session_id": sid, "prompt": "/explore moods idea"})
    tr = Path(outside) / "t2.jsonl"
    recs = [{"type": "user", "message": {"content": "/explore moods idea"}},
            {"type": "user", "message": {"content": [{"type": "tool_result", "content": "answered"}]},
             "toolUseResult": {"answers": {"Route?": "Switch to explore-design (Recommended)"}}}]
    tr.write_text("\n".join(json.dumps(r) for r in recs) + "\n")
    code, err = run({"hook_event_name": "PreToolUse", "session_id": sid, "transcript_path": str(tr), "tool_name": "Bash", "tool_input": launch})
    assert code == 0, ("switch", code, err)
    assert (state_dir / sid).read_text(encoding="utf-8").strip() == "mocks"
    # 3. /explore turn where the owner chose to stay: still plan-only.
    sid = "test-guard-stay"
    run({"hook_event_name": "UserPromptSubmit", "session_id": sid, "prompt": "/explore moods idea"})
    recs[1]["toolUseResult"]["answers"] = {"Route?": "Stay in explore"}
    tr.write_text("\n".join(json.dumps(r) for r in recs) + "\n")
    code, err = run({"hook_event_name": "PreToolUse", "session_id": sid, "transcript_path": str(tr), "tool_name": "Bash", "tool_input": launch})
    assert code == 2 and "plan-only" in err, ("stay", code, err)
    # 4. A switch answered in an earlier turn does not carry into a new /explore turn.
    sid = "test-guard-old-switch"
    run({"hook_event_name": "UserPromptSubmit", "session_id": sid, "prompt": "/explore another idea"})
    recs2 = [recs[0], {**recs[1], "toolUseResult": {"answers": {"Route?": "Switch to explore-design"}}},
             {"type": "user", "message": {"content": "/explore another idea"}}]
    tr.write_text("\n".join(json.dumps(r) for r in recs2) + "\n")
    code, err = run({"hook_event_name": "PreToolUse", "session_id": sid, "transcript_path": str(tr), "tool_name": "Bash", "tool_input": launch})
    assert code == 2 and "plan-only" in err, ("old switch", code, err)
    print("new cases ok")


def read_only_cases():
    """INC-3: read-only launches pass in plan-only turns; /work-audit clears; stale flags pruned."""
    lane = lambda letter: CODEX + " --cwd /tmp --model gpt-x --effort low --lane " + letter + " --prompt-file p.md"
    # Mixed prompt: /explore and /work-audit together stay plan-only, but lane A passes.
    sid = "test-ro-mixed"
    mixed = "/explore auth idea, then /work-audit the result"
    run({"hook_event_name": "UserPromptSubmit", "session_id": sid, "prompt": mixed})
    assert (state_dir / sid).read_text(encoding="utf-8").strip() == "explore"
    def pre(tool, tool_input):
        return run({"hook_event_name": "PreToolUse", "session_id": sid, "prompt": mixed,
                    "tool_name": tool, "tool_input": tool_input})
    code, err = pre("Bash", {"command": lane("A")})
    assert code == 0, ("lane A", code, err)
    for letter in ("B", "C"):
        code, err = pre("Bash", {"command": lane(letter)})
        assert code == 2 and "plan-only" in err and "Read-only launches" in err, (letter, code, err)
    # The last --lane wins in the wrappers, so a trailing write lane is blocked.
    code, err = pre("Bash", {"command": lane("A") + " --lane B"})
    assert code == 2, ("A then B", code, err)
    # One read-only segment does not excuse a writing one in the same command.
    code, err = pre("Bash", {"command": lane("A") + " && " + lane("B")})
    assert code == 2, ("A && B", code, err)
    code, err = pre("Agent", {"subagent_type": "general-purpose", "prompt": "edit"})
    assert code == 2, ("general-purpose", code, err)
    code, err = pre("Agent", {"subagent_type": "Plan", "prompt": "design"})
    assert code == 0, ("Plan agent", code, err)
    # Wrapper help is read-only; help with a prompt is a launch.
    code, err = pre("Bash", {"command": CODEX + " --help"})
    assert code == 0, ("--help", code, err)
    code, err = pre("Bash", {"command": CODEX + " -h --lane B --prompt-file p.md"})
    assert code == 2, ("-h with prompt", code, err)
    # A later typed /work-audit clears the flag; launches are then allowed.
    run({"hook_event_name": "UserPromptSubmit", "session_id": sid, "prompt": "/work-audit"})
    assert not (state_dir / sid).exists()
    code, err = run({"hook_event_name": "PreToolUse", "session_id": sid, "prompt": "/work-audit",
                     "tool_name": "Bash", "tool_input": {"command": lane("B")}})
    assert code == 0, ("after work-audit", code, err)
    # A word that only contains work-audit does not clear.
    run({"hook_event_name": "UserPromptSubmit", "session_id": sid, "prompt": "/create-plan x"})
    run({"hook_event_name": "UserPromptSubmit", "session_id": sid, "prompt": "see docs/work-audit notes"})
    assert (state_dir / sid).exists()
    # Pruning: an 8-day-old flag goes, a fresh one stays.
    old, fresh = state_dir / "test-ro-old", state_dir / "test-ro-fresh"
    for flag in (old, fresh):
        flag.write_text("create-plan\n", encoding="utf-8")
    eight_days_ago = time.time() - 8 * 24 * 3600
    os.utime(old, (eight_days_ago, eight_days_ago))
    run({"hook_event_name": "UserPromptSubmit", "session_id": "test-ro-other", "prompt": "hello"})
    assert not old.exists() and fresh.exists()
    # Mock mode is unchanged: lane A inside a git tree is still a mock-round block.
    sid = "test-ro-mocks"
    repo = str(Path.home() / "Workspace/Projects/Personal/Reviewer+")
    run({"hook_event_name": "UserPromptSubmit", "session_id": sid, "prompt": "/explore-design hero"})
    code, err = run({"hook_event_name": "PreToolUse", "session_id": sid, "prompt": "", "tool_name": "Bash",
                     "tool_input": {"command": WRAPPER + " --cwd '" + repo + "' --lane A"}})
    assert code == 2 and "explore-design mock round" in err, ("mocks", code, err)
    print("read-only cases ok")


def transcript_cases():
    """2026-10-14: PreToolUse carries no prompt; injected user records must not read as typed prompts."""
    tmp = Path(STATE.name) / "transcripts"
    tmp.mkdir(exist_ok=True)
    launch = {"command": CODEX + " --cwd /tmp --model gpt-x --effort low --lane B --prompt-file p.md"}
    quoting = "Report: the plan said /create-plan first, then /explore the idea."
    hand_backs = [
        {"type": "user", "message": {"content": [{"type": "tool_result", "content": quoting}]},
         "toolUseResult": {"status": "completed"}},
        {"type": "user", "message": {"content": "<task-notification>" + quoting + "</task-notification>"}},
        {"type": "user", "message": {"content": "<agent-message>" + quoting + "</agent-message>"}},
        {"type": "user", "message": {"content": "<cross-session-message>" + quoting + "</cross-session-message>"}},
        {"type": "user", "message": {"content": "<system-reminder>" + quoting + "</system-reminder>"}},
        {"type": "user", "isMeta": True, "message": {"content": [{"type": "text", "text": quoting}]}},
        {"type": "user", "message": {"content": "Base directory for this skill: /x\n" + quoting}},
    ]
    def pre(sid, records):
        tr = tmp / (sid + ".jsonl")
        tr.write_text("\n".join(json.dumps(r) for r in records) + "\n", encoding="utf-8")
        return run({"hook_event_name": "PreToolUse", "session_id": sid, "transcript_path": str(tr),
                    "tool_name": "Bash", "tool_input": launch})
    # Typed /implement, then hand-backs quoting /create-plan and /explore: launches allowed.
    sid = "test-tr-implement"
    run({"hook_event_name": "UserPromptSubmit", "session_id": sid, "prompt": "/implement plans/x.md"})
    typed = {"type": "user", "message": {"content": "/implement plans/x.md"}}
    for i, rec in enumerate(hand_backs):
        code, err = pre(sid, [typed, rec])
        assert code == 0, ("hand-back", i, code, err)
    code, err = pre(sid, [typed] + hand_backs)
    assert code == 0, ("all hand-backs", code, err)
    # Typed /create-plan, then a hand-back: still blocked (flag and typed prompt agree).
    sid = "test-tr-plan"
    run({"hook_event_name": "UserPromptSubmit", "session_id": sid, "prompt": "/create-plan tidy nav"})
    code, err = pre(sid, [{"type": "user", "message": {"content": "/create-plan tidy nav"}}, hand_backs[0]])
    assert code == 2 and "plan-only" in err, ("plan + hand-back", code, err)
    # No flag: a typed slash command recorded as <command-message> still counts; its skill body does not decide.
    sid = "test-tr-command"
    cmd = {"type": "user", "message": {"content":
           "<command-message>explore</command-message>\n<command-name>/explore</command-name>\n"
           "<command-args>pricing idea</command-args>"}}
    body = {"type": "user", "isMeta": True, "message": {"content": [{"type": "text",
            "text": "Base directory for this skill: /x\nEnd with /implement plans/x.md"}]}}
    code, err = pre(sid, [cmd, body])
    assert code == 2 and "plan-only" in err, ("command-message", code, err)
    # A <command-message> without a <command-name> is injected text, not a typed command.
    code, err = pre("test-tr-bare", [typed, {"type": "user", "message": {"content":
                    "<command-message>/create-plan is loading</command-message>"}}])
    assert code == 0, ("bare command-message", code, err)
    print("transcript cases ok")


def find_launch_guard():
    """The headless launch guard from the Orchestration bundle, or None when it is not installed."""
    for path in (SOURCE.with_name("headless-launch-guard.py"),
                 SOURCE.parents[2] / "skills-orchestration/hooks/headless-launch-guard.py",
                 Path.home() / ".agents/hooks/headless-launch-guard.py"):
        if path.is_file():
            return path
    return None


class Setup(unittest.TestCase):
    """Each class builds the condition it asserts: a private copy of the hook, with or
    without the launch guard beside it and a HOME that cannot supply one."""
    with_guard = False

    @classmethod
    def setUpClass(cls):
        global SCRIPT, TEST_HOME, STATE, state_dir
        guard = find_launch_guard()
        if cls.with_guard and guard is None:
            raise unittest.SkipTest("Orchestration's headless-launch-guard.py is not installed")
        cls.tmp = tempfile.TemporaryDirectory(prefix="create-plan-hook-")
        cls.state = STATE = tempfile.TemporaryDirectory(prefix="create-plan-state-")
        state_dir = Path(STATE.name)
        hooks = Path(cls.tmp.name) / "hooks"
        hooks.mkdir()
        (hooks / SOURCE.name).write_bytes(SOURCE.read_bytes())
        if cls.with_guard:
            (hooks / guard.name).write_bytes(guard.read_bytes())
        home = Path(cls.tmp.name) / "home"
        home.mkdir()
        SCRIPT, TEST_HOME = hooks / SOURCE.name, str(home)

    @classmethod
    def tearDownClass(cls):
        global SCRIPT, TEST_HOME
        SCRIPT, TEST_HOME = SOURCE, None
        cls.tmp.cleanup()
        cls.state.cleanup()


class CreatePlanGuardWithLaunchGuard(Setup):
    with_guard = True

    def test_main(self):
        main()

    def test_new_cases(self):
        new_cases()

    def test_read_only_cases(self):
        read_only_cases()

    def test_transcript_cases(self):
        transcript_cases()


class CreatePlanGuardWithoutLaunchGuard(Setup):
    def test_launch_detection_is_skipped_without_the_guard(self):
        code, err = run({
            "hook_event_name": "PreToolUse",
            "session_id": "test-no-launch-guard",
            "prompt": "/create-plan compile lavish. orchestrate to grok 4.6 medium supersoldiers",
            "tool_name": "Bash",
            "tool_input": {"command": WRAPPER + " --model grok-4.6 --effort medium"},
        })
        self.assertEqual(code, 0, err)
        self.assertNotIn("Traceback", err)


if __name__ == "__main__":
    unittest.main()
