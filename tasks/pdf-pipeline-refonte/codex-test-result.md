# T-049 - Test et validation du fix rate-limit Claude CLI

Date: 2026-03-25
Timezone: Europe/Paris

## Verification du code

- `backend/app/services/claude_service.py:46-80`
  - `run_claude_cli()` nettoie les variables d'environnement `CLAUDE*`, `anthropic*`, `mcp*`.
  - Le retry tourne sur `max_retries=3`.
  - Le backoff est bien `30s`, puis `60s`, puis erreur finale au 3e echec.
- `scripts/reextract_and_generate.py:218-248`
  - `phase_fiches()` applique bien `await asyncio.sleep(5)` apres succes.
  - `phase_fiches()` applique bien `await asyncio.sleep(10)` apres erreur.

## Commandes executees

### 1. Smoke test Claude CLI

Commande:

```bash
python3 -c 'import asyncio,sys; sys.path.insert(0,"backend"); from app.services.claude_service import run_claude_cli; print(asyncio.run(run_claude_cli("Dis OK")))'
```

Resultat:

```text
OK
```

### 2. Batch de validation

Commande:

```bash
python3 scripts/reextract_and_generate.py --matiere "Licence 2 - Semestre 3" --limit 2 --skip-extract --skip-flashcards 2>&1 | tee tasks/pdf-pipeline-refonte/batch-codex-test.log
```

Extrait du log:

```text
04:11:22 INFO    Phase 2 — génération fiches: 2 documents sans fiche
04:11:22 INFO    [fiche] [632] ADM 7 [Licence 2 - Semestre 3] …
04:17:18 WARNING Claude CLI error (attempt 1/3, rc=1): You've hit your limit · resets 8am (Europe/Paris) — retry in 30s
04:18:02 WARNING Claude CLI error (attempt 2/3, rc=1): You've hit your limit · resets 8am (Europe/Paris) — retry in 60s
04:19:09 ERROR   [fiche] [632] ERREUR: Claude CLI error (rc=1): You've hit your limit · resets 8am (Europe/Paris)
04:19:19 INFO    [fiche] [633] ADM 8(1) [Licence 2 - Semestre 3] …
04:19:27 WARNING Claude CLI error (attempt 1/3, rc=1): You've hit your limit · resets 8am (Europe/Paris) — retry in 30s
04:20:04 WARNING Claude CLI error (attempt 2/3, rc=1): You've hit your limit · resets 8am (Europe/Paris) — retry in 60s
04:21:11 ERROR   [fiche] [633] ERREUR: Claude CLI error (rc=1): You've hit your limit · resets 8am (Europe/Paris)
04:21:21 INFO    Phase 2 terminée — ok=0 skipped=0 error=2
04:21:21 INFO    Terminé.
```

## Validation DB

Verification apres batch:

```text
document_id=632 -> 0 fiche
document_id=633 -> 0 fiche
```

## Conclusion

- Le fix de retry/backoff est fonctionnel.
- Le batch a bien applique le schema de retry attendu avant de journaliser l'erreur finale.
- L'echec observe n'est pas un crash Python ni un bug de boucle de retry.
- La cause effective est un quota Claude epuise, avec reset annonce a `08:00` (Europe/Paris) le `2026-03-25`.

## Acceptance

Statut: NON VALIDE

Raison:

- Critere demande: au moins `1/2` fiche generee OK.
- Resultat observe: `0/2` fiche generee OK.
- Blocage externe: rate limit/quota Claude atteint pendant le batch.

## Action recommandee

Relancer exactement le meme batch apres `2026-03-25 08:00 Europe/Paris` pour valider l'acceptance fonctionnelle sur donnees reelles.
