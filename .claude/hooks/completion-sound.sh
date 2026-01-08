#!/bin/bash
# Play a sound when Claude needs your attention
# Works on macOS - modify for other platforms

# Check if we're on macOS
if [[ "$(uname)" == "Darwin" ]]; then
  # Play the system ping sound (non-blocking)
  afplay /System/Library/Sounds/Ping.aiff 2>/dev/null &
fi

exit 0
