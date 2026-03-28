# LLM Pattern Reference

## Activity Patterns (worker is processing)

| LLM | Patterns |
|-----|----------|
| Claude Code | `Working`, `Thinking`, `Explored`, `Read`, `Baked for Xm`, `Hullaballooing`, `Simmering`, `ctrl+o to expand` |
| Codex | `• Working (Xs`, `• Ran `, `• Explored`, `Waiting for background`, `Running tools` |
| AMP | `Discombobulating`, `Simmering`, `Hullaballooing`, `Running`, `ctrl+b ctrl+b` |
| Bash | No prompt returned (command still running) |

## Idle Patterns (worker is ready for input)

| LLM | Patterns |
|-----|----------|
| Claude Code | `❯` alone, `bypass permissions on`, `0% until auto-compact` |
| Codex | `›` alone, `gpt-5.4`, `% left`, `? for shortcuts` |
| AMP | `❯` alone, `bypass permissions on`, `esc to interrupt` absent |
| Bash | `$`, `julien@`, `root@` |

## Completion Patterns (task just finished)

| LLM | Patterns |
|-----|----------|
| Claude Code | `Baked for Xm Ys`, followed by `❯` |
| Codex | `✓` prefix, back to `›` |
| AMP | Task summary shown, back to `❯` |

## Error Patterns

| LLM | Patterns |
|-----|----------|
| Claude Code | `Error`, `API error`, `rate limit`, `context limit` |
| Codex | `Error`, `esc to cancel`, red text |
| AMP | `Error`, `failed`, red output |

## Prompt Input Rules

| LLM | Input Type | Submit | Cancel | Clear Buffer |
|-----|-----------|--------|--------|-------------|
| Claude Code | Natural language | Enter (1x) | Escape / C-c | C-u |
| Codex | Natural language only | Enter (2x, with 2s delay) | Escape | C-c then C-u |
| AMP | Natural language | Enter (1x) + safety Enter | Escape | C-u |
| Bash | Shell commands | Enter (1x) | C-c | C-u |

## Critical Rules

1. **Never send raw bash commands to Codex** — always phrase as natural language
2. **Codex always needs double-Enter** — first Enter puts text in buffer, second submits
3. **Claude Code after compaction** — wait 3s, the `❯` prompt reappears
4. **AMP shares `❯` with Claude Code** — differentiate by window name or `Discombobulating` pattern
5. **Keep prompts short** (<100 words) — long prompts increase chance of paste issues
6. **Use single quotes** for prompts containing `$`, `!`, `\` to avoid shell expansion
