# prompt-auto-log

Prompt Auto Log automatically captures every prompt submitted during development and stores it in a single repository file that is easy to review, version, and extend.

## Overview

The canonical log lives at the repository root in [copilot-prompts.json](copilot-prompts.json). Every time a prompt is submitted in Claude Code, a hook fires and appends the entry to this file with metadata.

The log is useful for:

- Tracking prompt iterations over time
- Reviewing context for a given task or branch
- Keeping prompt history in Git instead of in a separate service

## How It Works

A Claude Code `userPromptSubmitted` hook is registered via [.github/hooks/hooks.json](.github/hooks/hooks.json). On every prompt submission, Claude Code runs [.github/hooks/scripts/log-prompt-hook.sh](.github/hooks/scripts/log-prompt-hook.sh), which:

1. Reads the prompt text from the hook's stdin payload
2. Resolves the current Git branch and user
3. Appends a new entry to [copilot-prompts.json](copilot-prompts.json) using `jq`
4. Exits successfully (`exit 0`) so the prompt proceeds normally

## Data Format

`copilot-prompts.json` uses the following structure:

- `version`: log format version
- `createdAt`: timestamp for when the file was first created
- `prompts`: array of prompt entries

Each prompt entry stores:

- `id`: unique identifier (`prompt-<epoch-ms>`)
- `timestamp`: capture time in ISO 8601 UTC format
- `gitBranch`: branch where the prompt was recorded
- `gitUser`: Git user name associated with the capture
- `promptText`: the full prompt content
- `context`: label extracted from the hook input, defaulting to `"copilot"`

## Repository Structure

```text
.
├── README.md
├── copilot-prompts.json
└── .github/
    └── hooks/
        ├── hooks.json              # Claude Code hook registration
        └── scripts/
            └── log-prompt-hook.sh  # Hook implementation
```

## Getting Started

### Prerequisites

- Git
- Claude Code CLI
- `jq` and `python3` available in your shell (used by the hook script)

### Clone the repository

```bash
git clone git@github.com:pucrs-csw-2026-1/prompt-auto-log.git
cd prompt-auto-log
```

### Enable the hook

Register the hook with Claude Code by pointing it at the hook configuration file:

```bash
# In Claude Code settings, add the hooks file path or copy its contents
# into your project-level .claude/settings.json under the "hooks" key.
```

Once configured, every prompt submitted in this workspace is automatically logged to [copilot-prompts.json](copilot-prompts.json).

### Inspect the log

Open [copilot-prompts.json](copilot-prompts.json) to review captured entries, or use `jq` to query them:

```bash
# List all prompts with their timestamps
jq '.prompts[] | {timestamp, promptText}' copilot-prompts.json

# Filter by branch
jq '.prompts[] | select(.gitBranch == "main")' copilot-prompts.json
```

## Roadmap

- Validate the JSON structure before writes
- Add filtering and search utilities
- Add export and reporting options
- Add CI checks to lint the log file on pull requests

## Contributing

Contributions are welcome.

1. Fork the repository
2. Create a branch with your change
3. Commit your work
4. Push the branch
5. Open a pull request

## License

Add a license file when the project license is decided.

## Contact

Repository: <https://github.com/pucrs-csw-2026-1/prompt-auto-log>
