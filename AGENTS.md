# AGENTS.md — Link Shortener

These instructions are for any coding agent working in this repo (Claude Code, Antigravity, Codex, Cursor…).
Read [`intent.md`](intent.md) first: it explains *why* the service exists and what must never break.

## Project map
| Path | What it is |
|---|---|
| `main.py` | The whole app: FastAPI routes, SQLite access, base62 `encode()` |
| `test_main.py` | pytest suite, using FastAPI `TestClient` against the real SQLite file |
| `links.db` | SQLite database, created on import. Git-ignored, **never commit it** |
| `docs/TASKS.md` | Backlog of small features |
| `docs/PLAYBOOKS.md` | Reusable prompts/workflows (mirrors `.claude/commands/`) |
| `.githooks/pre-commit` | Quality gate: ruff lint + format check + pytest |
| `.claude/agents/` | `planner`, `implementer`, `reviewer` subagents |
| `.claude/commands/` | `/test-summary` reusable workflow |

## Setup and run
```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt -r requirements-dev.txt
git config core.hooksPath .githooks     # enable the pre-commit gate (once per clone)
.venv/bin/uvicorn main:app --reload     # http://localhost:8000/docs
```

## Commands
| Purpose | Command |
|---|---|
| Run tests | `.venv/bin/pytest` |
| Lint | `.venv/bin/ruff check .` |
| Format | `.venv/bin/ruff format .` |
| Full gate (same as the hook) | `scripts/check.sh` |

## Safe vs. forbidden
**Safe without asking:** reading any file; running the commands above; editing `main.py`,
`test_main.py`, and `docs/`; creating new test files; `git status`, `git diff`, `git log`.

**Forbidden unless the human explicitly asks:**
- `git commit --no-verify`, or anything else that skips or disables `.githooks/`
- `git push`, `git reset --hard`, `git clean`, force-pushes, or rewriting history
- deleting or editing `links.db` by hand, or `rm -rf` anything
- adding dependencies without also updating `requirements.txt`
- changing the response shape of `POST /shorten` or `GET /{code}`: clients depend on them (see `intent.md`)
- weakening or deleting an existing test to make a change pass

## Workflow: adding a new endpoint or feature
1. **Failing test first.** Add a test in `test_main.py` that describes the behaviour, then run
   `.venv/bin/pytest` and confirm it **fails for the right reason**.
2. **Implement** the smallest change in `main.py` that makes it pass. Keep SQL parameterized
   (`?` placeholders, never f-strings). Return errors with `HTTPException` and the right status code
   (400 bad input, 404 unknown, 409 conflict, 410 gone).
3. **Schema changes** must be backward compatible with an existing `links.db`: add columns with
   `ALTER TABLE … ADD COLUMN` guarded by a check, and never drop data.
4. **Run the hook**: `scripts/check.sh` (or simply commit; the pre-commit hook runs it). Fix
   until it is green. Do not bypass it.
5. **Summarize** what changed, which tests were added, and any follow-ups.

## Conventions
- Python 3.10+, type hints on new functions, ruff line length 100.
- One test per behaviour, named `test_<behaviour>`. Tests must not depend on execution order.
- Keep `main.py` a single module until it exceeds ~300 lines.
