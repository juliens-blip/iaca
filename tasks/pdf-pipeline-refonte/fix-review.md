# Review — fix rate-limit claude_service.py + reextract_and_generate.py

Date: 2026-03-25

---

## claude_service.py — `run_claude_cli()`

### Ce qui fonctionne correctement

- **Retry loop structurellement correct** : `range(1, max_retries+1)` itère bien 3 fois. Le dernier essai lève, les précédents logguent et dorment. Pas d'ambiguïté.
- **Pas de fuite de process** : `process.communicate()` attend la fin du subprocess avant de continuer. Pas besoin de `process.wait()` ou de nettoyage explicite.
- **Capture d'erreur stdout/stderr** : `error_detail = stderr_text or stdout_text or "(empty)"` est correct. Certaines versions du CLI Claude écrivent l'erreur sur stdout — le fallback couvre ce cas.
- **Backoff raisonnable** : 30 s → 60 s → 90 s, soit 3 min max de délai total avant abandon. Adapté aux rate limits Claude.
- **Retry sur tout returncode ≠ 0** : acceptable ici — les erreurs permanentes (mauvais prompt) ne font que consommer les 3 tentatives puis lèvent. Pas de risque de boucle infinie.

### Corrections appliquées

| # | Sévérité | Problème | Correction |
|---|---|---|---|
| 1 | Avertissement | `max_tokens: int = 4096` déclaré dans la signature mais jamais utilisé (option `--max-tokens` supprimée car non supportée par le CLI) | Paramètre supprimé |
| 2 | Avertissement | `raise RuntimeError("Claude CLI: max retries exceeded")` ligne 82 — code mort inatteignable (le dernier essai lève toujours avant d'atteindre cette ligne) | Ligne supprimée |

---

## reextract_and_generate.py — phases fiches et flashcards

### Ce qui fonctionne correctement

- **`asyncio.sleep(5)` après succès / `sleep(10)` après erreur** : cohérent avec le mécanisme de retry interne de `run_claude_cli`. Le sleep externe ajoute un espacement inter-documents sans interférer avec le backoff interne.
- **Détection `nb_flashcards`** : `"nb_flashcards" in doc.keys()` est la bonne façon de tester un champ optionnel sur un `sqlite3.Row`.
- **SQL `fetch_docs_with_few_flashcards`** : la substitution `sql.replace("GROUP BY d.id", "AND lower(m.nom) LIKE ? GROUP BY d.id")` + réordonnancement `params = [matiere, min_fc]` est correcte — le `?` du LIKE précède le `?` du HAVING, dans le même ordre que les params.
- **Traitement séquentiel** : intentionnel et adapté aux contraintes de rate limit. Pas de parallélisme, donc pas de risque de rafale.

### Points à surveiller (non bloquants)

| # | Sévérité | Observation | Recommandation |
|---|---|---|---|
| 1 | Suggestion | `conn.close()` dans `main()` non protégé par `try/finally` — une exception non attrapée dans une phase ferme le script sans fermer la connexion | Pour un script batch court-lived, le kernel récupère le FD. Pas critique, mais un `try/finally: conn.close()` serait propre. |
| 2 | Suggestion | Le sleep(5) couvre un document avec contenu court (1 chunk = 1 appel CLI). Pour un document long chunké en 4-6 parties, `generer_fiche` fait 4-6 appels CLI consécutifs en interne sans sleep entre eux — le sleep externe de 5 s ne s'intercale qu'entre deux documents. | Acceptable : `run_claude_cli` gère les rate limits en interne. Si des erreurs de rate limit persistent sur des docs longs, envisager un sleep inter-chunk dans `generer_fiche`. |
| 3 | Info | `fetch_docs_to_reextract` sélectionne les docs avec `< 200 chars`, mais `fetch_docs_without_fiche` et `fetch_docs_with_few_flashcards` utilisent `>= 120 chars`. Les docs entre 120 et 200 chars peuvent entrer en phase 2/3 mais pas en phase 1. | Cohérence intentionnelle (seuils différents par phase). OK tel quel. |

### Aucune correction appliquée dans ce fichier

Les deux corrections appliquées sont dans `claude_service.py` uniquement. `reextract_and_generate.py` est fonctionnel tel quel.

---

## État final

```
backend/app/services/claude_service.py  — 2 corrections appliquées (param inutilisé, dead code)
scripts/reextract_and_generate.py       — aucune correction nécessaire
```

Compile check : `python3 -m compileall backend/app/services/claude_service.py scripts/reextract_and_generate.py` — OK.
