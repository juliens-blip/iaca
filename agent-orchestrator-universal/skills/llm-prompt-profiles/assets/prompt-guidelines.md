# Prompt Guidelines per LLM

## General Rules (all LLMs)

- **Keep prompts under 80 words** — long prompts break paste submission
- **One task per prompt** — never batch multiple tasks
- **No context reload** — don't re-explain the project, the LLM has its context
- **Be direct** — start with the action verb, skip preamble

## Claude Code (Haiku / Sonnet / Opus)

Good:
```
Génère les fiches pour les 2 docs Droit public restants: backend/.venv/bin/python3 scripts/reextract_and_generate.py --matiere 'Droit public' --limit 2 --skip-extract --provider gemini
```

Bad:
```
Salut, peux-tu s'il te plaît regarder dans la base de données combien de documents n'ont pas encore de fiche et ensuite lancer le script de génération avec le bon provider pour créer les fiches manquantes en vérifiant bien que tout fonctionne correctement...
```

Tips:
- Can include exact bash commands — Claude Code will run them
- Can reference agent library: `Load @agents_library/backend-architect.md`
- Responds well to task IDs: `Task T-045:`

## Codex

Good:
```
Run dedup_documents.py then git push the results
```

Bad:
```
backend/.venv/bin/python3 scripts/dedup_documents.py --apply 2>&1 | tail -10 && git add -A && git commit -m "dedup" && git push
```

Tips:
- **Natural language ONLY** — raw commands get pasted as text, not executed
- Keep it simple: Codex interprets intent, not syntax
- Don't specify exact file paths unless necessary — Codex finds them
- Avoid special chars (`|`, `&&`, `2>&1`) in prompts

## AMP

Good:
```
Audit flashcard quality for L2-S3 documents. Check for duplicates and low quality cards.
```

Tips:
- Similar to Claude Code but prefers higher-level instructions
- Can handle multi-step tasks in a single prompt
- Don't micro-manage tool usage

## Bash (raw terminal)

Good:
```
backend/.venv/bin/python3 scripts/dedup_documents.py --dry-run 2>&1 | tail -20
```

Tips:
- Exact commands only — no natural language
- Use full paths (not relative)
- Chain with `&&` for sequential execution
