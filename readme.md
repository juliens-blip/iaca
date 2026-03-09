# IACA - Intelligence Artificielle pour Cours et Apprentissage

> Assistant IA personnel de revision pour Master en Droit

---

## Vision

Un professeur personnel IA avec:
- Flashcards intelligentes generees depuis tes cours (PDF/PPTX)
- Quiz et cas pratiques juridiques
- Interaction vocale en francais (ecoute + parle)
- Organisation par matieres et chapitres
- Contenus visuels (mind maps, schemas)

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   FRONTEND WEB                       │
│              (React/Next.js + TailwindCSS)          │
└─────────────────────┬───────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────┐
│                   BACKEND API                        │
│                    (FastAPI)                         │
├─────────────────────────────────────────────────────┤
│  Documents  │  Flashcards  │  Quiz  │  Vocal  │ ... │
└─────────────────────┬───────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        ▼             ▼             ▼
┌───────────┐  ┌───────────┐  ┌───────────┐
│  Claude   │  │  Gemini   │  │  Local    │
│   API     │  │   API     │  │ STT/TTS   │
│ (texte)   │  │ (visuel)  │  │ Whisper   │
│           │  │           │  │ Piper     │
└───────────┘  └───────────┘  └───────────┘
```

---

## Stack Technique

### Backend
- Python 3.11+
- FastAPI
- SQLite/PostgreSQL
- Redis (cache)

### Frontend
- React 18+ / Next.js 14+
- TailwindCSS
- shadcn/ui

### IA
- **Claude API** - Comprehension, generation texte, flashcards
- **Gemini API** - Generation visuelle (mind maps, schemas)
- **Whisper** - STT local (voix → texte)
- **Piper TTS** - TTS local (texte → voix)

### Documents
- PyMuPDF (PDF)
- python-pptx (PowerPoint)

---

## Cles API Requises

```env
# .env
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...
```

---

## Developpement

**REGLE:** Utiliser `universal-orchestrator` pour diviser les taches.

```bash
# Charger l'orchestrateur
@agents_library/agent-orchestrator-universal/universal-orchestrator.md

# Lancer sur une tache
/start "Implementer le module d'ingestion de documents PDF"
```

Voir `AGENT.md` pour le catalogue complet des agents.

---

## Structure Projet (a venir)

```
IACA/
├── agents_library/          # Agents IA (copie)
├── backend/                 # API FastAPI
│   ├── api/
│   ├── services/
│   └── models/
├── frontend/                # App React/Next.js
│   ├── components/
│   └── pages/
├── docs/                    # Cours uploades
│   └── matieres/
├── data/                    # Base de donnees
├── claude.md                # Memoire projet
├── AGENT.md                 # Catalogue agents
└── readme.md                # Ce fichier
```

---

## Prochaines Etapes

1. Configurer les cles API
2. Definir les matieres du Master
3. Lancer l'orchestrateur pour implementer

---

*Projet demarre le 2026-02-26*
