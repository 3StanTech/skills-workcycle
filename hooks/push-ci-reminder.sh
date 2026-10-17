#!/bin/bash
# PostToolUse/Bash: after a git push, remind the agent to run the bounded CI/deploy wait.
exec python3 "$HOME/.agents/hooks/push-ci-reminder.py"
