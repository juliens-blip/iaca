# Project Memory - <PROJECT_NAME>

## Global State
- **Main goal:** <describe the goal>
- **Progress:** 0%
- **Phase:** <current phase name>
- **Orchestrator:** <LLM name> (window <N>)
- **Session started:** <timestamp>
- **Last update:** <timestamp>

## Architecture LLMs Active

| Window | LLM | Status | Current Task |
|--------|-----|--------|--------------|
| w0 | bash | READY | - |
| w1 | <LLM name> | STARTING | - |

## Task Assignment Queue

| ID | Task | Files | Acceptance Criteria | Agent | Assigned To | Priority | Status | Created |
|----|------|-------|---------------------|-------|-------------|----------|--------|---------|
| T-001 | <precise task description> | <file paths> | <test command + expected output> | <@agents_library/agent-name> | <LLM (wN)> | HIGH/MED/LOW | PENDING | <date> |

## Task Completion Log

| Timestamp | Task ID | LLM | Result | Files Touched | Notes |
|-----------|---------|-----|--------|---------------|-------|

## Resource Locks

| Resource | Claimed By | Status | Started |
|----------|------------|--------|---------|
| <e.g. ollama pull mistral> | w3 | IN_PROGRESS | <timestamp> |

## Inter-LLM Messages

| From | To | Message | Time |
|------|----|---------|------|

## Remaining / Blocked Tasks
- <task or blocker with reason>

## Session Recovery Log

| Timestamp | Event | Action Taken |
|-----------|-------|-------------|
| <timestamp> | Session start | Bootstrap completed, N workers ready |
| <timestamp> | Context compaction | Re-read CLAUDE.md, redistributed N tasks |
