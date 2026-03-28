#!/usr/bin/env python3
"""
Audit des documents avec contenu vide (<120 chars) dans data/iaca.db
Identifie les documents orphelins (sans fiches/flashcards/quiz)
"""

import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent.parent / "data" / "iaca.db"

def get_connection():
    """Créer une connexion SQLite"""
    return sqlite3.connect(DB_PATH)

def audit_empty_documents():
    """Analyser les documents avec contenu < 120 chars"""
    conn = get_connection()
    cursor = conn.cursor()

    # Documents avec contenu < 120 chars
    cursor.execute("""
        SELECT id, titre, fichier_path,
               COALESCE(contenu_extrait, '') as contenu,
               matiere_id, created_at
        FROM documents
        WHERE LENGTH(COALESCE(contenu_extrait, '')) < 120
        ORDER BY id
    """)

    empty_docs = cursor.fetchall()

    # Pour chaque document vide, compter les associations
    results = []
    for doc_id, titre, fichier_path, contenu, matiere_id, created_at in empty_docs:
        # Compter flashcards
        cursor.execute("SELECT COUNT(*) FROM flashcards WHERE document_id = ?", (doc_id,))
        fc_count = cursor.fetchone()[0]

        # Compter quizzes
        cursor.execute("SELECT COUNT(*) FROM quizzes WHERE document_id = ?", (doc_id,))
        quiz_count = cursor.fetchone()[0]

        # Compter fiches
        cursor.execute("SELECT COUNT(*) FROM fiches WHERE document_id = ?", (doc_id,))
        fiche_count = cursor.fetchone()[0]

        # Total de contenus générés
        total_content = fc_count + quiz_count + fiche_count

        results.append({
            'id': doc_id,
            'titre': titre,
            'fichier_path': fichier_path,
            'contenu_chars': len(contenu),
            'matiere_id': matiere_id,
            'created_at': created_at,
            'flashcards': fc_count,
            'quizzes': quiz_count,
            'fiches': fiche_count,
            'total_content': total_content,
            'orphan': total_content == 0
        })

    conn.close()
    return results

def generate_report(results):
    """Générer le rapport markdown"""

    # Statistiques
    total_docs = len(results)
    orphans = [r for r in results if r['orphan']]
    non_orphans = [r for r in results if not r['orphan']]

    report = f"""# Audit des Documents Vides

**Date d'audit**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Résumé

- **Documents avec contenu < 120 caractères**: {total_docs}
- **Documents orphelins** (sans fiches/FC/quiz): {len(orphans)}
- **Documents avec contenu généré**: {len(non_orphans)}

## Documents Orphelins (Suppression Potentielle)

{len(orphans)} documents n'ont aucun contenu généré associé:

| ID | Titre | Fichier | Chars | Matière | Créé |
|---|---|---|---|---|---|
"""

    for doc in sorted(orphans, key=lambda x: x['id']):
        report += f"| {doc['id']} | {doc['titre'][:40]} | {doc['fichier_path'][-30:]} | {doc['contenu_chars']} | {doc['matiere_id']} | {doc['created_at'][:10]} |\n"

    # Documents non-orphelins
    report += f"\n## Documents avec Contenu Généré ({len(non_orphans)})\n\n"
    report += "| ID | Titre | FC | Quiz | Fiches | Total |\n"
    report += "|---|---|---|---|---|---|\n"

    for doc in sorted(non_orphans, key=lambda x: x['id']):
        report += f"| {doc['id']} | {doc['titre'][:35]} | {doc['flashcards']} | {doc['quizzes']} | {doc['fiches']} | {doc['total_content']} |\n"

    # Détail complet des orphelins
    report += f"\n## Détail Complet (Orphelins)\n\n"
    for doc in sorted(orphans, key=lambda x: x['id']):
        report += f"### Doc #{doc['id']}: {doc['titre']}\n"
        report += f"- **Fichier**: `{doc['fichier_path']}`\n"
        report += f"- **Contenu extrait**: {doc['contenu_chars']} caractères\n"
        report += f"- **Matière**: ID {doc['matiere_id']}\n"
        report += f"- **Créé**: {doc['created_at']}\n"
        report += f"- **Associations**: FC=0, Quiz=0, Fiches=0 → **À supprimer?**\n\n"

    # Recommandations
    report += f"\n## Recommandations\n\n"
    report += f"1. **Vérifier les documents orphelins**: {len(orphans)} documents n'ont pas de contenu généré.\n"
    report += f"2. **Checker manuellement**: Certains documents courts peuvent être intentionnels (intro courte, etc.).\n"
    report += f"3. **Supprimer ou régénérer**: Pour les vrais orphelins, relancer la génération ou supprimer le document.\n"
    report += f"\n**Script de suppression recommandé**: Utiliser `DELETE FROM documents WHERE id IN ({', '.join(str(d['id']) for d in orphans[:5])})...` avec vérification préalable.\n"

    return report

if __name__ == "__main__":
    print(f"🔍 Audit des documents vides dans {DB_PATH}...")
    results = audit_empty_documents()
    print(f"✅ {len(results)} documents avec contenu < 120 chars trouvés")

    report = generate_report(results)

    output_path = Path(__file__).parent.parent / "tasks" / "pdf-pipeline-refonte" / "empty-docs-audit.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    output_path.write_text(report)
    print(f"📄 Rapport écrit: {output_path}")

    # Afficher résumé
    orphans = [r for r in results if r['orphan']]
    print(f"\n📊 Résumé:")
    print(f"   Total vides: {len(results)}")
    print(f"   Orphelins: {len(orphans)}")
    print(f"   Avec contenu: {len(results) - len(orphans)}")
