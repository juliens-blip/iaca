---
name: task-distribution-memory-sync
description: Distribute tasks with IDs across LLM workers and keep progress synced in CLAUDE.md. Use when orchestrating multi-LLM work, polling status, and redistributing tasks.
---

# Task Distribution and Memory Sync

## Arguments
- claude_md_path: path to shared memory file (default CLAUDE.md).
- session: tmux session name.
- window_map: map of workers to window numbers.
- poll_interval_sec: polling interval (default 60-90).

## Objectives
- Create task IDs and a single source of truth in CLAUDE.md.
- Decompose into **short, precise, atomic tasks** (15-30 min max).
- Distribute one task per prompt with clear acceptance criteria.
- Poll CLAUDE.md and reassign work immediately when tasks finish.
- Keep a completion log with files touched, test results, and notes.
- Require a relevant agents_library agent for each task (or explicitly note none).

## Task Atomicity Rules

Every task MUST be:

1. **One objective** — a single function, endpoint, fix, or test. Not "fix the backend."
2. **Max 30 minutes** — if it would take longer, split it into sub-tasks.
3. **Precise scope** — name the exact files, functions, endpoints, or components.
4. **Testable** — include an acceptance criterion: a command to run and the expected output.
5. **Self-contained** — include all context the worker needs. The worker should NOT need to ask questions.

### Splitting large tasks

If a user request is large (e.g., "implement authentication"), decompose it:

| Sub-task | Example |
|----------|---------|
| Schema/model | "Add User model in models/user.py with fields: id, email, password_hash, created_at" |
| Route | "Create POST /api/auth/register in routers/auth.py — validate email, hash password, insert user" |
| Middleware | "Add JWT auth middleware in middleware/auth.py — verify Authorization header, inject user in request.state" |
| Frontend page | "Create app/login/page.tsx — form with email/password, POST to /api/auth/login, store token in localStorage" |
| Integration test | "Test full flow: register user, login, access protected endpoint — all return 200" |

## Steps

1) Decompose the request into atomic tasks and assign IDs (T-001, T-002, ...).
2) For each task, define: What, Files, Acceptance criteria, Agent, Time budget.
3) Select the most relevant agent from `agents_library` for each task.
   - If none fits, record `Agent: none` and proceed.
4) Write tasks into the Task Assignment Queue in CLAUDE.md (include ALL columns).
5) Send prompts with the full task template (see `assets/task-prompt-template.md`).
   - Prefer `scripts/send-verified.sh` to send + verify.
   - If sending manually, always run `scripts/verify-submit.sh` right after.
   - **Double-Enter** for multi-line prompts to interactive CLI workers.
6) Poll CLAUDE.md and redistribute as soon as workers finish.
7) Mark blocked tasks and reassign or unblock.
8) After feature tasks, spawn test tasks and run Ralph cycles.

## Resource Coordination

Before assigning a task that uses a shared resource (download, install, DB migration):

1. Check CLAUDE.md Resource Locks section.
2. If already claimed, do NOT assign a duplicate task.
3. If not claimed, add a lock entry before distributing.
4. The assigned worker must release the lock on completion.

## Monitoring Long Operations

For tasks involving downloads, builds, or installs > 1 minute:

1. Poll every 2 minutes: check the process is still running and making progress.
2. Log progress in CLAUDE.md (e.g., "phi3:mini download 58% at 10:15").
3. If stalled for > 5 minutes, kill and retry once. If still stalled, mark BLOCKED.

## Post-Compaction Recovery

After any context compaction:

1. Re-read CLAUDE.md (this is step 1, always).
2. Identify tasks that are IN_PROGRESS but whose workers are idle → re-send.
3. Identify PENDING tasks → distribute to idle workers.
4. Do NOT re-analyze completed tasks. Trust CLAUDE.md.
5. Total recovery time: < 30 seconds.

## Common Failure: Prompt Not Submitted
- If a prompt is visible in the pane but no activity starts, it is **not submitted**.
- Run `scripts/verify-submit.sh` (or `scripts/send-verified.sh`).
- If still idle, send `C-c`, then re-send the full prompt.

## Examples

Task entry in CLAUDE.md:

```markdown
| T-004 | Fix /api/leads/sync 500 error — add missing LeadSync schema | routers/leads.py, schemas/lead.py | POST /api/leads/sync returns 200 | @agents_library/backend-developer.md | AMP (w4) | HIGH | IN_PROGRESS | 2026-02-02 |
```

Prompt sent to worker (using the template from `assets/task-prompt-template.md`):

```
Task T-004: Fix /api/leads/sync 500 error — add missing LeadSync schema

What: Create LeadSync Pydantic schema in schemas/lead.py, then update routers/leads.py to use it.
Files: backend/app/schemas/lead.py, backend/app/routers/leads.py
Acceptance: POST /api/leads/sync with valid JSON returns HTTP 200
Time budget: 20 min

Load agent: @agents_library/backend-developer.md

When done:
1) Update CLAUDE.md Task Assignment Queue: T-004 -> COMPLETED
2) Add a Task Completion Log entry with timestamp, files touched, test result, notes
```

## Resources
- `assets/claude-md-template.md`: minimal CLAUDE.md structure (with Resource Locks and Recovery Log).
- `assets/task-prompt-template.md`: consistent prompt format with acceptance criteria.
- `scripts/poll-claude-md.sh`: poll for task completion.
- `scripts/verify-submit.sh`: verify prompt submission and retry Enter.
- `references/status-rules.md`: status definitions and blocking rules.
