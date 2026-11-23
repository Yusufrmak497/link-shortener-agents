The gate is **red**. Lint and format pass, but 2 of 9 pytest tests fail.

**ruff check**: passed. **ruff format**: passed (14 files already formatted).

**pytest**: 2 failed, 7 passed

1. **Where**: `test_main.py:18`, `test_shorten_and_redirect`
   - **What**: `assert 307 == 302`
   - **Likely cause**: The app's redirect at `main.py:104` returns 307, but this test now expects 302. The last commit had `== 307` here; an uncommitted edit changed it to `302`.
   - **Suggested fix**: Change the test back to `assert r2.status_code == 307`.

2. **Where**: `test_main.py:74`, `test_redirect_shape_unchanged_with_counter`
   - **What**: `assert 307 == 302`
   - **Likely cause**: Same mismatch. This new test expects 302, but it is supposed to guard the unchanged redirect. `test_redirect_increments_clicks` in the same diff expects 307.
   - **Suggested fix**: Change the assertion to `== 307`.

In both cases the test is wrong, not the app. `intent.md:17` says the redirect returns 307 with a `Location` header, and AGENTS.md doesn't allow changing the response shape of `GET /{code}`, so don't change `main.py` to return 302.

Re-run only the failing tests:
```
.venv/bin/pytest -q test_main.py::test_shorten_and_redirect test_main.py::test_redirect_shape_unchanged_with_counter
```
