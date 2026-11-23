---
description: Run the quality gate and summarize any failures with likely causes
allowed-tools: Bash(scripts/check.sh), Bash(.venv/bin/pytest:*), Read, Grep
---
Run `scripts/check.sh` from the repo root and capture the full output.

If everything passes, reply with one line: `✔ gate green: <N> tests passed`.

Otherwise, report failures grouped by stage (ruff check / ruff format / pytest). For each failure, give:
- **Where**: `file:line` and the test or rule name
- **What**: the assertion or lint message, quoted exactly and kept short
- **Likely cause**: one sentence, based on reading the code at that line
- **Suggested fix**: one sentence. Do NOT edit files; this command only diagnoses.

End with the exact command to re-run only the failing tests (`.venv/bin/pytest -q <nodeid> ...`).
$ARGUMENTS
