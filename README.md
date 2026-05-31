# AI Coding Workflow Kit

`ai-coding-workflow-kit` is a small starter repository for teams who want AI coding work to be traceable, reviewable, and memory-aware.

It is built for the moment where AI coding starts to feel useful but messy:

- tasks blur together
- requirement changes are not captured clearly
- reviews happen as chat impressions instead of evidence
- the same workflow mistakes repeat because nothing durable gets recorded

This kit packages a lightweight workflow around four ideas:

1. Start every meaningful task with a task envelope.
2. Confirm the requirement before implementation begins.
3. Record `dev -> mentor -> qa` evidence as structured files.
4. Keep durable lessons in repo memory instead of repeating the same mistakes.

## Who this is for

- solo builders using AI heavily in daily development
- small teams that want more structure without adopting a heavy platform
- maintainers who want AI-assisted work to leave behind readable artifacts

## What problem it solves

Most AI coding workflows are good at producing code and weak at producing process.

This repository is an opinionated starter for adding just enough process to make AI work easier to inspect and reuse:

- startup context checks
- requirement confirmation before implementation
- structured `dev -> mentor -> qa` records
- normalized archive summaries
- repo-local memory that survives beyond one chat session

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
  - A sanitized example of the archive schema produced by the runner, plus a walkthrough README.

## Core loop

```text
Understand -> Build -> Review -> Verify -> Remember
```

The goal is not to automate judgment away. The goal is to make judgment visible and replayable.

## Quick start

```powershell
python tools/agent-comm/bootstrap_check.py --keywords "workflow memory qa"
python tools/agent-comm/workflow_runner.py start --title "Example task" --keywords "workflow example"
python tools/agent-comm/workflow_runner.py confirm --task-id task_xxx --note "Requirement confirmed."
python tools/agent-comm/workflow_runner.py status --task-id task_xxx
```

## A typical task flow

```powershell
python tools/agent-comm/bootstrap_check.py --keywords "bug form validation"
python tools/agent-comm/workflow_runner.py start --title "Fix form validation bug" --keywords "bug form validation"
python tools/agent-comm/workflow_runner.py confirm --task-id task_xxx --note "Requirement confirmed."
python tools/agent-comm/workflow_runner.py record --task-id task_xxx --role dev --summary "Implemented the fix" --evidence "Updated validation logic."
python tools/agent-comm/workflow_runner.py record --task-id task_xxx --role mentor --decision PASS --score 86 --summary "Review passed"
python tools/agent-comm/workflow_runner.py record --task-id task_xxx --role qa --decision PASS --score 91 --summary "QA passed"
python tools/agent-comm/workflow_runner.py complete --task-id task_xxx --summary "Validation bug fixed."
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

## What this kit does not try to do

- It does not include a model runtime.
- It does not require a hosted dashboard.
- It does not assume one editor, one agent framework, or one programming language.
- It does not replace human review. It makes review easier to trace.

## Current scope

This starter focuses on single-cluster task orchestration and repo-local memory.
It does not ship a model runtime, browser automation layer, or hosted dashboard.

## Repository status

Current release line: `v0.1.0-alpha`

This is an early public extraction from a real working repository. The core ideas are stable enough to publish, but the kit is intentionally small and still evolving.

If you try it, start by adapting the templates and scripts to your own repo instead of treating it as a drop-in platform.

## Maintainer

Maintained by Licheng.

- GitHub: [@chspace-art](https://github.com/chspace-art)
- Contact: please use GitHub Issues for questions and bug reports.

## Roadmap

- tighten the public starter docs around one full example task
- add a generic archive helper without hard-coded local paths
- add a migration guide for teams moving from ad hoc chat workflows
- improve cross-platform guidance for Windows, macOS, and Linux users

## Contributing

Contributions are welcome, especially in these areas:

- clearer onboarding docs
- stronger example tasks
- cross-platform workflow notes
- tighter archive and memory conventions

Start with [CONTRIBUTING.md](./CONTRIBUTING.md).

## Example walkthrough

If you want to see the archive format before adopting the kit, start with [examples/sample-task/README.md](./examples/sample-task/README.md).

It walks through:

- what a finished task archive looks like
- how `dev`, `mentor`, and `qa` records relate to `summary.json`
- which commands create and complete a task

## Publishing checklist

Before making this public:

1. Replace placeholder maintainer details in the community files.
2. Pick the final license if you do not want MIT.
3. Verify that no private paths, secrets, archives, or product code were copied in.
4. Run one sample task so the repository has a real, public-safe walkthrough.
