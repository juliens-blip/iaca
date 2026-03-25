# Hook Events

## Recommended Events

### `Setup`

Use this to create:

- `.claude/memory/`
- `.claude/memory/recent-learnings.md`
- `.claude/memory/hook-log.jsonl`

### `InstructionsLoaded`

Use this to catch problems early:

- root `CLAUDE.md` too large
- volatile markers in root memory
- missing `QUICK_REF.md`
- missing scoped `CLAUDE.md` files

### `PreCompact`

Use this for a short checkpoint before Claude compacts:

- current root line count
- top findings
- one-line reminder of what should move out of root memory

### `Stop`

Use this to write:

- `.claude/memory/last-audit.md`
- a short event log entry

## Local Memory vs External Memory

Recommended split:

- Root `CLAUDE.md`: stable repo facts only
- `.claude/memory/recent-learnings.md`: short local volatile notes
- External memory system such as `claude-mem`: long-term searchable session memory
- Docs on demand such as `Context7`: framework docs that should not live in project memory

This keeps always-loaded memory lean while preserving deeper context elsewhere.
