# Test rules (apply only to files in `tests/`)

- **Test through the public HTTP API** with `TestClient` (`POST /shorten`, `GET /{code}`, ...).
  Do not call private helpers or query SQLite directly, except in a migration test.
- **Cover success and failure** for every behaviour: the happy path plus at least one
  error or edge case (bad input → 400/422, unknown → 404, conflict → 409, ...).
- **Tests are independent.** `conftest.py` gives each test a fresh SQLite file; never rely on
  data from another test or on execution order, and never use the real `links.db`.
- **Assert behaviour, not implementation**: status codes, response JSON, redirect `Location`,
  not internal variable names or SQL.
- One behaviour per test, named `test_<behaviour>`. Never delete or loosen an existing test
  to make a change pass.
