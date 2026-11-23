# Week 4 — Structuring a Repo for Agents: The Link Shortener

**Student:** Yusuf Irmak · **Agent:** Claude Code (CLI) · **Feature:** Task 1, custom alias

> Work for the earlier version of this brief (hooks, subagents) is in
> [`docs/writeup-original-brief.md`](docs/writeup-original-brief.md).

## 1. What is in `AGENTS.md`, and why is it broadly available?
[`AGENTS.md`](AGENTS.md) (43 lines) covers what the service does, where the files are, how to install,
run and test, the product boundaries (including the API shape that must never change), and a workflow:
understand → test → implement → verify. Every task needs this, so it loads in every session.
Area-specific rules were kept out.

## 2. What is scoped, and when does it load?
[`tests/AGENTS.md`](tests/AGENTS.md): test through the public HTTP API, cover success and failure, keep
tests independent (a fixture gives each test its own SQLite file), and assert behaviour, not internals.
These rules only matter when someone writes tests, so loading them everywhere would only add noise.

## 3. What procedure does the workflow encode?
[`.claude/skills/implement-feature/SKILL.md`](.claude/skills/implement-feature/SKILL.md) has seven steps:
read the task and guidance, inspect code and tests, state the expected behaviour and files, add a failing
behavioural test, make the smallest change, run `pytest` and `scripts/check.sh`, then summarize the change and its risks.

## 4. How does Claude Code discover each artifact?
| Artifact | Discovery |
|---|---|
| `AGENTS.md` | Root `CLAUDE.md` (read at startup) is just `@AGENTS.md` |
| `tests/AGENTS.md` | Nested `tests/CLAUDE.md` (`@AGENTS.md`) loads **only when the agent reads files in `tests/`** |
| Skill | Listed by name and description, loaded on demand; stage 2 called `Skill("implement-feature")` |

## 5. What did planning and review contribute?
Each stage was a separate `claude -p` session (transcripts in [`evidence/week4/`](evidence/week4/)).
- **Plan** (read-only): it found a real collision. Auto codes are base62 of the row id, so an alias like
  `c` blocks a future auto code, and the next `POST /shorten` would crash with a 500. The approved fix
  skips taken codes. It also reserved route names like `docs`.
- **Implement** (skill): the agent noticed that its first collision test passed even with the fix turned
  off, so it rewrote the test until it failed on the bug. Result: 28 tests passing.
- **Review** (read-only): **`VERDICT: ACCEPT`**. Its nits (two tests could assert more) are left as follow-ups.

## 6. What I learned
Instead of telling the agent every time how to run the tests and what it must not break, I wrote that once
in `AGENTS.md`, and it reads it at the start of every session. Rules that only matter for tests live in
`tests/AGENTS.md`, so they load only when the agent works there. The skill made the procedure repeatable:
the agent had to write a failing test first, and that is exactly how it caught its own useless test.
Splitting plan, implement and review into separate sessions also helped, because the read-only planner
found the alias collision before any code was written, and the reviewer judged code it hadn't written.
