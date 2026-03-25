# {{PROJECT_NAME}}

Root project memory. Keep this file stable, short, and shared across the repo.

## Memory Rules

- Keep this file under {{ROOT_CLAUDE_TARGET}} lines.
- No dated logs, task queues, or sprint history here.
- Commands go in `QUICK_REF.md`.
- Volatile notes go in `.claude/memory/recent-learnings.md`.
- Scope-specific rules go in `.claude/rules/*.md` or scoped `CLAUDE.md` files.

## Product

- Purpose: {{PROJECT_PURPOSE}}
- Main stack: {{STACK_SUMMARY}}
- Primary directories: {{PRIMARY_DIRECTORIES}}

## Stable Invariants

- Replace this section with real repo-wide invariants only.
- Example: API auth is bearer-based.
- Example: frontend talks to backend through `/api/*`.
- Example: schema changes must update model, route, consumer, and docs.

## Navigation

- Commands: `QUICK_REF.md`
- Volatile memory: `.claude/memory/recent-learnings.md`
- Narrow rules: `.claude/rules/`
- Scoped memories: add `<scope>/CLAUDE.md` only for real boundaries

## Working Rules

- Prefer targeted changes over broad rewrites.
- Keep instructions factual and durable.
- Delete or move stale memory instead of stacking new notes on top.
