#!/usr/bin/env python3
"""
Identifie et classe les documents à régénérer en priorité.

Usage:
  python3 scripts/identify_regen_targets.py [options]

Options:
  --limit N     Affiche les N premiers résultats (défaut: tous)
  --export CSV  Exporte les résultats dans un fichier CSV
  --matiere NOM Filtre sur le nom de la matière (insensible à la casse)
  --min-score N Affiche uniquement les docs avec score >= N
"""

import argparse
import csv
import sqlite3
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = REPO_ROOT / "data" / "iaca.db"


def open_db() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def compute_scores(conn: sqlite3.Connection, matiere_filter: str | None) -> list[dict]:
    sql = """
        SELECT
            d.id,
            d.titre,
            d.contenu_extrait,
            d.matiere_id,
            m.nom AS matiere_nom,
            COUNT(DISTINCT fc.id) AS nb_flashcards,
            COUNT(DISTINCT f.id)  AS nb_fiches,
            MIN(f.titre)          AS fiche_titre
        FROM documents d
        LEFT JOIN matieres m    ON m.id = d.matiere_id
        LEFT JOIN flashcards fc ON fc.document_id = d.id
        LEFT JOIN fiches f      ON f.document_id = d.id
    """
    params: list = []
    if matiere_filter:
        sql += " WHERE lower(m.nom) LIKE ?"
        params.append(f"%{matiere_filter.lower()}%")
    sql += " GROUP BY d.id ORDER BY d.id"

    rows = conn.execute(sql, params).fetchall()
    results: list[dict] = []

    for row in rows:
        score = 0
        raisons: list[str] = []

        contenu = (row["contenu_extrait"] or "").strip()
        if len(contenu) < 200:
            score += 10
            raisons.append("contenu vide/court (<200 chars)")

        if row["nb_fiches"] == 0:
            score += 5
            raisons.append("aucune fiche")

        if row["nb_flashcards"] == 0:
            score += 3
            raisons.append("aucune flashcard")
        elif row["nb_flashcards"] < 10:
            score += 1
            raisons.append(f"peu de flashcards ({row['nb_flashcards']})")

        fiche_titre = row["fiche_titre"] or ""
        titre_doc = (row["titre"] or "").strip()
        if fiche_titre and (
            fiche_titre.startswith("Fiche -")
            and titre_doc
            and titre_doc in fiche_titre
        ):
            score += 2
            raisons.append("titre de fiche générique")

        results.append({
            "id": row["id"],
            "titre": titre_doc,
            "matiere": row["matiere_nom"] or "",
            "nb_flashcards": row["nb_flashcards"],
            "nb_fiches": row["nb_fiches"],
            "score": score,
            "raisons": ", ".join(raisons) if raisons else "—",
        })

    results.sort(key=lambda x: x["score"], reverse=True)
    return results


def print_table(rows: list[dict]) -> None:
    if not rows:
        print("Aucun document trouvé.")
        return

    col_id    = max(len("ID"),    max(len(str(r["id"]))    for r in rows))
    col_titre = min(50, max(len("Titre"), max(len(r["titre"][:50]) for r in rows)))
    col_mat   = min(30, max(len("Matière"), max(len(r["matiere"][:30]) for r in rows)))
    col_score = max(len("Score"), max(len(str(r["score"])) for r in rows))
    col_fc    = max(len("FC"),    max(len(str(r["nb_flashcards"])) for r in rows))
    col_fi    = max(len("Fi"),    max(len(str(r["nb_fiches"])) for r in rows))

    header = (
        f"{'ID':<{col_id}}  "
        f"{'Titre':<{col_titre}}  "
        f"{'Matière':<{col_mat}}  "
        f"{'Score':>{col_score}}  "
        f"{'FC':>{col_fc}}  "
        f"{'Fi':>{col_fi}}  "
        f"Raisons"
    )
    sep = "-" * len(header)
    print(header)
    print(sep)

    for r in rows:
        titre_trunc = r["titre"][:col_titre]
        mat_trunc   = r["matiere"][:col_mat]
        print(
            f"{r['id']:<{col_id}}  "
            f"{titre_trunc:<{col_titre}}  "
            f"{mat_trunc:<{col_mat}}  "
            f"{r['score']:>{col_score}}  "
            f"{r['nb_flashcards']:>{col_fc}}  "
            f"{r['nb_fiches']:>{col_fi}}  "
            f"{r['raisons']}"
        )


def export_csv(rows: list[dict], path: str) -> None:
    fields = ["id", "titre", "matiere", "score", "nb_flashcards", "nb_fiches", "raisons"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for r in rows:
            writer.writerow({k: r[k] for k in fields})
    print(f"\nExport CSV: {path} ({len(rows)} lignes)")


def print_stats(all_rows: list[dict]) -> None:
    total = len(all_rows)
    if total == 0:
        return
    needs_extract  = sum(1 for r in all_rows if "contenu vide/court" in r["raisons"])
    needs_fiche    = sum(1 for r in all_rows if "aucune fiche" in r["raisons"])
    needs_fc       = sum(1 for r in all_rows if "aucune flashcard" in r["raisons"])
    generic_fiche  = sum(1 for r in all_rows if "titre de fiche générique" in r["raisons"])
    score_zero     = sum(1 for r in all_rows if r["score"] == 0)

    print(f"\n{'='*60}")
    print(f"STATS GLOBALES ({total} documents au total)")
    print(f"{'='*60}")
    print(f"  Contenu vide/court (<200 chars) : {needs_extract:>5}")
    print(f"  Sans fiche                      : {needs_fiche:>5}")
    print(f"  Sans flashcard                  : {needs_fc:>5}")
    print(f"  Fiche à titre générique         : {generic_fiche:>5}")
    print(f"  Score zéro (rien à faire)       : {score_zero:>5}")

    score_gt0 = [r["score"] for r in all_rows if r["score"] > 0]
    if score_gt0:
        print(f"  Docs avec score > 0             : {len(score_gt0):>5}")
        print(f"  Score moyen (docs > 0)          : {sum(score_gt0)/len(score_gt0):>8.1f}")
        print(f"  Score max                       : {max(score_gt0):>5}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Identifie et classe les documents à régénérer en priorité."
    )
    parser.add_argument("--limit",     type=int,   default=None,  metavar="N",   help="Limite le nombre de résultats affichés")
    parser.add_argument("--export",    type=str,   default=None,  metavar="CSV", help="Exporte les résultats dans un fichier CSV")
    parser.add_argument("--matiere",   type=str,   default=None,  metavar="NOM", help="Filtre sur le nom de la matière")
    parser.add_argument("--min-score", type=int,   default=0,     metavar="N",   help="Score minimum pour afficher un doc (défaut: 0)")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if not DB_PATH.exists():
        print(f"Base de données introuvable: {DB_PATH}", file=sys.stderr)
        sys.exit(1)

    conn = open_db()
    all_rows = compute_scores(conn, args.matiere)
    conn.close()

    # Filtrer par score minimum
    filtered = [r for r in all_rows if r["score"] >= args.min_score]

    # Afficher
    display = filtered[: args.limit] if args.limit else filtered
    print_table(display)

    # Export CSV (sur l'ensemble filtré, pas seulement les N affichés)
    if args.export:
        export_csv(filtered, args.export)

    # Stats globales (toujours sur tous les docs)
    print_stats(all_rows)


if __name__ == "__main__":
    main()
