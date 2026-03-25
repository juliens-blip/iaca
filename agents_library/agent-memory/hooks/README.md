# Memory Hooks

This hook pack keeps Claude memory clean without turning root memory into a log sink.

## Hook Strategy

- `Setup`: create missing memory directories and seed lightweight files
- `InstructionsLoaded`: detect oversized or badly split memory early
- `PreCompact`: capture a short checkpoint before compaction
- `Stop`: write a fresh audit report for the repo

## Files Touched

- `.claude/memory/recent-learnings.md`
- `.claude/memory/last-audit.md`
- `.claude/memory/hook-log.jsonl`

## Installation

Use:

```bash
python3 agents_library/agent-memory/skills/memory-hooks/scripts/install_memory_hooks.py --root . --write
```

Or merge [hooks.json](/home/julien/Documents/IACA/agents_library/agent-memory/hooks/hooks.json) into `.claude/settings.json` manually.

## Design Rules

- Do not write large transcripts from hooks.
- Do not mutate root `CLAUDE.md` automatically.
- Prefer short reports and append-only learnings.
- Treat hooks as hygiene helpers, not as a second orchestration layer.
