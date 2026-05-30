#!/usr/bin/env python3
"""Repository startup checklist helper.

This script prints the required pre-task checklist:
- repo lessons and common memory
- optional project memory
- repo skills available to the local coding agent
- similar archive summaries from the last N days
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
LESSONS = REPO_ROOT / "docs" / "LESSONS_LEARNED.md"
COMMON_MEMORY = REPO_ROOT / "docs" / "memory" / "COMMON.md"
SKILLS_INDEX = REPO_ROOT / ".agents" / "skills" / "INDEX.md"
ARCHIVE_DIR = REPO_ROOT / "share" / "archive"


@dataclass
class SkillInfo:
    name: str
    path: Path
    description: str


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def normalize_keywords(raw: str) -> list[str]:
    return [kw for kw in re.split(r"[\s,，;；]+", raw.strip()) if kw]


def relevant_lines(text: str, keywords: list[str], limit: int = 8) -> list[str]:
    if not keywords:
        return []
    hits: list[str] = []
    lowered_keywords = [kw.lower() for kw in keywords]
    for line in text.splitlines():
        lower = line.lower()
        if any(kw in lower for kw in lowered_keywords):
            hits.append(line.strip())
        if len(hits) >= limit:
            break
    return hits


def parse_skill(skill_file: Path) -> SkillInfo:
    text = read_text(skill_file)
    name = skill_file.parent.name
    description = ""
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            for line in parts[1].splitlines():
                if line.startswith("name:"):
                    name = line.split(":", 1)[1].strip().strip('"')
                elif line.startswith("description:"):
                    description = line.split(":", 1)[1].strip().strip('"')
    return SkillInfo(name=name, path=skill_file.relative_to(REPO_ROOT), description=description)


def list_repo_skills() -> list[SkillInfo]:
    skills_root = REPO_ROOT / ".agents" / "skills"
    if not skills_root.exists():
        return []
    return sorted(
        [parse_skill(path) for path in skills_root.glob("*/SKILL.md")],
        key=lambda item: item.name,
    )


def project_memory(project: str | None) -> dict[str, str]:
    if not project:
        return {}
    base = REPO_ROOT / project
    return {
        "lessons": read_text(base / "docs" / "LESSONS_LEARNED.md"),
        "project": read_text(base / "docs" / "memory" / "PROJECT.md"),
    }


def archive_summaries(keywords: list[str], days: int) -> list[dict]:
    if not ARCHIVE_DIR.exists():
        return []
    cutoff = datetime.now() - timedelta(days=days)
    results: list[dict] = []
    lowered_keywords = [kw.lower() for kw in keywords]
    for summary_file in ARCHIVE_DIR.glob("*/summary.json"):
        try:
            mtime = datetime.fromtimestamp(summary_file.stat().st_mtime)
        except OSError:
            continue
        if mtime < cutoff:
            continue
        haystack = summary_file.parent.name.lower() + "\n" + read_text(summary_file).lower()
        if lowered_keywords and not any(kw in haystack for kw in lowered_keywords):
            continue
        try:
            data = json.loads(read_text(summary_file))
        except json.JSONDecodeError:
            data = {"summary": read_text(summary_file)[:300]}
        results.append(
            {
                "task_dir": summary_file.parent.name,
                "path": str(summary_file.relative_to(REPO_ROOT)),
                "updated": mtime.isoformat(timespec="seconds"),
                "summary": data.get("summary") or data.get("final_status") or data.get("status", ""),
            }
        )
    return sorted(results, key=lambda item: item["updated"], reverse=True)


def build_report(args: argparse.Namespace) -> dict:
    keywords = normalize_keywords(args.keywords or "")
    lessons_text = read_text(LESSONS)
    common_text = read_text(COMMON_MEMORY)
    project_texts = project_memory(args.project)
    skills = list_repo_skills()
    archives = archive_summaries(keywords, args.days)

    return {
        "repo_root": str(REPO_ROOT),
        "keywords": keywords,
        "lessons_exists": LESSONS.exists(),
        "lessons_relevant": relevant_lines(lessons_text + "\n" + common_text, keywords),
        "project": args.project,
        "project_memory_read": bool(project_texts) and any(project_texts.values()),
        "skills_index_exists": SKILLS_INDEX.exists(),
        "skills": [skill.__dict__ | {"path": str(skill.path)} for skill in skills],
        "archives": archives,
    }


def print_checklist(report: dict) -> None:
    lesson_hits = report["lessons_relevant"]
    lesson_summary = "；".join(lesson_hits[:3]) if lesson_hits else "未命中关键词，已读取通用经验"
    skill_names = [skill["name"] for skill in report["skills"]]
    archive_names = [item["task_dir"] for item in report["archives"]]
    project_part = "已读" if report["project_memory_read"] else "不涉及或未发现项目级经验"

    print(f"✅ 已读 LESSONS_LEARNED.md（发现{len(lesson_hits)}条相关经验：{lesson_summary}）")
    print(f"✅ 已读子项目经验（{project_part}）")
    print(f"✅ 已识别可用Skills：{skill_names}")
    print(f"✅ 已检索历史同类任务（找到{len(archive_names)}条：{', '.join(archive_names) or '无'}）")


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

    parser = argparse.ArgumentParser(description="Repository startup checklist helper")
    parser.add_argument("--keywords", default="", help="Space or comma separated task keywords")
    parser.add_argument("--project", default=None, help="Optional subproject directory name")
    parser.add_argument("--days", type=int, default=30, help="Archive lookback days")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of checklist")
    args = parser.parse_args()

    report = build_report(args)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print_checklist(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
