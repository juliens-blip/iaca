#!/usr/bin/env python3
"""
Test des nouveaux prompts: generer_flashcards et generer_fiche.

Récupère un document aléatoire de data/iaca.db (contenu > 1000 chars),
appelle les fonctions Claude, et affiche les résultats en JSON.

Usage:
  python3 scripts/test_new_prompts.py --limit 1
  python3 scripts/test_new_prompts.py --limit 1 --dry-run
"""

import argparse
import asyncio
import json
import random
import sqlite3
import sys
from pathlib import Path
from typing import Optional

# Ajouter le backend au path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))


async def main():
    parser = argparse.ArgumentParser(
        description="Test les nouveaux prompts Claude pour flashcards et fiches"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=1,
        help="Nombre de documents à tester (défaut: 1)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Affiche juste le document choisi sans appeler Claude",
    )
    args = parser.parse_args()

    # Connexion DB
    db_path = Path(__file__).parent.parent / "data" / "iaca.db"
    if not db_path.exists():
        print(f"❌ DB non trouvée: {db_path}")
        sys.exit(1)

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Récupérer documents avec contenu > 1000 chars
    cursor.execute(
        """
        SELECT id, titre, matiere_id, contenu_extrait
        FROM documents
        WHERE length(contenu_extrait) > 1000
        ORDER BY RANDOM()
        LIMIT ?
    """,
        (args.limit,),
    )
    docs = cursor.fetchall()

    if not docs:
        print("❌ Aucun document avec contenu > 1000 chars trouvé")
        sys.exit(1)

    # Récupérer le mapping matiere_id -> matiere.nom
    cursor.execute("SELECT id, nom FROM matieres")
    matieres = {row[0]: row[1] for row in cursor.fetchall()}
    conn.close()

    # Traiter chaque document
    for idx, doc in enumerate(docs, 1):
        doc_id = doc["id"]
        titre = doc["titre"]
        matiere_id = doc["matiere_id"]
        contenu = doc["contenu_extrait"]
        matiere_nom = matieres.get(matiere_id, "Inconnue")

        print("=" * 75)
        print(f"Test {idx}/{len(docs)} — Document {doc_id}")
        print("=" * 75)
        print(f"Titre: {titre}")
        print(f"Matière: {matiere_nom}")
        print(f"Contenu: {len(contenu):,} chars")
        print()

        if args.dry_run:
            print("🔍 Mode dry-run: affichage du document uniquement")
            print()
            print("Aperçu du contenu (500 chars):")
            print("-" * 75)
            preview = contenu[:500].replace("\n", " ")
            print(f"{preview}...")
            print("-" * 75)
            continue

        # Importer les fonctions Claude
        try:
            from app.services.claude_service import (
                generer_flashcards,
                generer_fiche,
            )
        except ImportError as e:
            print(f"❌ Erreur d'import: {e}")
            sys.exit(1)

        # Appeler generer_flashcards
        print("📇 Génération flashcards...")
        try:
            flashcards = await generer_flashcards(
                contenu=contenu, matiere=matiere_nom, nb=3
            )
            print(f"   ✅ {len(flashcards)} flashcards générées")
            print()
            print("Flashcards JSON:")
            print(json.dumps(flashcards, ensure_ascii=False, indent=2))
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
            flashcards = []

        print()
        print("-" * 75)
        print()

        # Appeler generer_fiche
        print("📋 Génération fiche...")
        try:
            fiche = await generer_fiche(
                contenu=contenu, matiere=matiere_nom, titre_doc=titre
            )
            print(f"   ✅ Fiche générée")
            print(f"      • Titre: {fiche.get('titre', 'N/A')}")
            print(f"      • Sections: {len(fiche.get('sections', []))}")
            print()
            print("Fiche JSON:")
            print(json.dumps(fiche, ensure_ascii=False, indent=2))
        except Exception as e:
            print(f"   ❌ Erreur: {e}")

        print()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⏸️  Interrompu par l'utilisateur")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        sys.exit(1)
