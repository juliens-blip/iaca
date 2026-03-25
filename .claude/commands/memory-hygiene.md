---
description: Audit, compact, bootstrap, or wire Claude project memory through memory-agent
model: haiku
---

# Memory Hygiene Command

Use `memory-agent` as the entry point for Claude memory work in this repository.

## Supported Modes

- `/memory-hygiene audit`
- `/memory-hygiene bootstrap`
- `/memory-hygiene hooks`
- `/memory-hygiene full`

If no mode is supplied, default to `full`.

## Workflow

1. Inspect the current memory files:
   - `CLAUDE.md`
   - `QUICK_REF.md`
   - `.claude/settings.json`
   - `.claude/rules/*.md`
   - `.claude/memory/recent-learnings.md`
   - scoped `CLAUDE.md` files such as `backend/CLAUDE.md` and `frontend/CLAUDE.md`
2. Invoke the `memory-agent` agent with the requested mode.
3. Require the agent to use the bundled `memory-bootstrap`, `memory-audit`, and `memory-hooks` skills when relevant.
4. Return:
   - files changed
   - what moved where
   - verification commands run
   - remaining memory debt, if any

## Mode Semantics

### `audit`

- Run the deterministic memory audit.
- Do not rewrite files unless the user explicitly asks for edits in addition to the audit.

### `bootstrap`

- Create or refresh the layered memory structure.
- Focus on `CLAUDE.md`, `QUICK_REF.md`, `.claude/rules/`, `.claude/memory/`, and scoped memories.

### `hooks`

- Review or install the memory hook pack.
- Explain what each active hook writes and which artifacts remain local-only.

### `full`

- Audit current memory.
- Compact or split memory where needed.
- Refresh commands and scoped memories if stale.
- Validate hooks and `.gitignore`.

## Critical Requirements

- Use the `memory-agent` agent, not an ad-hoc freeform rewrite.
- Keep root `CLAUDE.md` stable and short.
- Keep commands in `QUICK_REF.md`.
- Keep volatile notes in `.claude/memory/recent-learnings.md`.
- Do not silently install hooks when the user asked only for `audit`.
