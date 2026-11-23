# Week 5 — Structuring a Repo for Agents: The Link Shortener

**Student:** Yusuf Irmak
**Agent:** Claude Code (CLI). The assignment's default is Antigravity; each concept below is
mapped to the equivalent Claude Code feature.

## 1. Artifacts, and the agent feature each maps to

| Artifact | What it does | Claude Code feature (and its Antigravity equivalent) |
|---|---|---|
| [`AGENTS.md`](AGENTS.md) | Project map, setup/run commands, a **safe vs. forbidden** command list, and the workflow "failing test → implement → run the hook" | Cross-tool `AGENTS.md`. Claude Code reads `CLAUDE.md`, which just imports it (`@AGENTS.md`), so there is one source of truth. (Antigravity: workspace rules) |
| [`intent.md`](intent.md) | *Why* the service exists, plus four invariants that must never break (stable codes, http/https only, stable API shape, additive schema changes) | Context file referenced from `AGENTS.md`. The subagents are told to read it |
| [`.githooks/pre-commit`](.githooks/pre-commit) → [`scripts/check.sh`](scripts/check.sh) | `ruff check` + `ruff format --check` + `pytest`. It **blocks the commit** if any of them fails | git `pre-commit` hook, enabled with `git config core.hooksPath .githooks`. It is deterministic, so it works the same for any agent or human |
| [`.claude/commands/test-summary.md`](.claude/commands/test-summary.md) (+ [`docs/PLAYBOOKS.md`](docs/PLAYBOOKS.md)) | `/test-summary`: runs the gate and groups failures with file:line, the exact message, the likely cause and a suggested fix, without editing anything | Claude Code **custom slash command**, restricted with `allowed-tools`. (Antigravity: saved workflow.) `PLAYBOOKS.md` holds the same prompt for any other tool |
| [`.claude/agents/`](.claude/agents/) `planner` / `implementer` / `reviewer` | Role-specialized subagents. The planner and reviewer are **read-only** (no Edit/Write tools); the implementer is the only one that can edit | Claude Code **subagents** with a per-agent `tools:` allow-list. (Antigravity: Agent Manager agents) |

`pyproject.toml` configures ruff (line length 100). The starter had one unformatted line, which was fixed
once so that the gate starts green.

## 2. The hook blocking a failing change
Screenshot: [`evidence/hook-blocked.png`](evidence/hook-blocked.png) (raw log:
[`evidence/hook-blocked.txt`](evidence/hook-blocked.txt)).

![pre-commit hook blocking a commit](evidence/hook-blocked.png)

The bad change allows `ftp://` URLs (which breaks invariant 2 in `intent.md`) and leaves an unused import.
`git commit` was **rejected**. Ruff reported `F401 'os' imported but unused` and a format problem, and pytest reported
`FAILED test_main.py::test_rejects_bad_url - assert 200 == 400`. `git log` shows no new commit.
After reverting the change, the gate is green, and every later commit in this repo went through the hook.

## 3. Reusable workflow in action
[`evidence/test-summary-run.md`](evidence/test-summary-run.md) shows `/test-summary` run against a deliberately broken
assertion (`307` changed to `302`). It found both failing tests and pointed to `intent.md` ("GET /{code} returns 307"), so
it concluded that **the test is wrong, not the app**. It then printed the command that re-runs only those two tests.
It didn't edit anything, as its `allowed-tools` require.

## 4. Subagents: Task 2 (click counter)
Full transcript: [`evidence/subagent-transcript.md`](evidence/subagent-transcript.md). An orchestrating
Claude Code session ran the three subagents in order, and each one received the previous one's output verbatim:

1. **planner** (read-only): defined the API contract. `GET /stats/{code}` returns `{"url","clicks"}` or a
   404. Only a 307 redirect counts as a click, and reading the stats does not. The schema change is additive
   (`ALTER TABLE … ADD COLUMN clicks … DEFAULT 0`, guarded by `PRAGMA table_info` so existing
   `links.db` files are migrated). The plan listed 6 tests to write first, plus the risks: route ordering of
   `/stats/{code}` vs `/{code}`, and a read-then-write race on the counter.
2. **implementer**: wrote the 6 tests first. 5 of them failed for the right reason (`404 == 200` for the missing route, `no such column: clicks` for the migration). The sixth guards the unchanged redirect shape, so it passed both before and after, as it should. Then it implemented the change. It used an atomic
   `UPDATE … SET clicks = clicks + 1`, not a read-modify-write, and committed only when the code exists.
   `scripts/check.sh` was green with 9 tests.
3. **reviewer** (read-only): **`VERDICT: APPROVED`**, with no MUST FIX items. It suggested a stronger "stats doesn't
   count" test (visit once, read the stats twice, expect 1) and a comment on the uncommitted UPDATE for unknown codes.

**My own review before accepting:** I read the diff line by line. The SQL is parameterized, the
`/{code}` response is unchanged, and the migration is idempotent and only adds a column. The tests patch `DB_PATH` for
the migration test, so the real database isn't touched. I accepted the change, and the commit passed the hook.
The reviewer's NICE TO HAVE items are left as follow-ups.

## 5. What I learned
Instead of telling the agent every time to run the tests and never accept `ftp://`, I wrote those rules into `AGENTS.md` and `intent.md`, so the agent reads them itself at the start of every session and they don't get forgotten. A hook is stronger than a request: asking the agent not to commit bad code is only a request, but the pre-commit hook enforces it, and the broken `ftp://` change could not be committed even if the agent had wanted to. Splitting the roles also helped, because the planner and reviewer can't edit files and only the implementer writes code, so each agent sticks to its own job and the reviewer gives an independent review instead of the code's author approving its own work.
