# Skill: Skill Harvesting (Post-Session)

> Créer des skills réutilisables après une session de debug ou implémentation complexe

---

## Vue d'ensemble

Le skill harvesting consiste à extraire les patterns et solutions découverts pendant une session pour les transformer en skills réutilisables.

---

## Quand Harvester ?

| Situation | Action |
|-----------|--------|
| Tâche > 3 cycles Ralph | Créer skill debug |
| Pattern réutilisable trouvé | Créer skill pattern |
| Solution non triviale | Documenter dans skill |
| Erreur récurrente résolue | Créer skill fix |

---

## Process de Harvesting

### 1. Identifier le pattern

```
Questions à se poser :
- Ce problème/solution est-il susceptible de se reproduire ?
- La solution est-elle non triviale (> 5 min de réflexion) ?
- D'autres projets pourraient-ils en bénéficier ?
```

### 2. Créer le fichier skill

```bash
# Chemin
agents_library/universal-orchestrator/skills/[nom-du-skill].md

# Ou dans un dossier agent spécifique
agents_library/[agent]/skills/[nom-du-skill].md
```

### 3. Remplir le template

```markdown
# Skill: [NOM]

> [Description en une ligne]

---

## Contexte

[Quand utiliser ce skill - situation, symptômes]

## Problème

[Description du problème résolu]

## Solution

[Code/process/commandes]

```bash
# Exemple de commande
```

## Exemples d'utilisation

### Exemple 1
[Cas concret]

### Exemple 2
[Autre cas]

## Références

- [Liens vers docs]
- [Issues liées]

---

*Créé le [DATE] suite à [CONTEXTE]*
```

### 4. Référencer dans CLAUDE.md

```markdown
## Skills créés cette session

| Skill | Description | Date |
|-------|-------------|------|
| fix-circular-import | Résoudre imports circulaires Python | 2026-02-27 |
```

---

## Exemples de Skills à Harvester

### Après debug complexe

```markdown
# Skill: Debug Import Circulaire Python

> Résoudre les erreurs d'import circulaire dans les projets Python

## Contexte
Erreur `ImportError: cannot import name 'X' from 'Y'` dans un projet avec models/schemas interdépendants.

## Solution
Utiliser `TYPE_CHECKING` :

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models import User

def get_user() -> "User":
    ...
```
```

### Après pattern répété

```markdown
# Skill: FastAPI Router Pattern

> Template standard pour créer un router FastAPI

## Solution

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

router = APIRouter(prefix="/items", tags=["items"])

@router.get("/")
def list_items(db: Session = Depends(get_db)):
    return db.query(Item).all()
```
```

---

## Automatisation

### Script de harvesting

```bash
#!/bin/bash
# harvest-skill.sh - Crée un nouveau skill

NAME=$1
DESC=$2
DATE=$(date +%Y-%m-%d)

cat > "agents_library/universal-orchestrator/skills/$NAME.md" << EOF
# Skill: $NAME

> $DESC

---

## Contexte

[À compléter]

## Solution

[À compléter]

---

*Créé le $DATE*
EOF

echo "✅ Skill créé: agents_library/universal-orchestrator/skills/$NAME.md"
```

---

## Bonnes Pratiques

1. **Nommer clairement** - Le nom doit indiquer l'usage
2. **Documenter le contexte** - Quand utiliser ce skill
3. **Inclure des exemples** - Code concret, pas abstrait
4. **Référencer les sources** - Liens, issues, docs
5. **Mettre à jour CLAUDE.md** - Traçabilité

---

*Skill Harvesting v1.0*
