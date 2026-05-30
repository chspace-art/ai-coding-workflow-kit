# Agent Communication Tools

This directory contains the public alpha of the workflow kit tooling.

## Included scripts

- `bootstrap_check.py`
  - Reads lessons, memory, skills, and recent task summaries before work starts.
- `workflow_runner.py`
  - Creates task envelopes, records role outputs, advances phases, and writes normalized summaries.

## Example commands

```powershell
python tools/agent-comm/bootstrap_check.py --keywords "workflow memory"
python tools/agent-comm/workflow_runner.py start --title "Refine onboarding copy" --keywords "copy onboarding"
python tools/agent-comm/workflow_runner.py confirm --task-id task_xxx --note "Requirement confirmed."
python tools/agent-comm/workflow_runner.py status --task-id task_xxx
python tools/agent-comm/workflow_runner.py audit --warn-only
```

## Scope

This public starter focuses on task structure and archive hygiene.
It does not include a model runtime, orchestration daemon, or hosted dashboard.
