---
name: git-governance
description: Use for commit structure, archive linkage, and public repo hygiene.
---

# Git Governance

## Suggested commit format

```text
[taskID:iter_n] type: short description
```

## Rule

- Keep commits traceable to a task id when using the workflow runner.
- Do not stage unrelated local changes.
- Keep archive summaries and documentation in sync with behavior changes.
