# Common Memory

This file stores stable repo-wide guidance.

## Read order

1. `docs/LESSONS_LEARNED.md`
2. `docs/memory/COMMON.md`
3. Topic memory under `docs/memory/TOPICS/`
4. Repo-local skills under `.agents/skills/`
5. Similar task summaries under `share/archive/`

## Default workflow

- Run `bootstrap_check.py` before meaningful work.
- Start the task with `workflow_runner.py start`.
- Confirm the requirement before the first dev record unless the task is truly one-line explicit.
- Record `dev`, `mentor`, and `qa` outputs in order.
- Treat archive summaries as machine-readable artifacts, not free-form notes.

## Memory writing rule

Write memory only when the lesson is reusable:

- it prevents a recurring bug
- it changes verification behavior
- it clarifies a project constraint
- it captures a stable user or maintainer preference
