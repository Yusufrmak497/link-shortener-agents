# Stage 3 — Review (read-only session)

Review of the Task 1 (Custom alias) change in **link-shortener-agents**. I didn't edit any files.

**Checks run**
- `.venv/bin/pytest`: all 28 tests pass. The only warning is a Starlette/httpx deprecation from a dependency.
- I couldn't run ruff (lint and format) because that command needed approval. The lint and format part of `scripts/check.sh` is still unchecked.

**Findings** (none block merging)
1. `main.py:72`: `"openapi.json"` in `RESERVED_ALIASES` can never be reached, because `ALIAS_RE` already rejects `.`. Reserving `"stats"` is only a precaution, since `/stats` with no code would still go to `/{code}`. Neither is a bug.
2. `tests/test_main.py:160`: the reserved test passes for `openapi.json` because the format check rejects it, not the reserved check. It also only checks the status code, so it can't tell "reserved" from "bad format". Checking `detail == "alias is reserved"` for the names that pass the format check would fix that.
3. `tests/test_main.py:134`: `test_generated_code_skips_taken_alias` depends on the row-id → base62 mapping (ids 3 and 4 encode to "d" and "e"). That leans toward testing implementation, which `tests/AGENTS.md` warns against. It's still fine here, because it's the only way to trigger the collision and `conftest.py` gives each test a fresh database.
4. `tests/test_main.py:181`: `test_null_alias_behaves_like_no_alias` only checks that `code` is truthy. It could also check that the code redirects to the URL.
5. The rules are met:
   - **Invariant 1 (codes never reused):** aliases use a plain INSERT, never an upsert, and a taken alias returns 409 while the original keeps working. Auto codes skip any taken code by retrying, and AUTOINCREMENT never reuses ids, so the loop always ends.
   - **Invariant 2 (only http/https):** the URL is checked before the alias.
   - **Invariant 3 (response shape):** unchanged.
   - **Invariant 4 (schema):** no schema change.
   - **Project rules:** SQL stays parameterized, status codes are 400/409 as `AGENTS.md` requires, and nothing was added that's out of scope.
6. The change matches the approved Stage 1 plan (`evidence/week4/stage1-plan.md`), with a few extra tests on top.

VERDICT: ACCEPT. The change does what the approved plan says, keeps every invariant in `intent.md`, and passes all tests; the findings are minor test-strength nits, and ruff still needs to run before committing.
