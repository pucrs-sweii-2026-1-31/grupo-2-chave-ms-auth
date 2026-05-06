#!/usr/bin/env bash

input=$(cat)

# Extract and clean prompt (remove IDE context tags)
prompt=$(printf '%s' "$input" | jq -r '.prompt // ""' | perl -0777 -pe 's/<[a-z_]+>.*?<\/[a-z_]+>\n?//gs' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')

if [ -z "$prompt" ]; then
    exit 0
fi

# Git info
git_branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
git_user_name=$(git config --get user.name 2>/dev/null || echo "unknown")
git_email=$(git config --get user.email 2>/dev/null || echo "")

if [ -z "$git_email" ]; then
    git_email=$(printf '%s' "$git_user_name" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/_/g')
fi

# Call context (all fields except prompt and session_id)
call_context=$(printf '%s' "$input" | jq 'del(.prompt, .session_id)')

# Build entry
timestamp=$(date -u +"%Y-%m-%dT%H:%M:%S+00:00")
entry=$(jq -n \
    --arg timestamp "$timestamp" \
    --arg git_branch "$git_branch" \
    --arg git_user_name "$git_user_name" \
    --argjson call_context "$call_context" \
    --arg prompt "$prompt" \
    '{timestamp: $timestamp, git_branch: $git_branch, git_user_name: $git_user_name, call_context: $call_context, prompt: $prompt}')

# Determine log file path
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
log_path="$script_dir/prompt_log_${git_email}.json"

# Append to log file
if [ -f "$log_path" ]; then
    updated=$(jq ". + [$entry]" "$log_path")
    printf '%s\n' "$updated" > "$log_path"
else
    printf '[%s]\n' "$entry" > "$log_path"
fi
