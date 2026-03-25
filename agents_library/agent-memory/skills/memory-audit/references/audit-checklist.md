# Audit Checklist

## Stable vs Volatile

Use this split before editing:

| Class | Keep Here | Examples |
|------|-----------|----------|
| Stable | `CLAUDE.md` root | product purpose, repo map, invariants |
| Reference | `QUICK_REF.md` | setup, run, validate, endpoints, env vars |
| Narrow rules | `.claude/rules/*.md` | TypeScript, tests, backend policy |
| Scoped | `<scope>/CLAUDE.md` | backend-only or frontend-only rules |
| Volatile | `.claude/memory/recent-learnings.md` | recent incidents, short workarounds, compaction notes |
| External | docs on demand | framework docs, library APIs, long reports |

## Smells

- Root `CLAUDE.md` contains timestamps or dated sections
- Task queues or completion logs in root memory
- Long shell command blocks in root memory
- Repeated instructions copied across root and scoped files
- `.claude/` fully ignored even though shared rules are meant to ship
- Missing `QUICK_REF.md` while root memory contains mostly commands
- Scoped codebase exists but all rules still live in root

## What Good Looks Like

- Root memory is under 200 lines in most repos
- Commands live in `QUICK_REF.md`
- Scoped files exist only for real subtree boundaries
- Volatile notes are short, dated, and purged regularly
- A script can audit memory hygiene in one command
