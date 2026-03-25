---
name: memory-audit
description: Audit and compact project memory without losing useful context. Use when CLAUDE.md is bloated, when a repo accumulates transient notes, or when you want a report showing what belongs in root memory versus scoped or volatile files.
---

# Memory Audit

Audit the current memory layout, identify bloat, and produce a precise split plan.

## Objectives

- measure the current memory footprint
- find volatile content in stable memory files
- detect missing layers such as `QUICK_REF.md` or scoped `CLAUDE.md`
- catch `.gitignore` mistakes around `.claude/`
- produce concrete next actions, not vague advice

## Workflow

1. Run the audit script against the repo root.
2. Review findings by severity: oversized files, volatile markers, missing layers, tracking issues.
3. Move content by class:
   - stable -> root or scoped `CLAUDE.md`
   - command-heavy -> `QUICK_REF.md`
   - volatile -> `.claude/memory/recent-learnings.md`
   - external docs -> on-demand sources
4. Re-run the audit until the root memory is lean.
5. If you want stronger rules, review recent project conversation history and add only recurring patterns.

## Commands

Markdown report:

```bash
python3 agents_library/agent-memory/skills/memory-audit/scripts/audit_claude_memory.py --root .
```

Write report to disk:

```bash
python3 agents_library/agent-memory/skills/memory-audit/scripts/audit_claude_memory.py --root . --write .claude/memory/manual-audit.md
```

Fail CI or a local check when memory hygiene breaks:

```bash
python3 agents_library/agent-memory/skills/memory-audit/scripts/audit_claude_memory.py --root . --fail-on-issues
```

## Conversation Review Pattern

For recurring improvements, inspect recent Claude Code conversation history from `~/.claude/projects/` and compare what happened to what the current memory files said.

Use this only to strengthen recurring rules. Do not paste entire histories into memory files.

## Resources

- `scripts/audit_claude_memory.py`
- `references/audit-checklist.md`
- `references/concrete-examples.md`

## Rules

- Treat root memory as production configuration, not a notebook.
- Remove stale instructions instead of endlessly appending.
- Prefer one strong rule over five weak paraphrases.
