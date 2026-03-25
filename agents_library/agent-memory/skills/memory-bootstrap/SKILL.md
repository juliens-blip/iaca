---
name: memory-bootstrap
description: Bootstrap a clean CLAUDE.md memory layout from day one. Use when initializing a repo, splitting memory by backend/frontend scope, or replacing a single bloated CLAUDE.md with layered files.
---

# Memory Bootstrap

Create a clean memory layout before the project accumulates noise.

## Objectives

- Start with a stable root `CLAUDE.md`.
- Create `QUICK_REF.md` for commands and runbooks.
- Create `.claude/rules/` for narrow rule sets.
- Create `.claude/memory/recent-learnings.md` for volatile notes.
- Create scoped `CLAUDE.md` files only where the directory boundary is real.

## When to Use

- new project setup
- monorepo or multi-surface repo
- migration from a single overloaded `CLAUDE.md`
- project template creation

## Workflow

1. Inspect the repo roots and real boundaries such as `backend/`, `frontend/`, `apps/*`, or `packages/*`.
2. Run the bootstrap script to scaffold the layered memory files.
3. Replace placeholders in templates with the actual stack, commands, and invariants.
4. Update `.gitignore` so shared `.claude/rules/` and `.claude/memory/recent-learnings.md` are tracked if needed.
5. Run the memory audit to confirm the layout is lean and complete.

## Commands

Scaffold the layout:

```bash
python3 agents_library/agent-memory/skills/memory-bootstrap/scripts/bootstrap_memory_layout.py --root . --project-name IACA --scopes backend frontend
```

Scaffold and update `.gitignore`:

```bash
python3 agents_library/agent-memory/skills/memory-bootstrap/scripts/bootstrap_memory_layout.py --root . --project-name IACA --scopes backend frontend --update-gitignore
```

## Resources

- `assets/claude-root-template.md`
- `assets/quick-ref-template.md`
- `assets/scoped-claude-template.md`
- `assets/recent-learnings-template.md`
- `assets/rule-typescript-template.md`
- `assets/rule-tests-template.md`
- `assets/rule-backend-template.md`
- `assets/gitignore-snippet.txt`
- `scripts/bootstrap_memory_layout.py`

## Rules

- Keep the templates concise; do not turn them into tutorials.
- Fill only repo-specific facts that are stable enough to deserve always-loaded context.
- If a section is mostly commands, move it to `QUICK_REF.md`.
- If a section is only relevant inside one subtree, move it into that subtree.
