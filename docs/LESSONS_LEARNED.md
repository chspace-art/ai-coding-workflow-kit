# Lessons Learned

This file stores durable workflow lessons that should be read before meaningful work starts.

## Entry format

```text
### [YYYY-MM-DD] Title
- Scenario:
- Problem:
- Fix:
- Future rule:
- Related:
```

## Starter entries

### [2026-05-30] Use a runner for structure, not memory alone
- Scenario: Repeated AI tasks drifted because process rules lived only in prose.
- Problem: Task ids, summaries, and completion markers were easy to forget.
- Fix: Use a task runner to create the envelope, record role evidence, and write normalized summaries.
- Future rule: If a workflow rule is frequently missed, turn it into a repo-local gate.
- Related: `tools/agent-comm/workflow_runner.py`
