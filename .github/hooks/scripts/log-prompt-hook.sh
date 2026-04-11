#!/usr/bin/env bash
#
# Copilot Hook: Auto-log prompts
# Called on userPromptSubmitted event
# Input: JSON from stdin with fields like timestamp, cwd, and prompt
# Output: ignored for this hook type

set -euo pipefail

WORKSPACE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
LOG_FILE="${WORKSPACE_ROOT}/copilot-prompts.json"

# Read input JSON from stdin
INPUT=$(cat)

# Extract prompt text and optional context data from the input.
# Official payload uses .prompt; .userMessage is kept as compatibility fallback.
PROMPT_TEXT=$(echo "$INPUT" | jq -r '.prompt // .userMessage // ""' 2>/dev/null || echo "")
CONTEXT=$(echo "$INPUT" | jq -r '.context // .cwd // "copilot"' 2>/dev/null || echo "copilot")
INPUT_TS_MS=$(echo "$INPUT" | jq -r '.timestamp // empty' 2>/dev/null || echo "")

# Simplify context if it's too long
CONTEXT=$(echo "$CONTEXT" | cut -c1-80)

# Only log if we have a valid prompt (not empty)
if [ -n "$PROMPT_TEXT" ] && [ "$PROMPT_TEXT" != "Unknown Prompt" ]; then
  cd "$WORKSPACE_ROOT"

  # Get git info
  GIT_BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
  GIT_USER=$(git config user.name 2>/dev/null || echo "unknown")
  EPOCH_MS=$(python3 -c "import time; print(int(time.time() * 1000))")

  if [[ "$INPUT_TS_MS" =~ ^[0-9]+$ ]]; then
    TIMESTAMP=$(python3 -c "from datetime import datetime, timezone; ms=int('$INPUT_TS_MS'); n=datetime.fromtimestamp(ms/1000, tz=timezone.utc); print(n.strftime('%Y-%m-%dT%H:%M:%S.')+f'{n.microsecond//1000:03d}Z')")
  else
    TIMESTAMP=$(python3 -c "from datetime import datetime, timezone; n=datetime.now(timezone.utc); print(n.strftime('%Y-%m-%dT%H:%M:%S.')+f'{n.microsecond//1000:03d}Z')")
  fi

  PROMPT_ID="prompt-${EPOCH_MS}"

  # Create or update log file
  if [ ! -f "$LOG_FILE" ]; then
    jq -n --arg createdAt "$TIMESTAMP" '{version: "1.0", createdAt: $createdAt, prompts: []}' > "$LOG_FILE"
  fi

  # Guard against corrupted JSON so we do not overwrite a broken file silently.
  jq -e '.prompts and (.prompts | type == "array")' "$LOG_FILE" >/dev/null

  # Add new prompt entry using jq
  jq --arg id "$PROMPT_ID" \
     --arg timestamp "$TIMESTAMP" \
     --arg branch "$GIT_BRANCH" \
     --arg user "$GIT_USER" \
     --arg text "$PROMPT_TEXT" \
     --arg ctx "$CONTEXT" \
     '.prompts += [{"id": $id, "timestamp": $timestamp, "gitBranch": $branch, "gitUser": $user, "promptText": $text, "context": $ctx}]' \
     "$LOG_FILE" > "${LOG_FILE}.tmp"
  mv "${LOG_FILE}.tmp" "$LOG_FILE"
fi

exit 0
