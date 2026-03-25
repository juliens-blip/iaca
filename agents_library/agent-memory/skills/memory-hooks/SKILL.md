---
name: memory-hooks
description: Install and operate hook-driven memory hygiene for Claude Code projects. Use when you want automatic audits, compaction checkpoints, and lightweight memory guard rails without bloating CLAUDE.md.
---

# Memory Hooks

Use hooks to keep memory clean between sessions and compactions.

## Goals

- create missing memory folders on setup
- detect bloated or mis-split memory files when instructions load
- save a compact checkpoint before compaction
- write a fresh audit report at the end of a session

## Workflow

1. Inspect `.claude/settings.json`.
2. Merge the memory hook pack into project settings.
3. Dry-run the hook script directly against the repo.
4. Confirm the expected output files land in `.claude/memory/`.
5. Keep hooks small and quiet; they should support memory hygiene, not replace it.

## Commands

Preview merged settings:

```bash
python3 agents_library/agent-memory/skills/memory-hooks/scripts/install_memory_hooks.py --root .
```

Write merged settings:

```bash
python3 agents_library/agent-memory/skills/memory-hooks/scripts/install_memory_hooks.py --root . --write
```

Run a hook manually:

```bash
python3 agents_library/agent-memory/hooks/scripts/memory_hook.py --root . --event Stop
```

## Resources

- `../../../agent-memory/hooks/hooks.json`
- `../../../agent-memory/hooks/scripts/memory_hook.py`
- `references/hook-events.md`
- `scripts/install_memory_hooks.py`

## Rules

- Never let hooks auto-rewrite root `CLAUDE.md`.
- Hooks may create audits and checkpoints, but humans or dedicated agents should apply structural edits.
- Keep hook output concise; noise is also memory debt.
