# Archive Status

## Purpose

Archive summaries should stay machine-readable across tasks and repositories.

## Allowed final statuses

- `COMPLETED`
- `ACCEPTED`
- `DEPLOYED`
- `FAILED`
- `STOPPED`
- `ESCALATED`

Avoid new free-form status names in fresh summaries.

## Required summary fields

- `schema_version`
- `final_status`
- `normalized_status`
- `completion_gates`
- `ui_verification`
- `iterations`
