#!/usr/bin/env bash

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Call the original logger, passing through stdin
# and redirecting its output to stderr to keep stdout clean for Gemini
bash "$SCRIPT_DIR/log_prompts.sh" >&2

# Gemini CLI hooks MUST output valid JSON to stdout
echo "{}"
