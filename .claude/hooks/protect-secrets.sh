#!/bin/bash
# Block access to files containing secrets
# This prevents accidental reading/editing of sensitive configuration

input=$(cat)
tool_name=$(echo "$input" | jq -r '.tool_name // ""')
file_path=$(echo "$input" | jq -r '.tool_input.file_path // ""')
command=$(echo "$input" | jq -r '.tool_input.command // ""')

# Patterns that indicate secret files
secret_patterns=(
  "\.env$"
  "\.env\."
  "credentials"
  "secrets"
  "\.pem$"
  "\.key$"
  "service.*account.*\.json"
)

# Check file path for Read/Edit/Write tools
for pattern in "${secret_patterns[@]}"; do
  if [[ "$file_path" =~ $pattern ]]; then
    echo "Access blocked: '$file_path' appears to contain secrets."
    echo "If you need to reference environment variables, check .env.example instead."
    exit 2
  fi
done

# Check bash commands that might access secrets
for pattern in "${secret_patterns[@]}"; do
  if [[ "$command" =~ $pattern ]]; then
    echo "Command blocked: appears to access secret files."
    echo "Secret files should not be read, printed, or modified by Claude."
    exit 2
  fi
done

exit 0
