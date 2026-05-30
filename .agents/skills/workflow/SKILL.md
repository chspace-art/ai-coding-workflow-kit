---
name: workflow
description: Use when a task needs startup checks, a task envelope, phase tracking, or normalized archive summaries.
---

# Workflow Skill

## Startup

Run:

```powershell
python tools/agent-comm/bootstrap_check.py --keywords "<task keywords>"
python tools/agent-comm/workflow_runner.py start --title "<task title>" --keywords "<task keywords>"
```

## Gate

Confirm requirement understanding before the first dev record unless the change is one-line explicit.

## Completion

Use the runner summary as the canonical completion artifact.
