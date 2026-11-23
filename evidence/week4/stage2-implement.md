# Stage 2 — Implement (implement-feature skill)

## Tool calls
- `Skill {"skill": "implement-feature", "args": "Task 1 (Custom alias) from docs/TASKS.md, using the approved plan (ret`
- `Bash {"command": "cat main.py && cat tests/test_main.py tests/conftest.py tests/AGENTS.md intent.md docs/TASKS.md s`
- `Bash {"command": "cat >> tests/test_main.py <<'EOF'\n\n\ndef _shorten_alias(url: str, alias: str):\n    return clie`
- `Edit {"replace_all": false, "file_path": "/Users/yusufirmak/DEV/link-shortener-agents/tests/test_main.py", "old_str`
- `Edit {"replace_all": false, "file_path": "/Users/yusufirmak/DEV/link-shortener-agents/tests/test_main.py", "old_str`
- `Bash {"command": ".venv/bin/pytest -q 2>&1 | grep -E \"FAILED|passed|failed|Error\" | head -30", "description": "Ru`
- `Edit {"replace_all": false, "file_path": "/Users/yusufirmak/DEV/link-shortener-agents/main.py", "old_string": "clas`
- `Edit {"replace_all": false, "file_path": "/Users/yusufirmak/DEV/link-shortener-agents/main.py", "old_string": "impo`
- `Bash {"command": "scripts/check.sh 2>&1 | tail -15", "description": "Run lint, format check and tests"}`
- `Bash {"command": "cp main.py /tmp/main_backup.py && python3 - <<'EOF'\nimport pathlib\np = pathlib.Path(\"main.py\"`
- `Edit {"replace_all": false, "file_path": "/Users/yusufirmak/DEV/link-shortener-agents/main.py", "old_string": "    `
- `Bash {"command": ".venv/bin/pytest -q tests/test_main.py::test_generated_code_skips_taken_alias 2>&1 | grep -E \"In`
- `Edit {"replace_all": false, "file_path": "/Users/yusufirmak/DEV/link-shortener-agents/main.py", "old_string": "    `
- `Bash {"command": "sed -i '' 's/except sqlite3.IntegrityError:\\n            # Code/X/' main.py; .venv/bin/pytest -q`
- `Edit {"replace_all": false, "file_path": "/Users/yusufirmak/DEV/link-shortener-agents/main.py", "old_string": "    `
- `Bash {"command": ".venv/bin/pytest -q tests/test_main.py::test_generated_code_skips_taken_alias 2>&1 | tail -4", "d`
- `Edit {"replace_all": false, "file_path": "/Users/yusufirmak/DEV/link-shortener-agents/main.py", "old_string": "    `
- `Edit {"replace_all": false, "file_path": "/Users/yusufirmak/DEV/link-shortener-agents/main.py", "old_string": "    `
- `Bash {"command": ".venv/bin/pytest -q -p no:warnings tests/test_main.py::test_generated_code_skips_taken_alias 2>&1`
- `Edit {"replace_all": false, "file_path": "/Users/yusufirmak/DEV/link-shortener-agents/main.py", "old_string": "    `
- `Edit {"replace_all": false, "file_path": "/Users/yusufirmak/DEV/link-shortener-agents/main.py", "old_string": "    `
- `Bash {"command": ".venv/bin/pytest -p no:warnings --tb=line tests/test_main.py::test_generated_code_skips_taken_ali`
- `Edit {"replace_all": false, "file_path": "/Users/yusufirmak/DEV/link-shortener-agents/main.py", "old_string": "    `
- `Edit {"replace_all": false, "file_path": "/Users/yusufirmak/DEV/link-shortener-agents/main.py", "old_string": "    `
- `Bash {"command": ".venv/bin/pytest -p no:warnings --tb=line tests/test_main.py::test_generated_code_skips_taken_ali`
- `Edit {"replace_all": false, "file_path": "/Users/yusufirmak/DEV/link-shortener-agents/main.py", "old_string": "    `
- `Edit {"replace_all": false, "file_path": "/Users/yusufirmak/DEV/link-shortener-agents/tests/test_main.py", "old_str`
- `Edit {"replace_all": false, "file_path": "/Users/yusufirmak/DEV/link-shortener-agents/main.py", "old_string": "    `
- `Bash {"command": ".venv/bin/pytest -p no:warnings --tb=line tests/test_main.py::test_generated_code_skips_taken_ali`
- `Edit {"replace_all": false, "file_path": "/Users/yusufirmak/DEV/link-shortener-agents/main.py", "old_string": "    `
- `Edit {"replace_all": false, "file_path": "/Users/yusufirmak/DEV/link-shortener-agents/docs/TASKS.md", "old_string":`
- `Bash {"command": "scripts/check.sh", "description": "Run the full quality gate"}`
- `Bash {"command": "git status --short", "description": "Show changed files"}`

## Final report
Task 1 (custom alias) is done in `link-shortener-agents`, following the approved plan. The full gate (`scripts/check.sh`: lint, format, pytest) passes with 28 tests. Nothing is committed.

**What changed**
- **`main.py`**:
  - `POST /shorten` now takes an optional `alias`. If it's free, it becomes the code (200). If it's already used by another alias or an auto code, the request gets 409 `"alias already in use"`. It's a plain `INSERT`, so an existing link is never overwritten.
  - A bad alias gets 400. Valid aliases are 1–32 characters from `[A-Za-z0-9_-]`. Reserved names (`docs`, `redoc`, `openapi.json`, `stats`, `shorten`) also get 400.
  - The URL is checked first, so a bad URL never uses up an alias.
  - Auto codes now skip codes an alias has already taken: the uncommitted placeholder row is deleted and the insert is tried again. That case used to return a 500.
  - No schema change, and the response stays `{"code", "short_url"}`.
- **`tests/test_main.py`**: new tests for:
  - an alias becoming the code and redirecting
  - 409 when the alias is taken, with the original link unchanged
  - 409 when the alias matches an auto code
  - auto codes skipping a taken alias
  - 400 for invalid aliases (6 cases) and reserved aliases (5 cases)
  - a 32-character alias being accepted
  - a bad URL leaving the alias free
  - the response shape staying the same
  - `alias: null` behaving like no alias
- **`docs/TASKS.md`**: Task 1 is marked done.

**A fix to the planned collision test.** The first version I wrote (aliases `b`/`c`/`d`) still passed with the retry turned off, so it proved nothing. Each alias uses up a row id itself, so a collision only happens when an alias matches a code that a *later* id will get. The test now creates aliases `d` and `e` on ids 1–2, so the next auto code has to skip twice. With the retry turned off it fails with `UNIQUE constraint failed`, which is the bug. With the retry back in, it passes.

**Open risks**
- Each skipped auto code leaves an unused id. That's harmless, and no code is ever reused.
- The reserved list has to be updated by hand whenever a new route is added.
- None of the specialist agents in the global CLAUDE.md (`guvenlik`, `inceleyici`) were run, because you asked for the skill, which works in a single session. You could run the `reviewer` agent on this diff before committing.
