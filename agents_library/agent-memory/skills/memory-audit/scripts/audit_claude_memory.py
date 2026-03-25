#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT_LINE_BUDGET = 200
CHILD_LINE_BUDGET = 120
RULE_FILES = ("typescript.md", "tests.md", "backend.md")
VOLATILE_PATTERNS = {
    "dated log markers": re.compile(r"\b20\d{2}-\d{2}-\d{2}\b|last updated", re.IGNORECASE),
    "task queue markers": re.compile(r"\btask queue\b|\bassigned to\b|\bpriority\b", re.IGNORECASE),
    "progress markers": re.compile(
        r"\bin[_ -]?progress\b|\bphase\s+\d+\b|\bstatus:\s*(pending|completed|in progress)\b",
        re.IGNORECASE,
    ),
    "log section markers": re.compile(r"\bcompletion log\b|\borchestration log\b|\blive log\b", re.IGNORECASE),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit project CLAUDE memory hygiene.")
    parser.add_argument("--root", default=".", help="Project root.")
    parser.add_argument(
        "--format",
        choices=("markdown", "json"),
        default="markdown",
        help="Output format.",
    )
    parser.add_argument("--write", default="", help="Optional output file.")
    parser.add_argument(
        "--fail-on-issues",
        action="store_true",
        help="Exit non-zero when findings are present.",
    )
    return parser.parse_args()


def read_text(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return ""
    return path.read_text(encoding="utf-8")


def count_lines(path: Path) -> int:
    text = read_text(path)
    if not text:
        return 0
    return len(text.splitlines())


def scoped_claude_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for candidate in sorted(root.glob("*/CLAUDE.md")):
        if not candidate.is_file():
            continue
        scope_dir = candidate.parent
        if (scope_dir / ".git").is_dir():
            continue
        if scope_dir.name.startswith("."):
            continue
        files.append(candidate)
    return files


def audit(root: Path) -> dict:
    findings: list[dict[str, str]] = []
    files: dict[str, dict[str, int | bool]] = {}

    root_claude = root / "CLAUDE.md"
    quick_ref = root / "QUICK_REF.md"
    root_text = read_text(root_claude)
    root_lines = count_lines(root_claude)

    files["CLAUDE.md"] = {"lines": root_lines, "exists": root_claude.exists()}
    files["QUICK_REF.md"] = {"lines": count_lines(quick_ref), "exists": quick_ref.exists()}

    if not root_claude.exists():
        findings.append({"severity": "high", "message": "Missing root CLAUDE.md."})
    else:
        if root_lines > ROOT_LINE_BUDGET:
            findings.append(
                {
                    "severity": "high",
                    "message": f"Root CLAUDE.md is {root_lines} lines; target is <= {ROOT_LINE_BUDGET}.",
                }
            )

        for label, pattern in VOLATILE_PATTERNS.items():
            if pattern.search(root_text):
                findings.append(
                    {
                        "severity": "medium",
                        "message": f"Root CLAUDE.md contains {label}.",
                    }
                )

        if root_text.count("```") > 6:
            findings.append(
                {
                    "severity": "medium",
                    "message": "Root CLAUDE.md contains many code blocks; move commands to QUICK_REF.md.",
                }
            )

    if not quick_ref.exists():
        findings.append({"severity": "medium", "message": "Missing QUICK_REF.md."})

    rules_dir = root / ".claude" / "rules"
    for rule_name in RULE_FILES:
        rule_path = rules_dir / rule_name
        files[str(rule_path.relative_to(root))] = {
            "lines": count_lines(rule_path),
            "exists": rule_path.exists(),
        }
        if not rule_path.exists():
            findings.append(
                {
                    "severity": "medium",
                    "message": f"Missing .claude/rules/{rule_name}.",
                }
            )

    recent_learnings = root / ".claude" / "memory" / "recent-learnings.md"
    files[str(recent_learnings.relative_to(root))] = {
        "lines": count_lines(recent_learnings),
        "exists": recent_learnings.exists(),
    }
    if not recent_learnings.exists():
        findings.append(
            {
                "severity": "medium",
                "message": "Missing .claude/memory/recent-learnings.md.",
            }
        )

    for scoped_file in scoped_claude_files(root):
        scoped_lines = count_lines(scoped_file)
        rel_path = str(scoped_file.relative_to(root))
        files[rel_path] = {"lines": scoped_lines, "exists": True}
        if scoped_lines > CHILD_LINE_BUDGET:
            findings.append(
                {
                    "severity": "low",
                    "message": f"{rel_path} is {scoped_lines} lines; consider splitting if it keeps growing.",
                }
            )

    for scope_name in ("backend", "frontend"):
        scope_dir = root / scope_name
        scope_claude = scope_dir / "CLAUDE.md"
        if scope_dir.is_dir() and not scope_claude.exists():
            findings.append(
                {
                    "severity": "medium",
                    "message": f"Directory {scope_name}/ exists but {scope_name}/CLAUDE.md is missing.",
                }
            )

    gitignore = root / ".gitignore"
    gitignore_text = read_text(gitignore)
    if ".claude/" in gitignore_text:
        missing_exception = (
            "!.claude/rules/" not in gitignore_text
            or "!.claude/rules/*.md" not in gitignore_text
            or "!.claude/memory/recent-learnings.md" not in gitignore_text
        )
        if missing_exception:
            findings.append(
                {
                    "severity": "medium",
                    "message": ".gitignore ignores .claude/ without exceptions for shared rules or recent-learnings.",
                }
            )

    suggestions = []
    if root_lines > ROOT_LINE_BUDGET:
        suggestions.append("Move commands to QUICK_REF.md and volatile notes to .claude/memory/recent-learnings.md.")
    if not quick_ref.exists():
        suggestions.append("Create QUICK_REF.md for setup, run, validation, env vars, and endpoint cheatsheets.")
    if any("contains" in item["message"] for item in findings):
        suggestions.append("Strip dated logs, status tables, and sprint notes from root CLAUDE.md.")
    if any("missing" in item["message"].lower() for item in findings):
        suggestions.append("Fill the missing memory layers before adding more content to root CLAUDE.md.")

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "root": str(root),
        "files": files,
        "findings": findings,
        "suggestions": suggestions,
    }


def render_markdown(report: dict) -> str:
    lines = [
        "# Memory Audit Report",
        "",
        f"- Timestamp: {report['timestamp']}",
        f"- Root: {report['root']}",
        f"- Findings: {len(report['findings'])}",
        "",
        "## Files",
        "",
    ]

    for path, info in sorted(report["files"].items()):
        status = "present" if info["exists"] else "missing"
        lines.append(f"- `{path}`: {info['lines']} lines ({status})")

    lines.extend(["", "## Findings", ""])
    if report["findings"]:
        for finding in report["findings"]:
            lines.append(f"- [{finding['severity']}] {finding['message']}")
    else:
        lines.append("- No issues detected.")

    lines.extend(["", "## Suggestions", ""])
    if report["suggestions"]:
        for suggestion in report["suggestions"]:
            lines.append(f"- {suggestion}")
    else:
        lines.append("- Keep the current split and re-run the audit after major memory edits.")

    lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    root = Path(args.root).resolve()
    report = audit(root)

    output = json.dumps(report, indent=2, sort_keys=True) if args.format == "json" else render_markdown(report)

    if args.write:
        output_path = Path(args.write).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(output + ("" if output.endswith("\n") else "\n"), encoding="utf-8")
    else:
        sys.stdout.write(output if output.endswith("\n") else output + "\n")

    if args.fail_on_issues and report["findings"]:
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
