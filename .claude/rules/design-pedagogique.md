# Agent Design Pedagogique

## Declencheur

Cette regle s'active quand l'utilisateur demande de :
- Reformater / redesigner des fiches de revision
- Appliquer la charte graphique pedagogique
- Ameliorer le design d'apprentissage des composants
- Creer de nouveaux composants de revision (fiches, flashcards, QCM)

Mots-cles : "design pedagogique", "charte graphique", "reformater fiches", "appliquer design", "ameliorer lisibilite"

## Protocole obligatoire

### Etape 1 : Charger la charte
Lire `.claude/charte-graphique-pedagogique.md` en entier AVANT toute modification.

### Etape 2 : Auditer le composant cible
Pour chaque fichier a modifier, verifier ces 10 points :

1. **Hierarchie visuelle** : H1 > H2 > H3 > body avec tailles et poids distincts
2. **Palette** : max 3-4 couleurs, couleurs de matiere coherentes avec `matiereColors`
3. **Contraste de pertinence** : contenu pedagogique = colore, decoratif = desature/gris
4. **Typographie** : `font-heading` pour H1, `font-body` pour le reste, interligne `leading-7`
5. **Espacement** : `space-y-6` entre sections, `space-y-4` entre paragraphes, `p-5` encadres
6. **Chunking** : listes <= 9 items, accordeons si besoin, 1 image instructive max/section
7. **Encadres semantiques** : "A retenir" (orange), "Definition" (blue), "Exemple" (emerald), "Attention" (rose)
8. **Feedback** : etats loading/error/vide, transitions 200-300ms, hover/focus visibles
9. **Accessibilite** : contraste >=4.5:1, `aria-label`, tailles cibles 44px+
10. **Anti-patterns** : aucun des 10 anti-patterns listes dans la charte

### Etape 3 : Plan de modifications
Lister les modifications necessaires AVANT d'editer, avec justification pour chaque changement basee sur un principe de la charte.

### Etape 4 : Appliquer
- Modifier le minimum necessaire pour respecter la charte
- Conserver l'architecture existante (App Router, composants existants)
- Reutiliser les classes utilitaires de `globals.css` (`card`, `btn-primary`, etc.)
- Respecter les couleurs de matiere existantes dans `matiereColors`

### Etape 5 : Verifier
Executer `cd frontend && npx tsc --noEmit` apres modification.

## Composants de reference

### Encadre semantique generique
```tsx
function PedagogicalBox({
  type,
  children
}: {
  type: "retenir" | "definition" | "exemple" | "attention" | "resume";
  children: React.ReactNode;
}) {
  const config = {
    retenir: {
      bg: "bg-orange-500/10",
      border: "border-orange-500/30",
      text: "text-orange-400",
      title: "A retenir",
      icon: "M11.48 3.499a.562.562 0 0 1 1.04 0l2.125 5.111a.563.563 0 0 0 .475.345l5.518.442c.499.04.701.663.321.988l-4.204 3.602a.563.563 0 0 0-.182.557l1.285 5.385a.562.562 0 0 1-.84.61l-4.725-2.885a.562.562 0 0 0-.586 0L6.982 20.54a.562.562 0 0 1-.84-.61l1.285-5.386a.562.562 0 0 0-.182-.557l-4.204-3.602a.562.562 0 0 1 .321-.988l5.518-.442a.563.563 0 0 0 .475-.345L11.48 3.5Z",
    },
    definition: {
      bg: "bg-blue-500/10",
      border: "border-blue-500/30",
      text: "text-blue-400",
      title: "Definition",
      icon: "M12 6.042A8.967 8.967 0 0 0 6 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 0 1 6 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 0 1 6-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0 0 18 18a8.967 8.967 0 0 0-6 2.292m0-14.25v14.25",
    },
    exemple: {
      bg: "bg-emerald-500/10",
      border: "border-emerald-500/30",
      text: "text-emerald-400",
      title: "Exemple",
      icon: "M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75Z",
    },
    attention: {
      bg: "bg-rose-500/10",
      border: "border-rose-500/30",
      text: "text-rose-400",
      title: "Attention",
      icon: "M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z",
    },
    resume: {
      bg: "bg-violet-500/10",
      border: "border-violet-500/30",
      text: "text-violet-400",
      title: "En resume",
      icon: "M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25H12",
    },
  };
  const c = config[type];
  return (
    <div className={`rounded-xl border ${c.border} ${c.bg} p-5`}>
      <div className="flex items-start gap-3">
        <div className={`p-2 rounded-lg ${c.bg} ${c.text} shrink-0 mt-0.5`}>
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d={c.icon} />
          </svg>
        </div>
        <div className="flex-1">
          <p className={`text-xs font-semibold ${c.text} uppercase tracking-wider mb-2`}>{c.title}</p>
          <div className="text-slate-200 text-base leading-7">{children}</div>
        </div>
      </div>
    </div>
  );
}
```

### Flashcard optimisee
```tsx
// Face question : gradient matiere en fond, question centree
// Face reponse : fond neutre, reponse + explication dans encadre
// Boutons de feedback : Facile (emerald) / Moyen (amber) / Difficile (rose)
```

## Regles de contenu genere (pour les prompts IA)

Quand on genere du contenu de fiche via IA, le prompt doit demander :
- Des sections de 5-9 paragraphes/items max
- Des termes cles en **gras** (pas des phrases entieres)
- Des encadres "A retenir" pour les points essentiels
- Des encadres "Definition" pour le vocabulaire technique
- Des encadres "Exemple" pour les illustrations concretes
- Des encadres "Attention" pour les pieges courants
- Progression du simple au complexe

## Fichiers concernes

- `frontend/app/fiches/page.tsx` - Page principale des fiches
- `frontend/app/flashcards/page.tsx` - Page des flashcards
- `frontend/components/FlashCard.tsx` - Composant flashcard
- `frontend/app/globals.css` - Classes utilitaires
- `frontend/app/quiz/page.tsx` - Page quiz (si elle existe)
