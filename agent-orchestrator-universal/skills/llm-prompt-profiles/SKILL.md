---
name: llm-prompt-profiles
description: LLM-specific prompt submission profiles for tmux orchestration. Use when sending prompts to workers — handles input protocol differences between Claude Code, Codex, AMP, and raw bash terminals.
---

# LLM Prompt Profiles (tmux)

## Arguments
- session: tmux session name.
- window: tmux window index (numeric).
- llm_type: one of `claude-code`, `codex`, `amp`, `bash`.
- message: prompt to send (natural language for LLMs, commands for bash).

## Objectives
- Send prompts adapted to each LLM's input protocol.
- Guarantee submission (not stuck in input buffer).
- Detect activity using LLM-specific patterns.
- Provide a unified `send-to-llm.sh` script that auto-detects LLM type.

## LLM Profiles

### claude-code (Claude Code CLI — Haiku, Sonnet, Opus)
- **Prompt char**: `❯`
- **Input**: natural language, single Enter submits
- **Activity patterns**: `Working`, `Thinking`, `Explored`, `Read`, `Baked`, `Hullaballooing`, `Simmering`
- **Idle patterns**: `❯` alone on last line, `bypass permissions`
- **Submit**: `Enter` (once is usually enough)
- **Cancel**: `Escape` or `C-c`
- **Gotcha**: After compaction (`Compacting conversation…`), prompt reappears — wait 3s then check

### codex (OpenAI Codex CLI)
- **Prompt char**: `›` (right-pointing single bracket)
- **Input**: natural language only (NOT raw bash commands)
- **Activity patterns**: `Working`, `Ran `, `• `, `Waiting for background`
- **Idle patterns**: `›` alone, `gpt-5.4`, `% left`
- **Submit**: needs **double Enter** — first Enter pastes, second submits
- **Cancel**: `Escape`
- **Gotcha**: Raw bash commands appear in buffer but Codex treats them as text. Always phrase as natural language instructions. Multi-line paste swallows the first Enter.
- **Critical**: After `tmux send-keys ... Enter`, ALWAYS `sleep 2 && tmux send-keys ... Enter` again

### amp (Anthropic AMP CLI)
- **Prompt char**: `❯`
- **Input**: natural language, single Enter submits
- **Activity patterns**: `Discombobulating`, `Simmering`, `Running`, `Hullaballooing`
- **Idle patterns**: `❯` alone, `bypass permissions`, `esc to interrupt`
- **Submit**: `Enter` (single, like Claude Code)
- **Cancel**: `Escape`
- **Gotcha**: Shares `❯` prompt with Claude Code — differentiate via window name or `Discombobulating` pattern

### bash (raw terminal)
- **Prompt char**: `$` or custom PS1
- **Input**: shell commands only
- **Activity patterns**: no cursor returned (command running)
- **Idle patterns**: `$` prompt visible
- **Submit**: single `Enter`
- **Cancel**: `C-c`
- **Gotcha**: Not an LLM — do not send natural language prompts

## Steps

1) Identify the LLM type from the window name or capture output.
2) Format the prompt according to the profile (natural language for LLMs, commands for bash).
3) Send using `scripts/send-to-llm.sh` which handles per-LLM submission protocol.
4) Verify activity using LLM-specific patterns within 5s.
5) If no activity detected, apply profile-specific recovery (double-Enter for Codex, C-c + resend for others).

## Auto-Detection

Use `scripts/detect-llm-type.sh` to identify the LLM from pane content:

```bash
llm_type=$(bash scripts/detect-llm-type.sh $SESSION $WINDOW)
# Returns: claude-code | codex | amp | bash | unknown
```

## Examples

Send to Claude Code worker:
```bash
bash scripts/send-to-llm.sh $SESSION 2 claude-code "Génère les fiches pour Droit public --limit 5"
```

Send to Codex worker (double-Enter automatic):
```bash
bash scripts/send-to-llm.sh $SESSION 0 codex "Run dedup_documents.py then git push"
```

Send to AMP worker:
```bash
bash scripts/send-to-llm.sh $SESSION 4 amp "Audit flashcard quality for L2-S3"
```

Auto-detect and send:
```bash
bash scripts/send-to-llm.sh $SESSION 3 auto "Generate missing flashcards"
```

## Resources
- `scripts/send-to-llm.sh`: unified send with per-LLM protocol handling.
- `scripts/detect-llm-type.sh`: auto-detect LLM type from pane content.
- `references/llm-patterns.md`: full pattern reference table.
- `assets/prompt-guidelines.md`: how to write effective short prompts per LLM.

