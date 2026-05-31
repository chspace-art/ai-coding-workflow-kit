# Sample Task Walkthrough

This folder shows what a minimal completed task archive looks like.

## Files

- `summary.json`
  - the final task summary written by `workflow_runner.py complete`
- `iter_01_dev.json`
  - implementation evidence from the development step
- `iter_01_mentor.json`
  - review evidence from the review step
- `iter_01_qa.json`
  - verification evidence from the QA step

## How to read it

Start with `summary.json`.

That file tells you:

- the task id
- whether requirements were confirmed
- whether completion gates passed
- whether UI verification was required
- which iteration records belong to the task

Then open each `iter_*.json` file to see what the role contributed.

## Why this matters

Many AI workflows leave important decisions scattered across chat history.

This example shows the opposite pattern:

- one task id
- one archive folder
- structured role outputs
- one normalized final summary

## Typical command flow

```powershell
python tools/agent-comm/bootstrap_check.py --keywords "example workflow"
python tools/agent-comm/workflow_runner.py start --title "Example workflow task" --keywords "example workflow"
python tools/agent-comm/workflow_runner.py confirm --task-id task_xxx --note "Requirement confirmed."
python tools/agent-comm/workflow_runner.py record --task-id task_xxx --role dev --summary "Implemented the change" --evidence "..."
python tools/agent-comm/workflow_runner.py record --task-id task_xxx --role mentor --decision PASS --score 86 --summary "Review passed"
python tools/agent-comm/workflow_runner.py record --task-id task_xxx --role qa --decision PASS --score 91 --summary "QA passed"
python tools/agent-comm/workflow_runner.py complete --task-id task_xxx --summary "Task completed."
```

## Next step

After reading this example, adapt the starter files in `templates/` and `.agents/skills/` to match your own repository.
