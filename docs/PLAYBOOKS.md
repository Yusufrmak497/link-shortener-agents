# Playbooks: reusable agent workflows

Each playbook is a prompt you can paste into any agent. In Claude Code the same playbooks are
saved as slash commands in `.claude/commands/` and subagents in `.claude/agents/`.

## `/test-summary`: run the gate and diagnose failures
Source: [`.claude/commands/test-summary.md`](../.claude/commands/test-summary.md).
> Run `scripts/check.sh`. If it is green, reply `✔ gate green: N tests passed`. Otherwise, for each
> failure give file:line, the exact message, the likely cause, and a suggested fix, without editing files.
> End with the command that re-runs only the failing tests.

## Feature via subagents: planner → implementer → reviewer
> 1. Ask the **planner** subagent for a plan for task *X* from `docs/TASKS.md`.
> 2. Give that plan verbatim to the **implementer** subagent (test-first, gate must be green).
> 3. Ask the **reviewer** subagent to review `git diff` against the plan, `AGENTS.md` and `intent.md`.
> 4. If the reviewer says CHANGES REQUESTED, send its findings back to the implementer, for at most two rounds.
> 5. A human reads the diff and the reviewer verdict before committing.
