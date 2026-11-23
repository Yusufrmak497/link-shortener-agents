# AGENTS.md — Link Shortener

A tiny FastAPI service that turns long `http(s)` URLs into short codes and redirects visitors.
Read [`intent.md`](intent.md) for the invariants that must never break.

## Where things are
| Path | What it is |
|---|---|
| `main.py` | The whole app: routes, SQLite access, base62 `encode()` |
| `tests/` | pytest suite (has its own `tests/AGENTS.md` with test rules) |
| `docs/TASKS.md` | Feature backlog: pick one task at a time |
| `.claude/skills/implement-feature/` | Reusable procedure for adding a feature |
| `links.db` | SQLite file created on import. Git-ignored, never commit or edit it |

## Install, run, test
```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt -r requirements-dev.txt
.venv/bin/uvicorn main:app --reload    # http://localhost:8000/docs
.venv/bin/pytest                       # all tests
scripts/check.sh                       # ruff lint + format check + pytest (the pre-commit gate)
```

## Product boundaries
**In scope:** creating short links, redirecting, small link features from `docs/TASKS.md`
(aliases, click counts, expiry).
**Out of scope:** user accounts, auth, dashboards, custom domains, new services or databases,
new dependencies. Ask the human before adding any of these.
**Never change:** the response shape of `POST /shorten` (`{"code", "short_url"}`) and
`GET /{code}` (307 + `Location`, or 404); only `http://`/`https://` targets; an issued code
always points to the same URL.

## Change workflow
1. **Understand**: read the task, `intent.md`, and the code it touches.
2. **Test**: add a behavioural test first and see it fail for the right reason.
3. **Implement**: the smallest change in `main.py`. SQL stays parameterized (`?`), errors
   use `HTTPException` (400 bad input, 404 unknown, 409 conflict, 410 gone), schema
   changes are additive.
4. **Verify**: `scripts/check.sh` is green. Never use `--no-verify` or weaken a test.

For a full feature, follow `.claude/skills/implement-feature/SKILL.md`.

## Don't
`git push`, `git reset --hard`, force-push, or delete files without being asked.
