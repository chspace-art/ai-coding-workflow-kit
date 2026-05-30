# AI Coding Workflow Kit

`ai-coding-workflow-kit` is a small starter repository for teams who want AI coding work to be traceable, reviewable, and memory-aware.

It packages a lightweight workflow around four ideas:

1. Start every meaningful task with a task envelope.
2. Confirm the requirement before implementation begins.
3. Record `dev -> mentor -> qa` evidence as structured files.
4. Keep durable lessons in repo memory instead of repeating the same mistakes.

## What is included

- `tools/agent-comm/bootstrap_check.py`
  - Reads lessons, memory, skills, and recent task summaries before work starts.
- `tools/agent-comm/workflow_runner.py`
  - Creates task folders, tracks phase transitions, records role outputs, and writes normalized summaries.
- `docs/`
  - Starter memory and workflow guidance.
- `.agents/skills/`
  - Generic repo-local skill templates for workflow, memory, UI verification, and git governance.
- `examples/sample-task/`
  - A sanitized example of the archive schema produced by the runner.

## Quick start

```powershell
python tools/agent-comm/bootstrap_check.py --keywords "workflow memory qa"
python tools/agent-comm/workflow_runner.py start --title "Example task" --keywords "workflow example"
python tools/agent-comm/workflow_runner.py confirm --task-id task_xxx --note "Requirement confirmed."
python tools/agent-comm/workflow_runner.py status --task-id task_xxx
```

## Suggested repository layout

```text
.
|-- .agents/skills/
|-- docs/
|   |-- LESSONS_LEARNED.md
|   `-- memory/
|-- share/
|   |-- archive/
|   `-- over/
`-- tools/agent-comm/
```

## Design goals

- Small enough to understand in one sitting.
- Strong enough to prevent the most common AI workflow drift.
- Easy to adapt without forcing a specific model vendor or IDE.

## Current scope

This starter focuses on single-cluster task orchestration and repo-local memory.
It does not ship a model runtime, browser automation layer, or hosted dashboard.

## Maintainer

Maintained by Licheng.

- GitHub: [@chspace-art](https://github.com/chspace-art)
- Contact: please use GitHub Issues for questions and bug reports.

## Publishing checklist

Before making this public:

1. Replace placeholder maintainer details in the community files.
2. Pick the final license if you do not want MIT.
3. Verify that no private paths, secrets, archives, or product code were copied in.
4. Run one sample task so the repository has a real, public-safe walkthrough.
