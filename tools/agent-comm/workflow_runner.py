#!/usr/bin/env python3
"""Single-cluster workflow runner for repository workflows.

The runner is the repo-local gatekeeper for the documented
dev -> mentor -> qa loop. It does not call model agents by itself; it creates
the task envelope, stores role outputs, advances phases, checks completion
gates, and writes normalized archive summaries.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import bootstrap_check


REPO_ROOT = Path(__file__).resolve().parents[2]
ARCHIVE_DIR = REPO_ROOT / "share" / "archive"
OVER_DIR = REPO_ROOT / "share" / "over"
MAX_LOOPS = 5
SUMMARY_SCHEMA_VERSION = 2

ROLE_ALIASES = {
    "dev": "dev",
    "dev-engineer": "dev",
    "mentor": "mentor",
    "mentor-engineer": "mentor",
    "qa": "qa",
    "qa-engineer": "qa",
}

ROLE_FULL_NAMES = {
    "dev": "dev-engineer",
    "mentor": "mentor-engineer",
    "qa": "qa-engineer",
}

ROLE_ORDER = ["dev", "mentor", "qa"]
SUCCESS_FINAL_STATUSES = {"COMPLETED", "ACCEPTED", "DEPLOYED"}
FINAL_STATUSES = sorted(SUCCESS_FINAL_STATUSES | {"FAILED", "STOPPED", "ESCALATED"})

ARCHIVE_STATUS_ALIASES = {
    "accepted": "ACCEPTED",
    "analysis_and_guardrails_applied": "COMPLETED",
    "completed": "COMPLETED",
    "completed_static_verification": "COMPLETED",
    "delivered": "DEPLOYED",
    "deployed": "DEPLOYED",
    "done": "COMPLETED",
    "failed": "FAILED",
    "implemented_real_data_baseline": "COMPLETED",
    "ready_for_review": "READY_FOR_REVIEW",
    "source_collection_done": "COMPLETED",
    "stopped": "STOPPED",
    "ui_open_for_user_review": "READY_FOR_REVIEW",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def slugify(text: str, fallback: str = "task") -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", text.strip().lower()).strip("_")
    return slug[:48] or fallback


def generate_task_id(title: str) -> str:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    slug = slugify(title, "workflow")
    return f"task_{stamp}_{slug}"


def task_dir(task_id: str) -> Path:
    return ARCHIVE_DIR / task_id


def state_path(task_id: str) -> Path:
    return task_dir(task_id) / "state.json"


def read_json(path: Path, fallback: Any = None) -> Any:
    if not path.exists():
        return fallback
    with path.open("r", encoding="utf-8-sig") as fh:
        return json.load(fh)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
        fh.write("\n")


def normalize_role(role: str) -> str:
    normalized = ROLE_ALIASES.get(role.strip().lower())
    if not normalized:
        valid = ", ".join(sorted(ROLE_ALIASES))
        raise SystemExit(f"Unknown role: {role}. Valid roles: {valid}")
    return normalized


def load_state(task_id: str) -> dict[str, Any]:
    state = read_json(state_path(task_id))
    if not state:
        raise SystemExit(f"Task state not found: {state_path(task_id)}")
    return state


def save_state(state: dict[str, Any]) -> None:
    state["updated_at"] = now_iso()
    write_json(state_path(state["task_id"]), state)


def parse_key_values(values: list[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for item in values:
        if "=" not in item:
            raise SystemExit(f"--set expects key=value, got: {item}")
        key, value = item.split("=", 1)
        result[key.strip()] = value.strip()
    return result


def split_items(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [item.strip() for item in re.split(r"[,;，；]\s*", raw) if item.strip()]


def role_key_of(item: dict[str, Any]) -> str:
    role = str(item.get("role_key") or item.get("role") or "").strip().lower()
    return ROLE_ALIASES.get(role, role)


def score_value(item: dict[str, Any]) -> float | None:
    score = item.get("total_score", item.get("score"))
    if isinstance(score, (int, float)):
        return float(score)
    text = str(score or "").strip()
    if text.replace(".", "", 1).isdigit():
        return float(text)
    return None


def decision_value(item: dict[str, Any]) -> str:
    return str(item.get("decision") or item.get("status") or "").strip().upper()


def is_passing_record(item: dict[str, Any], min_score: float = 80) -> bool:
    decision = decision_value(item)
    score = score_value(item)
    return decision == "PASS" and (score is None or score >= min_score)


def normalize_archive_status(raw: Any) -> str | None:
    if raw is None:
        return None
    text = str(raw).strip()
    if not text:
        return None
    upper = text.upper()
    if upper in FINAL_STATUSES or upper == "READY_FOR_REVIEW":
        return upper
    return ARCHIVE_STATUS_ALIASES.get(text.lower())


def build_handoff_md(state: dict[str, Any]) -> str:
    task_id = state["task_id"]
    title = state["title"]
    phase = state.get("phase", "needs_confirmation")
    skills = ", ".join(state.get("recommended_skills", [])) or "none"
    return f"""# Single-Cluster Handoff

TaskID: `{task_id}`
Mode: `single_cluster`
Current phase: `{phase}`

## Original Task

{title}

## Required Startup Evidence

- Bootstrap report: `startup_report.json`
- Startup checklist: `startup_checklist.txt`
- Recommended skills: {skills}

## Required Gate

Confirm the requirement before the first dev record, unless the user gave an
extremely explicit one-line change:

```powershell
python tools/agent-comm/workflow_runner.py confirm --task-id {task_id} --note "User confirmed the requirement understanding."
```

## Role Loop

1. `dev-engineer` records implementation evidence.
2. `mentor-engineer` records review score and decision.
3. `qa-engineer` records real command/browser evidence.
4. Runner advances state or returns to `dev` until pass/fuse.

## Record Commands

```powershell
python tools/agent-comm/workflow_runner.py record --task-id {task_id} --role dev --status DONE --summary "..." --evidence "..."
python tools/agent-comm/workflow_runner.py record --task-id {task_id} --role mentor --decision PASS --score 85 --summary "..." --evidence "..."
python tools/agent-comm/workflow_runner.py record --task-id {task_id} --role qa --decision PASS --score 90 --summary "..." --evidence "..."
python tools/agent-comm/workflow_runner.py complete --task-id {task_id} --summary "..."
```
"""


def start_task(args: argparse.Namespace) -> int:
    task_id = args.task_id or generate_task_id(args.title)
    out_dir = task_dir(task_id)
    if out_dir.exists() and not args.force:
        raise SystemExit(f"Task already exists: {out_dir}. Use --force to overwrite metadata.")

    keywords = split_items(args.keywords) or split_items(args.title)
    bootstrap_args = argparse.Namespace(
        keywords=" ".join(keywords),
        project=args.project,
        days=args.days,
        json=False,
    )
    report = bootstrap_check.build_report(bootstrap_args)
    lesson_hits = report["lessons_relevant"]
    lesson_summary = "；".join(lesson_hits[:3]) if lesson_hits else "未命中关键词，已读取通用经验"
    skill_names = [skill["name"] for skill in report["skills"]]
    archive_names = [item["task_dir"] for item in report["archives"]]
    project_part = "已读" if report["project_memory_read"] else "不涉及或未发现项目级经验"
    checklist_lines = [
        f"✅ 已读 LESSONS_LEARNED.md（发现{len(lesson_hits)}条相关经验：{lesson_summary}）",
        f"✅ 已读子项目经验（{project_part}）",
        f"✅ 已识别可用Skills：{skill_names}",
        f"✅ 已检索历史同类任务（找到{len(archive_names)}条：{', '.join(archive_names) or '无'}）",
    ]

    requirements_confirmed = bool(args.understanding_confirmed)
    phase = "dev" if requirements_confirmed else "needs_confirmation"
    state = {
        "task_id": task_id,
        "mode": "single_cluster",
        "title": args.title,
        "project": args.project,
        "keywords": keywords,
        "phase": phase,
        "iteration": 0,
        "loop_count": 0,
        "max_loops": MAX_LOOPS,
        "requirements_confirmed": requirements_confirmed,
        "requirements_confirmation": {
            "confirmed_at": now_iso(),
            "note": args.understanding_note,
        } if requirements_confirmed else None,
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "archive_dir": str(out_dir.relative_to(REPO_ROOT)),
        "recommended_skills": skill_names,
        "startup_checklist": checklist_lines,
        "last_transition": f"start -> {phase}",
    }

    write_json(out_dir / "startup_report.json", report)
    (out_dir / "startup_checklist.txt").write_text("\n".join(checklist_lines) + "\n", encoding="utf-8")
    write_json(out_dir / "task.json", {
        "task_id": task_id,
        "title": args.title,
        "project": args.project,
        "mode": "single_cluster",
        "keywords": keywords,
        "created_at": state["created_at"],
    })
    write_json(state_path(task_id), state)
    (out_dir / "handoff.md").write_text(build_handoff_md(state), encoding="utf-8")

    if not args.no_print_checklist:
        print("\n".join(checklist_lines))
    print(f"TaskID: {task_id}")
    print(f"Archive: {out_dir}")
    print(f"Next phase: {phase}")
    return 0


def confirm_task(args: argparse.Namespace) -> int:
    state = load_state(args.task_id)
    state["requirements_confirmed"] = True
    state["requirements_confirmation"] = {
        "confirmed_at": now_iso(),
        "note": args.note,
    }
    if state.get("phase") == "needs_confirmation":
        state["phase"] = "dev"
    state["last_transition"] = "requirements confirmed -> dev"
    save_state(state)
    write_json(task_dir(args.task_id) / "requirements_confirmation.json", state["requirements_confirmation"])
    print(f"Requirements confirmed: {args.task_id}")
    print(f"Phase: {state['phase']}")
    return 0


def next_iteration_for(role: str, state: dict[str, Any]) -> int:
    if role == "dev":
        return int(state.get("iteration") or 0) + 1
    current = int(state.get("iteration") or 0)
    return max(current, 1)


def role_file(task_id: str, iteration: int, role: str) -> Path:
    return task_dir(task_id) / f"iter_{iteration:02d}_{role}.json"


def transition_after_record(state: dict[str, Any], role: str, payload: dict[str, Any]) -> None:
    decision = decision_value(payload)
    score = score_value(payload)

    if role == "dev":
        state["phase"] = "mentor"
        state["last_transition"] = "dev -> mentor"
        return

    if role == "mentor":
        if decision == "PASS" and (score is None or score >= 80):
            state["phase"] = "qa"
            state["last_transition"] = "mentor PASS -> qa"
        else:
            state["phase"] = "dev"
            state["loop_count"] = int(state.get("loop_count") or 0) + 1
            state["last_transition"] = "mentor not-pass -> dev"
        return

    if role == "qa":
        if decision == "PASS" and (score is None or score >= 80):
            state["phase"] = "ready_to_complete"
            state["last_transition"] = "qa PASS -> ready_to_complete"
        else:
            state["phase"] = "dev"
            state["loop_count"] = int(state.get("loop_count") or 0) + 1
            state["last_transition"] = "qa not-pass -> dev"

    if int(state.get("loop_count") or 0) >= int(state.get("max_loops") or MAX_LOOPS):
        state["phase"] = "fused"
        state["last_transition"] = "loop fuse -> user arbitration"


def validate_record_gate(state: dict[str, Any], role: str, force_phase: bool) -> None:
    if force_phase:
        return
    phase = str(state.get("phase") or "")
    if role == "dev" and not state.get("requirements_confirmed"):
        raise SystemExit("Requirements are not confirmed. Run `workflow_runner.py confirm` first, or use --force-phase with a clear reason.")
    if phase in {"completed", "failed", "stopped", "escalated"}:
        raise SystemExit(f"Task is already terminal: phase={phase}")
    if phase == "needs_confirmation":
        raise SystemExit("Task is waiting for requirement confirmation. Run `workflow_runner.py confirm` first.")
    expected = "dev" if phase in {"dev", "fused"} else phase
    if role != expected:
        raise SystemExit(f"Role {role} cannot record while phase is {phase}. Use --force-phase only for documented recovery.")


def build_record_payload(args: argparse.Namespace, role: str, iteration: int) -> dict[str, Any]:
    if args.from_json:
        payload = read_json(Path(args.from_json))
        if not isinstance(payload, dict):
            raise SystemExit("--from-json must point to a JSON object")
    else:
        payload = {
            "role": ROLE_FULL_NAMES[role],
            "iteration": iteration,
            "status": args.status,
            "summary": args.summary,
            "evidence": args.evidence,
            "files_changed": split_items(args.files_changed),
        }
        if args.decision:
            payload["decision"] = args.decision.upper()
        if args.score is not None:
            payload["total_score"] = args.score
        if args.known_issue:
            payload["known_issues"] = args.known_issue

    payload.setdefault("role", ROLE_FULL_NAMES[role])
    payload["role_key"] = role
    payload["iteration"] = iteration
    payload["archived_at"] = now_iso()
    for key, value in parse_key_values(args.set).items():
        payload[key] = value
    return payload


def record_iteration(args: argparse.Namespace) -> int:
    role = normalize_role(args.role)
    state = load_state(args.task_id)
    validate_record_gate(state, role, args.force_phase)
    iteration = args.iteration or next_iteration_for(role, state)
    path = role_file(args.task_id, iteration, role)
    if path.exists() and not args.overwrite:
        raise SystemExit(f"Iteration file exists: {path}. Use --overwrite to replace it.")

    payload = build_record_payload(args, role, iteration)
    evidence = payload.get("evidence") or []
    if isinstance(evidence, str):
        evidence = [evidence]
        payload["evidence"] = evidence
    warnings = []
    if role in {"dev", "qa"} and not evidence:
        warnings.append(f"{role} evidence is empty")
    if role == "mentor" and not evidence:
        warnings.append("mentor evidence is empty")
    if warnings:
        payload["runner_warnings"] = warnings

    write_json(path, payload)
    state["iteration"] = max(int(state.get("iteration") or 0), iteration)
    state["last_role"] = role
    state["last_record"] = str(path.relative_to(REPO_ROOT))
    transition_after_record(state, role, payload)
    save_state(state)

    print(f"Archived: {path}")
    print(f"Phase: {state['phase']}")
    if warnings:
        print("Warnings: " + "; ".join(warnings))
    return 0


def collect_iterations(task_id: str) -> list[dict[str, Any]]:
    items = []
    for path in sorted(task_dir(task_id).glob("iter_*.json")):
        payload = read_json(path, {})
        payload["_file"] = str(path.relative_to(REPO_ROOT))
        items.append(payload)
    return items


def latest_record(iterations: list[dict[str, Any]], role: str) -> dict[str, Any] | None:
    for item in reversed(iterations):
        if role_key_of(item) == role:
            return item
    return None


def validate_completion_gates(args: argparse.Namespace, state: dict[str, Any], iterations: list[dict[str, Any]], final_status: str) -> list[str]:
    if final_status not in SUCCESS_FINAL_STATUSES:
        return []

    errors = []
    if not state.get("requirements_confirmed"):
        errors.append("requirements_confirmed is false")
    if latest_record(iterations, "dev") is None:
        errors.append("missing dev record")
    mentor = latest_record(iterations, "mentor")
    if mentor is None or not is_passing_record(mentor):
        errors.append("latest mentor record is missing or not PASS >= 80")
    qa = latest_record(iterations, "qa")
    if qa is None or not is_passing_record(qa):
        errors.append("latest qa record is missing or not PASS >= 80")

    if args.requires_ui:
        if not args.ui_url:
            errors.append("--requires-ui needs --ui-url")
        if not args.ui_opened:
            errors.append("--requires-ui needs --ui-opened")
    return errors


def complete_task(args: argparse.Namespace) -> int:
    state = load_state(args.task_id)
    iterations = collect_iterations(args.task_id)
    final_status = args.final_status.upper()
    gate_errors = validate_completion_gates(args, state, iterations, final_status)
    if gate_errors and not args.allow_incomplete:
        print("Completion gates failed:")
        for item in gate_errors:
            print(f"- {item}")
        print("Use --allow-incomplete --gate-note \"...\" only for an explicit, documented exception.")
        return 2
    if gate_errors and not args.gate_note:
        raise SystemExit("--allow-incomplete requires --gate-note when gates fail")

    completed_at = now_iso()
    summary = {
        "schema_version": SUMMARY_SCHEMA_VERSION,
        "task_id": args.task_id,
        "title": state.get("title"),
        "mode": "single_cluster",
        "project": state.get("project"),
        "final_status": final_status,
        "normalized_status": final_status,
        "summary": args.summary,
        "total_records": len(iterations),
        "loop_count": state.get("loop_count", 0),
        "completed_at": completed_at,
        "requirements_confirmed": bool(state.get("requirements_confirmed")),
        "completion_gates": {
            "passed": not gate_errors,
            "errors": gate_errors,
            "override_note": args.gate_note if gate_errors else "",
        },
        "ui_verification": {
            "required": bool(args.requires_ui),
            "opened": bool(args.ui_opened),
            "url": args.ui_url or "",
            "user_accepted": bool(args.user_accepted),
        },
        "iterations": [
            {
                "file": item.get("_file"),
                "role": item.get("role") or item.get("role_key"),
                "iteration": item.get("iteration"),
                "status": item.get("status"),
                "decision": item.get("decision"),
                "total_score": item.get("total_score"),
                "summary": item.get("summary", ""),
            }
            for item in iterations
        ],
    }
    write_json(task_dir(args.task_id) / "summary.json", summary)

    state["phase"] = "completed" if final_status in SUCCESS_FINAL_STATUSES else final_status.lower()
    state["final_status"] = final_status
    state["completed_at"] = completed_at
    save_state(state)

    OVER_DIR.mkdir(parents=True, exist_ok=True)
    write_json(OVER_DIR / f"{args.task_id}_{final_status.lower()}.json", {
        "schema_version": SUMMARY_SCHEMA_VERSION,
        "task_id": args.task_id,
        "status": final_status,
        "summary": args.summary,
        "timestamp": completed_at,
        "archive_dir": str(task_dir(args.task_id).relative_to(REPO_ROOT)),
        "completion_gates": summary["completion_gates"],
    })

    print(f"Summary: {task_dir(args.task_id) / 'summary.json'}")
    print(f"Final status: {final_status}")
    return 0


def print_status(args: argparse.Namespace) -> int:
    state = load_state(args.task_id)
    iterations = collect_iterations(args.task_id)
    if args.json:
        print(json.dumps({"state": state, "iterations": iterations}, ensure_ascii=False, indent=2))
        return 0
    print(f"TaskID: {state['task_id']}")
    print(f"Title: {state.get('title', '')}")
    print(f"Phase: {state.get('phase')}")
    print(f"Requirements confirmed: {bool(state.get('requirements_confirmed'))}")
    print(f"Iteration: {state.get('iteration')} | loops: {state.get('loop_count')}/{state.get('max_loops')}")
    print(f"Last transition: {state.get('last_transition', '')}")
    print(f"Records: {len(iterations)}")
    return 0


def print_template(args: argparse.Namespace) -> int:
    role = normalize_role(args.role)
    template = {
        "role": ROLE_FULL_NAMES[role],
        "iteration": args.iteration,
        "status": "DONE",
        "summary": "",
        "evidence": [],
    }
    if role == "mentor":
        template.update({"decision": "PASS", "total_score": 80, "specific_action_items": []})
    elif role == "qa":
        template.update({"decision": "PASS", "total_score": 80, "test_commands_executed": []})
    else:
        template.update({"files_changed": [], "known_issues": []})
    print(json.dumps(template, ensure_ascii=False, indent=2))
    return 0


def audit_archives(args: argparse.Namespace) -> int:
    rows = []
    counts: Counter[str] = Counter()
    parse_errors = []
    missing_status = []
    unknown_status = []
    legacy_schema = []

    for path in sorted(ARCHIVE_DIR.glob("*/summary.json")):
        try:
            data = read_json(path)
        except Exception as exc:  # noqa: BLE001 - report bad archive files, do not hide them.
            parse_errors.append({"path": str(path.relative_to(REPO_ROOT)), "error": str(exc)})
            continue
        raw = data.get("normalized_status") or data.get("final_status") or data.get("status")
        normalized = normalize_archive_status(raw)
        if raw is None:
            missing_status.append(str(path.relative_to(REPO_ROOT)))
        elif normalized is None:
            unknown_status.append({"path": str(path.relative_to(REPO_ROOT)), "status": raw})
        else:
            counts[normalized] += 1
        if data.get("schema_version") != SUMMARY_SCHEMA_VERSION:
            legacy_schema.append(str(path.relative_to(REPO_ROOT)))
        rows.append({"path": str(path.relative_to(REPO_ROOT)), "raw_status": raw, "normalized_status": normalized})

    report = {
        "schema_version": SUMMARY_SCHEMA_VERSION,
        "summary_files": len(rows) + len(parse_errors),
        "status_counts": dict(sorted(counts.items())),
        "parse_errors": parse_errors,
        "missing_status": missing_status,
        "unknown_status": unknown_status,
        "legacy_schema_count": len(legacy_schema),
        "legacy_schema": legacy_schema[:25],
    }
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"Summary files: {report['summary_files']}")
        print(f"Status counts: {report['status_counts']}")
        print(f"Parse errors: {len(parse_errors)}")
        print(f"Missing status: {len(missing_status)}")
        print(f"Unknown status: {len(unknown_status)}")
        print(f"Legacy schema: {len(legacy_schema)}")

    has_errors = bool(parse_errors or missing_status or unknown_status)
    return 0 if args.warn_only or not has_errors else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Repository single-cluster workflow runner")
    sub = parser.add_subparsers(dest="command", required=True)

    start = sub.add_parser("start", help="Create a task envelope and bootstrap report")
    start.add_argument("--title", required=True, help="Original user task or task title")
    start.add_argument("--task-id", default=None, help="Explicit task id")
    start.add_argument("--keywords", default="", help="Comma/space separated bootstrap keywords")
    start.add_argument("--project", default=None, help="Optional subproject directory")
    start.add_argument("--days", type=int, default=30, help="Archive lookback days")
    start.add_argument("--understanding-confirmed", action="store_true", help="Start directly in dev because the requirement is already confirmed")
    start.add_argument("--understanding-note", default="", help="Why it is safe to start without a separate confirmation turn")
    start.add_argument("--force", action="store_true", help="Overwrite metadata if task exists")
    start.add_argument("--no-print-checklist", action="store_true", help="Do not print checklist")
    start.set_defaults(func=start_task)

    confirm = sub.add_parser("confirm", help="Mark requirement understanding as confirmed and move to dev")
    confirm.add_argument("--task-id", required=True)
    confirm.add_argument("--note", required=True)
    confirm.set_defaults(func=confirm_task)

    record = sub.add_parser("record", help="Archive a dev/mentor/qa role output and advance state")
    record.add_argument("--task-id", required=True)
    record.add_argument("--role", required=True)
    record.add_argument("--iteration", type=int, default=None)
    record.add_argument("--from-json", default=None, help="Read role output from a JSON file")
    record.add_argument("--status", default="DONE")
    record.add_argument("--decision", default=None)
    record.add_argument("--score", type=float, default=None)
    record.add_argument("--summary", default="")
    record.add_argument("--evidence", action="append", default=[])
    record.add_argument("--files-changed", default="")
    record.add_argument("--known-issue", action="append", default=[])
    record.add_argument("--set", action="append", default=[], help="Additional key=value metadata")
    record.add_argument("--overwrite", action="store_true")
    record.add_argument("--force-phase", action="store_true", help="Override phase order for documented recovery only")
    record.set_defaults(func=record_iteration)

    complete = sub.add_parser("complete", help="Write summary.json and over marker")
    complete.add_argument("--task-id", required=True)
    complete.add_argument("--summary", required=True)
    complete.add_argument("--final-status", default="COMPLETED", choices=FINAL_STATUSES)
    complete.add_argument("--requires-ui", action="store_true", help="Require UI verification metadata before successful completion")
    complete.add_argument("--ui-url", default="")
    complete.add_argument("--ui-opened", action="store_true")
    complete.add_argument("--user-accepted", action="store_true")
    complete.add_argument("--allow-incomplete", action="store_true", help="Allow completion with failed gates only when documented")
    complete.add_argument("--gate-note", default="", help="Required explanation when --allow-incomplete bypasses gates")
    complete.set_defaults(func=complete_task)

    status = sub.add_parser("status", help="Print task state")
    status.add_argument("--task-id", required=True)
    status.add_argument("--json", action="store_true")
    status.set_defaults(func=print_status)

    template = sub.add_parser("template", help="Print role JSON template")
    template.add_argument("--role", required=True)
    template.add_argument("--iteration", type=int, default=1)
    template.set_defaults(func=print_template)

    audit = sub.add_parser("audit", help="Audit archive summary status/schema health")
    audit.add_argument("--json", action="store_true")
    audit.add_argument("--warn-only", action="store_true", help="Return 0 even when legacy/bad summaries exist")
    audit.set_defaults(func=audit_archives)

    return parser


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
