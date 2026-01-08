#!/bin/bash
# Audit log all bash commands for review
# This runs AFTER the command executes (PostToolUse)
# Useful for understanding what Claude did in a session

input=$(cat)
tool_name=$(echo "$input" | jq -r '.tool_name // ""')
command=$(echo "$input" | jq -r '.tool_input.command // ""')
description=$(echo "$input" | jq -r '.tool_input.description // ""')
timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Only log Bash commands
if [[ "$tool_name" == "Bash" ]]; then
  log_dir="$HOME/.claude-audit"
  mkdir -p "$log_dir"

  # Log to daily file
  log_file="$log_dir/$(date +%Y-%m-%d).log"
  echo "[$timestamp] $description" >> "$log_file"
  echo "  Command: $command" >> "$log_file"
  echo "" >> "$log_file"
fi

exit 0
