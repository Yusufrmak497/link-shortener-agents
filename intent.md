# intent.md — why this service exists

## Purpose
Turn long URLs into short, stable codes that redirect reliably. The service is meant to be small
enough for one person (or one agent) to understand completely.

## Users
- **Link creators** call `POST /shorten` and paste the returned `short_url` somewhere public.
- **Visitors** follow `GET /{code}` and expect to land on the original URL instantly.

## Invariants (must never break)
1. **A short code, once issued, always resolves to the same URL.** Codes are never reused,
   reassigned, or recycled, because a printed or shared link must stay valid.
2. **Only `http://` and `https://` targets** are accepted. No `javascript:`, `ftp:`, or relative URLs
   (this guards against open-redirect abuse).
3. **The public API shape is stable**: `POST /shorten` returns `{"code", "short_url"}`, and `GET /{code}`
   returns 307 with a `Location` header or a 404.
4. **Existing data survives upgrades.** Schema changes are additive.

## Non-goals (for now)
User accounts, auth, analytics dashboards, custom domains, and horizontal scaling.

## Quality bar
Every behaviour has a test. `scripts/check.sh` must be green before any commit.
When in doubt, prefer the simpler change, and ask the human before changing an invariant.
