#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT_LINE_BUDGET = 200
EXPECTED_RULES = ("typescript.md", "tests.md", "backend.md")
VOLATILE_CHECKS = {
    "dated log markers": re.compile(r"\b20\d{2}-\d{2}-\d{2}\b|last updated", re.IGNORECASE),
    "task queue markers": re.compile(r"\btask queue\b|\bassigned to\b|\bpriority\b|\bstatus\b", re.IGNORECASE),
    "progress markers": re.compile(
        r"\bin[_ -]?progress\b|\bphase\s+\d+\b|\bstatus:\s*(pending|completed|in progress)\b",
        re.IGNORECASE,
    ),
    "log section markers": re.compile(r"\bcompletion log\b|\borchestration log\b|\blive log\b", re.IGNORECASE),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Hook-time memory hygiene audit.")
    parser.add_argument("--event", required=True, help="Hook event name.")
    parser.add_argument("--agent", default="", help="Agent name for log context.")
    parser.add_argument("--root", default="", help="Project root override.")
    return parser.parse_args()


def resolve_root(root_arg: str) -> Path:
    if root_arg:
        return Path(root_arg).resolve()
    return Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()).resolve()


def read_text(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return ""
    return path.read_text(encoding="utf-8")


def count_lines(path: Path) -> int:
    text = read_text(path)
    if not text:
        return 0
    return len(text.splitlines())


def read_stdin_payload() -> dict:
    raw = sys.stdin.read().strip()
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"raw": raw}


def ensure_memory_files(root: Path) -> Path:
    memory_dir = root / ".claude" / "memory"
    memory_dir.mkdir(parents=True, exist_ok=True)

    recent_learnings = memory_dir / "recent-learnings.md"
    if not recent_learnings.exists():
        recent_learnings.write_text(
            "# Recent Learnings\n\nAppend short notes at the top. Purge aggressively.\n",
            encoding="utf-8",
        )

    return memory_dir


def audit_memory(root: Path) -> dict:
    files: dict[str, int] = {}
    findings: list[str] = []

    root_claude = root / "CLAUDE.md"
    quick_ref = root / "QUICK_REF.md"
    gitignore = root / ".gitignore"

    files["CLAUDE.md"] = count_lines(root_claude)
    files["QUICK_REF.md"] = count_lines(quick_ref)

    if not root_claude.exists():
        findings.append("Missing root CLAUDE.md.")
    else:
        root_text = read_text(root_claude)

        if files["CLAUDE.md"] > ROOT_LINE_BUDGET:
            findings.append(
                f"Root CLAUDE.md is {files['CLAUDE.md']} lines; target is <= {ROOT_LINE_BUDGET}."
            )

        for label, pattern in VOLATILE_CHECKS.items():
            if pattern.search(root_text):
                findings.append(f"Root CLAUDE.md still contains {label}.")

        if root_text.count("```") > 6:
            findings.append("Root CLAUDE.md contains many code blocks; move command-heavy sections to QUICK_REF.md.")

    if not quick_ref.exists():
        findings.append("Missing QUICK_REF.md for commands and runbooks.")

    rules_dir = root / ".claude" / "rules"
    for rule_name in EXPECTED_RULES:
        rule_path = rules_dir / rule_name
        files[str(rule_path.relative_to(root))] = count_lines(rule_path)
        if not rule_path.exists():
            findings.append(f"Missing shared rule file: .claude/rules/{rule_name}")

    recent_learnings = root / ".claude" / "memory" / "recent-learnings.md"
    files[str(recent_learnings.relative_to(root))] = count_lines(recent_learnings)
    if not recent_learnings.exists():
        findings.append("Missing .claude/memory/recent-learnings.md.")

    for scope_name in ("backend", "frontend"):
        scope_dir = root / scope_name
        scope_claude = scope_dir / "CLAUDE.md"
        if scope_dir.is_dir():
            files[str(scope_claude.relative_to(root))] = count_lines(scope_claude)
            if not scope_claude.exists():
                findings.append(f"Missing scoped memory file: {scope_name}/CLAUDE.md")

    gitignore_text = read_text(gitignore)
    if ".claude/" in gitignore_text:
        missing_exception = (
            "!.claude/rules/" not in gitignore_text
            or "!.claude/memory/recent-learnings.md" not in gitignore_text
        )
        if missing_exception:
            findings.append(
                ".gitignore ignores .claude/ without explicit exceptions for shared rules or recent-learnings."
            )

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "root": str(root),
        "files": files,
        "findings": findings,
    }


def render_markdown(report: dict) -> str:
    lines = [
        "# Memory Audit",
        "",
        f"- Timestamp: {report['timestamp']}",
        f"- Root: {report['root']}",
        "",
        "## File Sizes",
        "",
    ]

    for path, line_count in sorted(report["files"].items()):
        lines.append(f"- `{path}`: {line_count} lines")

    lines.extend(["", "## Findings", ""])
    findings = report["findings"] or ["No issues detected."]
    for finding in findings:
        lines.append(f"- {finding}")

    lines.append("")
    return "\n".join(lines)


def append_checkpoint(memory_dir: Path, event: str, report: dict) -> None:
    recent_learnings = memory_dir / "recent-learnings.md"
    existing = read_text(recent_learnings)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    bullets = report["findings"][:4] or ["Aucun probleme memoire detecte."]
    entry_lines = [f"## {stamp} - {event}", ""]
    entry_lines.extend(f"- {bullet}" for bullet in bullets)
    entry_lines.extend(["", ""])
    entry = "\n".join(entry_lines)

    first_entry_match = re.search(r"(?m)^## ", existing)
    if first_entry_match:
        prefix = existing[:first_entry_match.start()].rstrip() + "\n\n"
        remainder = existing[first_entry_match.start():].lstrip()
        recent_learnings.write_text(prefix + entry + remainder, encoding="utf-8")
        return

    base = existing.rstrip()
    separator = "\n\n" if base else ""
    recent_learnings.write_text(base + separator + entry, encoding="utf-8")


def write_last_audit(memory_dir: Path, report: dict) -> None:
    (memory_dir / "last-audit.md").write_text(render_markdown(report), encoding="utf-8")


def append_event_log(memory_dir: Path, event: str, agent: str, payload: dict, report: dict) -> None:
    log_path = memory_dir / "hook-log.jsonl"
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": event,
        "agent": agent,
        "root": report["root"],
        "finding_count": len(report["findings"]),
        "payload_keys": sorted(payload.keys()),
    }

    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, sort_keys=True) + "\n")


def print_summary(event: str, report: dict) -> None:
    if event in {"PreToolUse", "PostToolUse"}:
        return

    summary = (
        f"memory-hook: event={event} root_claude_lines={report['files'].get('CLAUDE.md', 0)} "
        f"findings={len(report['findings'])}"
    )
    if report["findings"]:
        summary += " action=/memory-hygiene full"
    print(summary)


def main() -> int:
    args = parse_args()
    root = resolve_root(args.root)
    payload = read_stdin_payload()
    memory_dir = ensure_memory_files(root)
    report = audit_memory(root)

    append_event_log(memory_dir, args.event, args.agent, payload, report)

    if args.event == "PreCompact":
        append_checkpoint(memory_dir, args.event, report)

    if args.event in {"InstructionsLoaded", "Stop", "Setup", "PreCompact"}:
        write_last_audit(memory_dir, report)

    print_summary(args.event, report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
