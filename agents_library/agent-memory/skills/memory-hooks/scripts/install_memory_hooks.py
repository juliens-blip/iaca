#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


HOOKS_FILE = Path(__file__).resolve().parents[3] / "hooks" / "hooks.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Merge memory hooks into .claude/settings.json.")
    parser.add_argument("--root", default=".", help="Project root.")
    parser.add_argument(
        "--settings-path",
        default="",
        help="Override settings file path. Defaults to <root>/.claude/settings.json.",
    )
    parser.add_argument("--write", action="store_true", help="Write the merged settings to disk.")
    return parser.parse_args()


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def merge_settings(current: dict, addition: dict) -> dict:
    merged = dict(current)
    merged_hooks = dict(merged.get("hooks", {}))

    for event_name, new_entries in addition.get("hooks", {}).items():
        existing_entries = list(merged_hooks.get(event_name, []))
        for new_entry in new_entries:
            if new_entry not in existing_entries:
                existing_entries.append(new_entry)
        merged_hooks[event_name] = existing_entries

    merged["hooks"] = merged_hooks
    return merged


def main() -> int:
    args = parse_args()
    root = Path(args.root).resolve()
    settings_path = Path(args.settings_path).resolve() if args.settings_path else root / ".claude" / "settings.json"

    current_settings = load_json(settings_path)
    memory_hooks = load_json(HOOKS_FILE)
    merged_settings = merge_settings(current_settings, memory_hooks)
    rendered = json.dumps(merged_settings, indent=2, sort_keys=True) + "\n"

    if args.write:
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        settings_path.write_text(rendered, encoding="utf-8")
        print(f"wrote {settings_path}")
    else:
        sys.stdout.write(rendered)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
