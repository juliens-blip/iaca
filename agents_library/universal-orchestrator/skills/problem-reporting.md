# Skill: Problem Reporting (probleme.Md)

> Documenter les problèmes rencontrés dans probleme.Md

---

## RÈGLE OBLIGATOIRE

**Tout problème rencontré par un agent doit être documenté dans `probleme.Md`.**

---

## Chemin du fichier

```
/home/julien/Documents/IACA/probleme.Md
```

---

## Format du rapport

```markdown
### [DATE] - [AGENT] - [TÂCHE]
**Probleme:** Description claire du problème
**Erreur:** Message d'erreur exact (copier-coller)
**Contexte:** Ce qui a été tenté avant l'erreur
**Status:** En attente / Résolu
**Pistes de solution:**
1. Première piste
2. Deuxième piste
**Solution:** (remplir quand résolu)
```

---

## Quand créer un rapport ?

| Situation | Créer rapport ? |
|-----------|-----------------|
| Erreur bloquante | ✅ OUI |
| Bug reproductible | ✅ OUI |
| Comportement inattendu | ✅ OUI |
| Timeout/crash | ✅ OUI |
| Simple typo corrigée | ❌ NON |
| Warning non bloquant | ⚠️ Optionnel |

---

## Exemple de rapport

```markdown
### [2026-02-27] - claude-sonnet (w3) - S5 Router documents
**Probleme:** L'upload de fichiers PDF échoue avec erreur 413
**Erreur:** `HTTP 413 Request Entity Too Large`
**Contexte:**
- Tentative d'upload d'un PDF de 50MB
- Config FastAPI par défaut
- Nginx en reverse proxy
**Status:** En attente
**Pistes de solution:**
1. Augmenter `client_max_body_size` dans nginx.conf
2. Ajouter `max_request_size` dans FastAPI
3. Implémenter upload chunké
```

---

## Commande rapide pour ajouter un rapport

```bash
#!/bin/bash
# add-problem.sh

DATE=$(date +%Y-%m-%d)
AGENT=$1
TASK=$2
PROBLEM=$3

cat >> probleme.Md << EOF

### [$DATE] - $AGENT - $TASK
**Probleme:** $PROBLEM
**Erreur:** [À compléter]
**Contexte:** [À compléter]
**Status:** En attente
**Pistes de solution:**
1. [À compléter]
EOF

echo "✅ Rapport ajouté à probleme.Md"
```

---

## Workflow problème → solution → skill

```
1. PROBLÈME RENCONTRÉ
   └─ Documenter dans probleme.Md (Status: En attente)

2. INVESTIGATION
   └─ Tester les pistes de solution
   └─ Mettre à jour le rapport

3. SOLUTION TROUVÉE
   └─ Mettre Status: Résolu
   └─ Documenter la solution

4. SKILL HARVESTING (si applicable)
   └─ Si solution non triviale → créer un skill
   └─ Voir skill-harvesting.md
```

---

## Statuts possibles

| Status | Signification |
|--------|---------------|
| En attente | Problème identifié, pas encore résolu |
| En cours | Investigation active |
| Résolu | Solution trouvée et appliquée |
| Contourné | Workaround appliqué, pas de vraie solution |
| Abandonné | Problème non critique, ignoré |

---

*Skill Problem Reporting v1.0*
