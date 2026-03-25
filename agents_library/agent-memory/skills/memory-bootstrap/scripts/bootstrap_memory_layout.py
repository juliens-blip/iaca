#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_SCOPES = ("backend", "frontend")
ASSET_DIR = Path(__file__).resolve().parent.parent / "assets"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scaffold a layered Claude memory layout.")
    parser.add_argument("--root", default=".", help="Project root.")
    parser.add_argument("--project-name", default="", help="Project display name.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing files.")
    parser.add_argument(
        "--scopes",
        nargs="*",
        default=list(DEFAULT_SCOPES),
        help="Scoped directories that should get a CLAUDE.md if present.",
    )
    parser.add_argument(
        "--update-gitignore",
        action="store_true",
        help="Append the recommended .claude tracking snippet to .gitignore when missing.",
    )
    return parser.parse_args()


def read_asset(name: str) -> str:
    return (ASSET_DIR / name).read_text(encoding="utf-8")


def render(template: str, replacements: dict[str, str]) -> str:
    rendered = template
    for key, value in replacements.items():
        rendered = rendered.replace(f"{{{{{key}}}}}", value)
    return rendered


def write_file(path: Path, content: str, force: bool) -> str:
    if path.exists() and not force:
        return f"skip  {path}"

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")
    return f"write {path}"


def maybe_append_gitignore(root: Path, force: bool) -> str:
    gitignore_path = root / ".gitignore"
    snippet = read_asset("gitignore-snippet.txt").strip()

    if gitignore_path.exists():
        current = gitignore_path.read_text(encoding="utf-8")
        if snippet in current:
            return f"skip  {gitignore_path} (snippet present)"
        updated = current.rstrip() + "\n\n" + snippet + "\n"
        gitignore_path.write_text(updated, encoding="utf-8")
        return f"patch {gitignore_path}"

    gitignore_path.write_text(snippet + "\n", encoding="utf-8")
    return f"write {gitignore_path}"


def main() -> int:
    args = parse_args()
    root = Path(args.root).resolve()
    project_name = args.project_name or root.name
    date_stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    replacements = {
        "PROJECT_NAME": project_name,
        "ROOT_CLAUDE_TARGET": "150-250",
        "PROJECT_PURPOSE": "Replace with the actual product purpose.",
        "STACK_SUMMARY": "Replace with the actual repo stack.",
        "PRIMARY_DIRECTORIES": "backend/, frontend/, scripts/, docs/, data/, .claude/",
        "BACKEND_STACK": "Replace with backend stack.",
        "FRONTEND_STACK": "Replace with frontend stack.",
        "INFRA_STACK": "Replace with infra or tooling stack.",
        "SETUP_COMMANDS": "cp .env.example .env",
        "RUN_COMMANDS": "Replace with run commands.",
        "VALIDATION_COMMANDS": "Replace with validation commands.",
        "ENV_VAR_1": "DATABASE_URL",
        "ENV_VAR_2": "API_AUTH_TOKEN",
        "DATE_STAMP": date_stamp,
        "SCOPE_COMMANDS": "Replace with scope-specific commands.",
    }

    operations: list[str] = []
    operations.append(
        write_file(
            root / "CLAUDE.md",
            render(read_asset("claude-root-template.md"), replacements),
            args.force,
        )
    )
    operations.append(
        write_file(
            root / "QUICK_REF.md",
            render(read_asset("quick-ref-template.md"), replacements),
            args.force,
        )
    )
    operations.append(
        write_file(
            root / ".claude" / "memory" / "recent-learnings.md",
            render(read_asset("recent-learnings-template.md"), replacements),
            args.force,
        )
    )
    operations.append(
        write_file(
            root / ".claude" / "rules" / "typescript.md",
            read_asset("rule-typescript-template.md"),
            args.force,
        )
    )
    operations.append(
        write_file(
            root / ".claude" / "rules" / "tests.md",
            read_asset("rule-tests-template.md"),
            args.force,
        )
    )
    operations.append(
        write_file(
            root / ".claude" / "rules" / "backend.md",
            read_asset("rule-backend-template.md"),
            args.force,
        )
    )

    scoped_template = read_asset("scoped-claude-template.md")
    for scope_name in args.scopes:
        scope_dir = root / scope_name
        if not scope_dir.is_dir():
            operations.append(f"skip  {scope_dir} (missing directory)")
            continue

        scope_replacements = {
            **replacements,
            "SCOPE_NAME": scope_name,
        }
        operations.append(
            write_file(
                scope_dir / "CLAUDE.md",
                render(scoped_template, scope_replacements),
                args.force,
            )
        )

    if args.update_gitignore:
        operations.append(maybe_append_gitignore(root, args.force))

    for operation in operations:
        print(operation)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
