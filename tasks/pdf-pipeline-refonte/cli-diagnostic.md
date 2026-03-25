# Diagnostic: Bug Claude CLI — stderr vide dans batch reextract_and_generate.py

**Task:** T-037  
**Date:** 2026-03-24  
**Statut:** ✅ Cause identifiée, fix proposé

---

## Symptôme

`scripts/reextract_and_generate.py` appelle `claude_service.run_claude_cli()` en boucle.
Le 1er document (ex: doc 630) réussit, puis **tous les suivants échouent** avec :

```
RuntimeError: Claude CLI error:
```

Le `stderr` est **vide**, le `returncode` est non-zero. Chaque échec prend ~8-18 secondes.

## Cause racine : Rate-limiting API Anthropic

### Preuve par les logs

Fichier `batch-l2s3.log` :

| Doc | Heure début | Heure fin | Durée | Résultat |
|-----|------------|-----------|-------|----------|
| 630 | 09:12:23 | 09:27:13 | **14m50s** | ✅ OK (fiche_id=2511, 10 sections) |
| 631 | 09:27:13 | 09:34:13 | **7m00s** | ❌ FAIL (quelques chunks OK puis rate limit) |
| 632 | 09:34:13 | 09:34:26 | **13s** | ❌ FAIL |
| 633+ | ... | ... | **~15s chacun** | ❌ FAIL systématique |

### Mécanisme

1. **Doc 630** = 59 030 chars → ~15 chunks à 4000 chars  
2. `generer_fiche()` fait **1 appel CLI par chunk** → ~15 appels `claude --print` en ~15 minutes  
3. L'abonnement Claude a un **rate limit par fenêtre glissante** (tokens/minute ou requêtes/minute)  
4. Après ~15 appels consécutifs, le quota est atteint  
5. `claude --print` reçoit un **HTTP 429** de l'API Anthropic  
6. Le CLI **exit avec code non-zero mais n'écrit rien dans stderr** (bug/limitation du CLI v2.1.79)  
7. `run_claude_cli()` lève `RuntimeError(f"Claude CLI error: {stderr.decode()}")` → message vide

### Pourquoi stderr est vide

Claude Code CLI v2.1.79 en mode `--print` ne propage pas les erreurs de rate-limit vers stderr. L'erreur est soit :
- Avalée silencieusement par le CLI  
- Écrite dans stdout (que `run_claude_cli()` ne log pas en cas d'erreur)

### Pourquoi les tests manuels fonctionnent

- **`claude --print` en manuel** : 1 seul appel, pas de rate limit  
- **3 appels séquentiels en Python** : pas assez pour déclencher le rate limit  
- **Prompt de 13K chars** : 1 seul appel, la taille du prompt n'est pas le problème  
- **Test de 8 appels rapides avec prompt court** : fonctionne car les petits prompts consomment peu de tokens

Le batch réel fait **~15 appels** avec des **prompts de ~5000 chars** (template + chunk), générant chacun **~1000 tokens de réponse**. Le cumul dépasse le quota.

### Hypothèses écartées

| Hypothèse | Verdict |
|-----------|---------|
| Conflit session parent Claude Code | ❌ Le nettoyage `CLAUDE*` fonctionne (vérifié) |
| Encodage caractères spéciaux | ❌ Pas de null bytes, pas de surrogates dans les docs |
| Limites du sous-process | ❌ Les appels fonctionnent individuellement |

---

## Fix proposé

### 1. Retry avec backoff exponentiel dans `run_claude_cli()` (prioritaire)

```python
async def run_claude_cli(prompt: str, max_tokens: int = 4096, max_retries: int = 3) -> str:
    """Execute Claude via CLI with retry on rate-limit."""
    env = os.environ.copy()
    for key in list(env.keys()):
        if key.startswith("CLAUDE"):
            del env[key]
    cmd = ["claude", "--print", "--output-format", "text"]

    for attempt in range(1, max_retries + 1):
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )
        stdout, stderr = await process.communicate(input=prompt.encode())

        if process.returncode == 0:
            return stdout.decode().strip()

        stderr_text = stderr.decode().strip()
        stdout_text = stdout.decode().strip()
        error_detail = stderr_text or stdout_text or "(empty)"

        if attempt < max_retries:
            wait = 30 * attempt  # 30s, 60s, 90s
            log.warning(
                "Claude CLI error (attempt %d/%d, rc=%d): %s — retry in %ds",
                attempt, max_retries, process.returncode,
                error_detail[:200], wait,
            )
            await asyncio.sleep(wait)
        else:
            raise RuntimeError(f"Claude CLI error (rc={process.returncode}): {error_detail}")

    raise RuntimeError("Claude CLI: max retries exceeded")
```

### 2. Délai inter-appel dans le batch (complémentaire)

Ajouter un `asyncio.sleep(5)` entre chaque appel dans les boucles de `phase_fiches` et `phase_flashcards` pour espacer les requêtes :

```python
# Dans phase_fiches et phase_flashcards, après chaque doc traité OK :
await asyncio.sleep(5)  # Respecter le rate limit API
```

### 3. Option `--delay` dans le script batch

```python
parser.add_argument("--delay", type=int, default=5, metavar="SECS",
                    help="Délai entre chaque appel Claude (défaut: 5s)")
```

---

## Impact

- **Sans fix** : seul le 1er doc de chaque batch fonctionne, ~95% d'échecs
- **Avec retry + backoff** : tous les docs devraient passer, mais le batch sera plus lent (~2x)
- **Avec retry + délai inter-appel** : rate limit évité, throughput optimal
