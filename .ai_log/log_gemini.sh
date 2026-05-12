#!/usr/bin/env bash

# This script is a wrapper for Gemini CLI hooks.
# It calls the main log_prompts.sh script and ensures
# that the output is valid JSON for Gemini CLI.

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Call the original logger, passing through stdin
# and redirecting its output to stderr to keep stdout clean for Gemini
bash "$SCRIPT_DIR/log_prompts.sh" >&2

# Gemini CLI hooks MUST output valid JSON to stdout
echo "{}"
