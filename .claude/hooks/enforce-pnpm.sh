#!/bin/bash
# Enforce pnpm over npm in this project
# Exit code 2 = block with message shown to Claude

input=$(cat)
command=$(echo "$input" | jq -r '.tool_input.command // ""')

# Check if command starts with npm (but not npx)
if [[ "$command" == npm\ * ]] || [[ "$command" == "npm" ]]; then
  echo "This project uses pnpm, not npm. Please use 'pnpm' instead of 'npm'."
  echo "Examples: pnpm install, pnpm add <package>, pnpm run dev"
  exit 2
fi

exit 0
