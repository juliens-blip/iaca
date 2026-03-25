# Concrete Examples

## Example 1: Clean Memory Tree

```text
project/
├── CLAUDE.md
├── QUICK_REF.md
├── .claude/
│   ├── rules/
│   │   ├── typescript.md
│   │   ├── tests.md
│   │   └── backend.md
│   └── memory/
│       └── recent-learnings.md
├── backend/
│   └── CLAUDE.md
└── frontend/
    └── CLAUDE.md
```

## Example 2: Bad Root Memory

~~~markdown
# CLAUDE.md

Last updated: 2026-03-17
Phase 20 in progress

## Task Queue
- T-001 ...
- T-002 ...

## Commands
```bash
npm run dev
uvicorn app.main:app --reload
python scripts/one_off_fix.py
```

## Completion Log
- 2026-03-17 ...
~~~

Why it is bad:

- volatile status mixed with stable memory
- command blocks bloat always-loaded context
- task history belongs elsewhere

## Example 3: Better Split

```markdown
# CLAUDE.md

## Memory Rules
- Keep this file stable and short
- Commands live in QUICK_REF.md
- Volatile learnings live in .claude/memory/recent-learnings.md

## Product
- Backend: FastAPI
- Frontend: Next.js

## Stable Invariants
- Frontend calls /api/*
- Auth is bearer-based
```

~~~markdown
# QUICK REF

## Run
```bash
cd frontend && npm run dev
cd backend && uvicorn app.main:app --reload
```
~~~

```markdown
# Recent Learnings

## 2026-03-17
- Double-submit tmux prompts when interactive paste is flaky
```

## Example 4: `.gitignore` Fix

```gitignore
.claude/*
!.claude/rules/
!.claude/rules/*.md
!.claude/memory/
!.claude/memory/recent-learnings.md
.claude/settings.local.json
```

## Example 5: Hook Snippet

```json
{
  "hooks": {
    "PreCompact": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ${CLAUDE_PROJECT_DIR}/agents_library/agent-memory/hooks/scripts/memory_hook.py --event PreCompact",
            "timeout": 15000
          }
        ]
      }
    ]
  }
}
```
