#!/bin/bash
# PreToolUse / UserPromptSubmit: plan-only while /create-plan is the current turn.
exec python3 "$HOME/.agents/hooks/create-plan-no-implement.py"
