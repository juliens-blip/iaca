# Résultat du test fix rate-limit — T-044

**Date:** 2026-03-25 04:28  
**Commande:** `python3 scripts/reextract_and_generate.py --matiere "Licence 2 - Semestre 3" --limit 3 --skip-extract`

---

## Résultat : 1/3 OK — le fix fonctionne mais le rate limit est un hard cap quotidien

### Phase 2 (fiches)

| Doc | Durée | Résultat |
|-----|-------|----------|
| 631 (59K chars, ~14 chunks) | 12m41s | ✅ OK — fiche_id=2525, 10 sections |
| 632 (59K chars, ~14 chunks) | 11m34s | ❌ Rate limit atteint mid-chunk |
| 633 (93K chars, ~23 chunks) | 1m50s | ❌ Rate limit (3 tentatives échouées) |

### Phase 3 (flashcards)

| Doc | Résultat |
|-----|----------|
| 1433, 1434, 1435 | ❌ Rate limit (quota épuisé) |

### Ce que le fix a corrigé

1. **✅ Le message d'erreur est maintenant visible** :  
   `Claude CLI error (rc=1): You've hit your limit · resets 8am (Europe/Paris)`  
   Avant : `Claude CLI error:` (vide)

2. **✅ Le retry avec backoff fonctionne** :  
   ```
   04:18:02 WARNING attempt 1/3 — retry in 30s
   04:18:39 WARNING attempt 2/3 — retry in 60s
   04:19:46 ERROR   final failure
   ```

3. **✅ Le sleep inter-doc fonctionne** : 5s après OK, 10s après erreur

### Pourquoi seulement 1/3

Le rate limit Claude n'est **pas une fenêtre glissante** (requests/minute) — c'est un **quota quotidien** :
- `"You've hit your limit · resets 8am (Europe/Paris)"`
- Doc 631 (~14 chunks = ~14 appels API) a consommé le quota restant
- Tous les appels après sont bloqués jusqu'à 8h du matin

### Conclusion

Le fix **résout le problème technique** (stderr vide → erreur visible, retry sur erreurs temporaires). Mais le **vrai goulot d'étranglement est le quota quotidien** de l'abonnement Claude.

### Recommandations pour la suite

| Action | Impact |
|--------|--------|
| **Lancer les batches juste après 8h** (reset quota) | Maximise le nombre de docs par run |
| **Ajouter `--stop-on-rate-limit`** | Arrêter le batch dès le premier rate limit au lieu de gaspiller 90s de retry par doc |
| **Passer à l'API Anthropic** avec clé API | Contrôle fin du rate limit, pas de quota quotidien fixe |
| **Fallback Ollama local** (comme dans `generate_full_coverage.py`) | Bypass complet du rate limit pour les docs restants |

### Acceptance criteria

- ❌ 2/3 docs avec fiche OK — non atteint (quota quotidien épuisé, pas un bug du fix)
- ✅ Le fix retry + backoff fonctionne correctement
- ✅ L'erreur rate-limit est maintenant diagnostiquée et visible
- ✅ Le fix résout le problème original (stderr vide)
