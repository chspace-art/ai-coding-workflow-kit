# Release Notes: v0.1.0-alpha

`v0.1.0-alpha` is the first public cut of `ai-coding-workflow-kit`.

It turns an internal workflow pattern into a clean starter repository for teams who want AI-assisted development to leave behind better structure.

## What is included

- `bootstrap_check.py` for startup context gathering
- `workflow_runner.py` for task envelopes, phase transitions, and normalized summaries
- starter memory files under `docs/`
- repo-local skill templates under `.agents/skills/`
- GitHub community files for a healthier public repository
- a sanitized sample archive under `examples/sample-task/`

## Why this release exists

This release is meant to prove a narrow idea:

AI coding becomes easier to trust when the workflow is explicit.

Instead of relying on one long chat thread, the kit gives each meaningful task:

- a task id
- a requirement confirmation point
- structured `dev -> mentor -> qa` evidence
- a normalized completion summary
- durable memory inside the repository

## Current limitations

- single-cluster only
- no hosted dashboard
- no bundled browser automation
- no generic archive helper yet
- still early and intentionally small

## Suggested first use

Try it in a small side repository first.

1. Copy the starter into a test repo.
2. Adapt the `AGENTS.example.md` and skill templates.
3. Run one task end to end.
4. Decide what parts fit your own workflow and remove the rest.

## Thanks

Thanks to everyone experimenting with more durable ways to work with AI in real software projects.
