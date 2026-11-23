---
name: implement-feature
description: Implement one feature from docs/TASKS.md in this link shortener, test-first, then verify with pytest and summarize. Use when asked to build or complete a task from the backlog.
---

# Implement a feature (test-first)

Follow these steps in order. Do not skip the failing-test step.

1. **Read** the selected task in `docs/TASKS.md`, plus `AGENTS.md`, `intent.md` and `tests/AGENTS.md`.
2. **Inspect** the related code in `main.py` and the existing tests in `tests/`.
3. **State the plan** in 3–6 lines before editing: the expected behaviour (inputs, outputs,
   status codes), the files you will touch, and any invariant in `intent.md` it could affect.
4. **Add a failing behavioural test** in `tests/` (success case and at least one failure or
   edge case). Run `.venv/bin/pytest` and confirm the new tests fail **for the right reason**
   (e.g. 404/422 because the feature is missing, not an import error).
5. **Implement the smallest change** in `main.py` that makes them pass. Keep SQL
   parameterized and schema changes additive; don't change the existing API shape.
6. **Run** `.venv/bin/pytest` (all tests, old and new) and `scripts/check.sh` until both are green.
7. **Summarize**: what changed (files + behaviour), which tests were added, and any remaining
   risks or follow-ups. Do not commit unless asked.
