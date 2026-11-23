# Stage 1 — Plan (read-only session)

## Tool calls (read-only)
- `Read {"file_path": "/Users/yusufirmak/DEV/link-shortener-agents/docs/TASKS.md"}`
- `Read {"file_path": "/Users/yusufirmak/DEV/link-shortener-agents/main.py"}`
- `Read {"file_path": "/Users/yusufirmak/DEV/link-shortener-agents/intent.md"}`
- `Glob {"pattern": "tests/**"}`
- `Read {"file_path": "/Users/yusufirmak/DEV/link-shortener-agents/tests/test_main.py"}`
- `Read {"file_path": "/Users/yusufirmak/DEV/link-shortener-agents/tests/AGENTS.md"}`
- `Read {"file_path": "/Users/yusufirmak/DEV/link-shortener-agents/tests/conftest.py"}`

## Plan
# Plan: Task 1, custom alias (project: `link-shortener-agents`)

I didn't edit anything. I read `AGENTS.md`, `intent.md`, `docs/TASKS.md`, `main.py`, `tests/test_main.py`, `tests/AGENTS.md` and `tests/conftest.py`.

## Expected behaviour
`POST /shorten` takes an optional `alias` next to `url`: `{"url": "...", "alias": "my-link"}`.

| Case | Result |
|---|---|
| No `alias` | Same as today: auto base62 code, 200 |
| Valid, free `alias` | 200, `{"code": "my-link", "short_url": "/my-link"}`; `GET /my-link` returns 307 to the url |
| `alias` already in use (another alias or an auto code) | **409** `"alias already in use"`; the existing link is untouched |
| Bad `alias` format: empty, >32 chars, anything outside `[A-Za-z0-9_-]` | **400** |
| Reserved `alias` (`docs`, `redoc`, `openapi.json`, `stats`, `shorten`) | **400** |
| Bad `url` plus any `alias` | **400** (the URL is checked first and the alias isn't used up) |

- The response shape stays `{"code", "short_url"}`.
- Aliases are case-sensitive, like base62 codes.
- No idempotency: posting the same alias with the same URL again also returns 409.

## Files to change
- **`main.py`**:
  - Add `alias: str | None = None` to `ShortenRequest`.
  - Add a format and reserved-name check.
  - Add an alias branch: `INSERT INTO links (code, url) VALUES (?, ?)`, and turn `sqlite3.IntegrityError` into a 409. This also covers two requests racing for the same alias.
  - Make the auto-code path skip codes that are already taken (see risk 1).
  - No schema change: the existing `code TEXT UNIQUE` column is enough.
- **`tests/test_main.py`**: the new tests below.
- **`docs/TASKS.md`**: mark Task 1 as done.

## Tests to add (written first, seen to fail)
1. `test_shorten_with_alias_uses_alias_as_code`: code and short_url match the alias, and the redirect returns 307 with the right `Location`.
2. `test_alias_already_taken_returns_409`: the second request gets 409, and the alias still redirects to the **first** URL.
3. `test_alias_matching_generated_code_returns_409`: an auto link gets `"b"` (row id 1), then `alias="b"` gets 409.
4. `test_generated_code_skips_taken_alias`: create `alias="c"` (row id 1); the next auto shorten would get id 2, which is also `"c"`. Expected: 200, a code that isn't `"c"`, and `/c` still goes to the alias URL. **Without the fix this returns a 500 today.**
5. `test_invalid_alias_returns_400`, parametrized: `""`, `"has space"`, `"a/b"`, 33 chars.
6. `test_reserved_alias_returns_400`, e.g. `"docs"`.
7. `test_bad_url_with_alias_returns_400_and_alias_stays_free`: a later valid request with the same alias succeeds.
8. `test_alias_response_shape_unchanged`: the keys are exactly `{"code", "short_url"}`.

## Risks against `intent.md`
1. **Collision between an alias and a later auto code (invariant 1).** Auto codes come from row ids, so an alias like `"c"` can block a future id. Today the `UPDATE` would hit the UNIQUE constraint and return a 500. **Fix:** in the auto path, if `encode(id)` is taken, throw away that placeholder row (still uncommitted) and insert again. AUTOINCREMENT never reuses ids, so the loop always ends. The other option is to require aliases to contain `-` or `_` so they can never look like a base62 code. That's safe but limits users, so I recommend the retry.
2. **Overwriting an existing code (invariant 1).** Only plain `INSERT` is allowed, never `INSERT OR REPLACE` or upsert. Test 2 protects this.
3. **Hidden routes (invariant 3).** An alias like `docs` would never redirect because FastAPI's own route answers first. The reserved list handles this.
4. **Open redirect (invariant 2).** The URL check still runs before anything else, and the alias never changes the target.
5. **Status code for bad aliases.** A pydantic `pattern` would give 422, while AGENTS.md says bad input is 400. I'm proposing a manual check that returns 400; tell me if you'd rather have 422.

**Waiting for your approval before Stage 2.** In particular, please confirm the retry approach for risk 1 and the 400 status for bad aliases.
