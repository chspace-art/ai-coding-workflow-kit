# Workflow Runner

## Purpose

The runner exists so task structure does not depend on memory alone.

## Rule

- Start meaningful tasks with `workflow_runner.py start`.
- Confirm requirement understanding before the first dev record.
- Record `dev -> mentor -> qa` evidence as structured JSON.
- Complete tasks only after the latest mentor and qa records both pass.

## Validation

```powershell
python tools/agent-comm/workflow_runner.py status --task-id <taskID>
python tools/agent-comm/workflow_runner.py audit --warn-only
```
