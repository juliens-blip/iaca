#!/usr/bin/env python3
"""Audit quality of data/iaca.db and export markdown + CSV flags."""

from __future__ import annotations

import argparse
import csv
import re
import sqlite3
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB = REPO_ROOT / "data" / "iaca.db"
DEFAULT_REPORT = REPO_ROOT / "logs" / "p12_2_quality_report.md"
DEFAULT_FLAGS = REPO_ROOT / "logs" / "p12_2_quality_flags.csv"
SEVERITY_SCORE = {"critical": 100, "high": 60, "medium": 30, "low": 10}


@dataclass(slots=True)
class Doc:
    doc_id: int
    matiere: str
    titre: str
    text_len: int
    fc: int
    q: int
    f: int

    @property
    def full(self) -> bool:
        return self.fc > 0 and self.q > 0 and self.f > 0


@dataclass(slots=True)
class Flag:
    doc_id: int
    matiere: str
    titre: str
    issue_type: str
    severity: str
    details: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit content quality in iaca.db")
    parser.add_argument("--db-path", type=Path, default=DEFAULT_DB)
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--flags-path", type=Path, default=DEFAULT_FLAGS)
    return parser.parse_args()


def normalize_title(title: str) -> str:
    value = re.sub(r"\s+", " ", (title or "").lower()).strip()
    value = re.sub(r"\(\d+\)", "", value)
    return value.strip(" -_")


def duplicate_severity(size: int) -> str:
    if size >= 6:
        return "critical"
    if size >= 4:
        return "high"
    return "medium"


def load_docs(conn: sqlite3.Connection) -> list[Doc]:
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        SELECT
            d.id AS doc_id,
            COALESCE(m.nom, '(sans matiere)') AS matiere,
            d.titre AS titre,
            LENGTH(COALESCE(d.contenu_extrait, '')) AS text_len,
            COALESCE(fc.fc_count, 0) AS fc,
            COALESCE(q.q_count, 0) AS q,
            COALESCE(fi.f_count, 0) AS f
        FROM documents d
        LEFT JOIN matieres m ON m.id = d.matiere_id
        LEFT JOIN (
            SELECT document_id, COUNT(*) AS fc_count
            FROM flashcards WHERE document_id IS NOT NULL GROUP BY document_id
        ) fc ON fc.document_id = d.id
        LEFT JOIN (
            SELECT q.document_id, COUNT(qq.id) AS q_count
            FROM quizzes q
            LEFT JOIN quiz_questions qq ON qq.quiz_id = q.id
            WHERE q.document_id IS NOT NULL GROUP BY q.document_id
        ) q ON q.document_id = d.id
        LEFT JOIN (
            SELECT document_id, COUNT(*) AS f_count
            FROM fiches WHERE document_id IS NOT NULL GROUP BY document_id
        ) fi ON fi.document_id = d.id
        ORDER BY d.id
        """
    ).fetchall()
    return [
        Doc(
            doc_id=row["doc_id"],
            matiere=row["matiere"],
            titre=row["titre"],
            text_len=row["text_len"],
            fc=row["fc"],
            q=row["q"],
            f=row["f"],
        )
        for row in rows
    ]


def detect_duplicates(docs: list[Doc]) -> tuple[list[Flag], list[tuple[str, int, list[Doc]]]]:
    by_same: dict[tuple[str, str], list[Doc]] = defaultdict(list)
    by_title: dict[str, list[Doc]] = defaultdict(list)
    flags: list[Flag] = []
    clusters: list[tuple[str, int, list[Doc]]] = []

    for doc in docs:
        norm = normalize_title(doc.titre)
        by_same[(doc.matiere, norm)].append(doc)
        by_title[norm].append(doc)

    for (_, norm), group in by_same.items():
        if not norm or len(group) < 2:
            continue
        group = sorted(group, key=lambda d: d.doc_id)
        canonical = group[0].doc_id
        severity = duplicate_severity(len(group))
        clusters.append((norm, len(group), group))
        for doc in group[1:]:
            flags.append(
                Flag(
                    doc.doc_id,
                    doc.matiere,
                    doc.titre,
                    "duplicate_title_same_matiere",
                    severity,
                    f"normalized_title='{norm}',group_size={len(group)},canonical_doc_id={canonical}",
                )
            )

    for norm, group in by_title.items():
        if not norm or len(group) < 2:
            continue
        matieres = sorted({d.matiere for d in group})
        if len(matieres) < 2:
            continue
        group = sorted(group, key=lambda d: d.doc_id)
        canonical = group[0].doc_id
        severity = "high" if len(group) >= 4 else "medium"
        for doc in group[1:]:
            flags.append(
                Flag(
                    doc.doc_id,
                    doc.matiere,
                    doc.titre,
                    "duplicate_title_cross_matiere",
                    severity,
                    f"normalized_title='{norm}',group_size={len(group)},matieres={';'.join(matieres)},canonical_doc_id={canonical}",
                )
            )

    clusters.sort(key=lambda x: (-x[1], x[0]))
    return flags, clusters


def detect_short_content(docs: list[Doc]) -> list[Flag]:
    flags: list[Flag] = []
    for doc in docs:
        if doc.text_len == 0:
            issue_type, severity, details = "no_extracted_content", "critical", "text_length=0"
        elif doc.text_len < 80:
            issue_type, severity, details = "content_too_short", "high", f"text_length={doc.text_len}(<80)"
        elif doc.text_len < 200:
            issue_type, severity, details = "content_too_short", "medium", f"text_length={doc.text_len}(<200)"
        elif doc.text_len < 1000:
            issue_type, severity, details = "content_brief_for_generation", "low", f"text_length={doc.text_len}(<1000)"
        else:
            continue
        flags.append(Flag(doc.doc_id, doc.matiere, doc.titre, issue_type, severity, details))
    return flags


def compute_matiere_stats(docs: list[Doc]) -> dict[str, dict[str, float]]:
    stats: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    for doc in docs:
        s = stats[doc.matiere]
        s["total"] += 1
        if doc.text_len > 0:
            s["gt0"] += 1
        if doc.text_len > 200:
            s["gt200"] += 1
        if doc.text_len > 1000:
            s["gt1000"] += 1
        if doc.text_len > 200 and doc.full:
            s["full"] += 1

    for s in stats.values():
        total = int(s["total"])
        gt200 = int(s["gt200"])
        s["extractable_ratio"] = gt200 / total if total else 0.0
        s["deep_ratio"] = s["gt1000"] / total if total else 0.0
        s["full_ratio"] = s["full"] / gt200 if gt200 else 1.0
    return stats


def detect_matiere_coverage_issues(docs: list[Doc], stats: dict[str, dict[str, float]]) -> list[Flag]:
    by_matiere: dict[str, list[Doc]] = defaultdict(list)
    for doc in docs:
        by_matiere[doc.matiere].append(doc)

    flags: list[Flag] = []
    for matiere, s in stats.items():
        total = int(s["total"])
        if total < 5:
            continue
        extractable_ratio = s["extractable_ratio"]
        deep_ratio = s["deep_ratio"]
        full_ratio = s["full_ratio"]

        if extractable_ratio < 0.90:
            severity = "high" if extractable_ratio < 0.80 else "medium"
            for doc in by_matiere[matiere]:
                if doc.text_len <= 200:
                    flags.append(
                        Flag(
                            doc.doc_id,
                            doc.matiere,
                            doc.titre,
                            "matiere_low_extractable_ratio",
                            severity,
                            f"matiere_extractable_ratio={extractable_ratio:.2%},text_length={doc.text_len}",
                        )
                    )

        if deep_ratio < 0.85:
            severity = "medium" if deep_ratio < 0.70 else "low"
            for doc in by_matiere[matiere]:
                if 200 < doc.text_len <= 1000:
                    flags.append(
                        Flag(
                            doc.doc_id,
                            doc.matiere,
                            doc.titre,
                            "matiere_low_deep_ratio",
                            severity,
                            f"matiere_deep_ratio={deep_ratio:.2%},text_length={doc.text_len}",
                        )
                    )

        if full_ratio < 0.95:
            for doc in by_matiere[matiere]:
                if doc.text_len > 200 and not doc.full:
                    flags.append(
                        Flag(
                            doc.doc_id,
                            doc.matiere,
                            doc.titre,
                            "matiere_low_generation_coverage",
                            "high",
                            f"matiere_full_coverage_ratio={full_ratio:.2%},missing_fc={int(doc.fc == 0)},missing_q={int(doc.q == 0)},missing_f={int(doc.f == 0)}",
                        )
                    )
    return flags


def dedupe_and_sort_flags(flags: list[Flag]) -> list[Flag]:
    unique = {(f.doc_id, f.issue_type, f.details): f for f in flags}
    return sorted(unique.values(), key=lambda f: (-SEVERITY_SCORE[f.severity], f.issue_type, f.doc_id))


def build_top_docs_to_fix(docs: list[Doc], flags: list[Flag]) -> list[dict[str, str]]:
    docs_by_id = {doc.doc_id: doc for doc in docs}
    agg: dict[int, dict[str, object]] = defaultdict(lambda: {"score": 0, "types": Counter()})
    for flag in flags:
        agg[flag.doc_id]["score"] = int(agg[flag.doc_id]["score"]) + SEVERITY_SCORE[flag.severity]
        agg[flag.doc_id]["types"][flag.issue_type] += 1

    ranked = sorted(
        agg.items(),
        key=lambda item: (
            -int(item[1]["score"]),
            -sum(item[1]["types"].values()),
            docs_by_id[item[0]].text_len,
            item[0],
        ),
    )

    rows: list[dict[str, str]] = []
    for doc_id, payload in ranked[:10]:
        doc = docs_by_id[doc_id]
        rows.append(
            {
                "doc_id": str(doc.doc_id),
                "matiere": doc.matiere,
                "titre": doc.titre,
                "text_len": str(doc.text_len),
                "score": str(payload["score"]),
                "issues": ", ".join(sorted(payload["types"].keys())),
            }
        )
    return rows


def write_flags_csv(path: Path, flags: list[Flag]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["doc_id", "matiere", "titre", "issue_type", "severity", "details"],
        )
        writer.writeheader()
        for flag in flags:
            writer.writerow(
                {
                    "doc_id": flag.doc_id,
                    "matiere": flag.matiere,
                    "titre": flag.titre,
                    "issue_type": flag.issue_type,
                    "severity": flag.severity,
                    "details": flag.details,
                }
            )


def write_report(
    path: Path,
    docs: list[Doc],
    flags: list[Flag],
    clusters: list[tuple[str, int, list[Doc]]],
    matiere_stats: dict[str, dict[str, float]],
    top_docs: list[dict[str, str]],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    severity_counts = Counter(f.severity for f in flags)
    issue_counts = Counter(f.issue_type for f in flags)
    docs_gt200 = sum(1 for d in docs if d.text_len > 200)
    docs_full = sum(1 for d in docs if d.text_len > 200 and d.full)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    lines = [
        "# P12-2 Content Quality Audit Report",
        "",
        f"Generated at: {stamp}",
        "",
        "## Global Summary",
        "",
        f"- Total documents: **{len(docs)}**",
        f"- Docs with extractable text (>200): **{docs_gt200}**",
        f"- Full generated coverage on extractable docs: **{docs_full}/{docs_gt200}**",
        f"- Total quality flags: **{len(flags)}**",
        "",
        "### Flags by severity",
        "",
        "| Severity | Count |",
        "|---|---:|",
    ]
    for sev in ("critical", "high", "medium", "low"):
        lines.append(f"| {sev} | {severity_counts.get(sev, 0)} |")

    lines += ["", "### Top issue types", "", "| Issue type | Count |", "|---|---:|"]
    for issue_type, count in issue_counts.most_common(12):
        lines.append(f"| {issue_type} | {count} |")

    lines += [
        "",
        "## Per-Matiere Coverage",
        "",
        "| Matiere | Total docs | >200 chars | >1000 chars | Full coverage ratio (>200) | Extractable ratio | Deep ratio |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for matiere, s in sorted(matiere_stats.items(), key=lambda item: (item[1]["extractable_ratio"], item[0])):
        lines.append(
            f"| {matiere} | {int(s['total'])} | {int(s['gt200'])} | {int(s['gt1000'])} | "
            f"{s['full_ratio']:.2%} | {s['extractable_ratio']:.2%} | {s['deep_ratio']:.2%} |"
        )

    lines += ["", "## Largest Duplicate Clusters (same matiere)", "", "| Normalized title | Cluster size | Sample doc_ids |", "|---|---:|---|"]
    for norm, size, group in clusters[:15]:
        sample_ids = ", ".join(str(d.doc_id) for d in group[:4])
        lines.append(f"| {norm} | {size} | {sample_ids} |")

    lines += ["", "## Top 10 Docs to Fix", "", "| Rank | doc_id | matiere | text_len | score | issue types | titre |", "|---:|---:|---|---:|---:|---|---|"]
    for idx, row in enumerate(top_docs, 1):
        lines.append(
            f"| {idx} | {row['doc_id']} | {row['matiere']} | {row['text_len']} | {row['score']} | "
            f"{row['issues']} | {row['titre'].replace('|', '/')} |"
        )

    lines += [
        "",
        "## Thresholds Used",
        "",
        "- Short content: critical=0, high<80, medium<200, low<1000 chars.",
        "- Low matiere extractable ratio: <90% (high if <80%).",
        "- Low matiere deep ratio: <85% (medium if <70%, else low).",
        "- Duplicate severity by cluster size: >=6 critical, >=4 high, else medium.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    with sqlite3.connect(args.db_path) as conn:
        docs = load_docs(conn)

    dup_flags, dup_clusters = detect_duplicates(docs)
    short_flags = detect_short_content(docs)
    matiere_stats = compute_matiere_stats(docs)
    coverage_flags = detect_matiere_coverage_issues(docs, matiere_stats)
    flags = dedupe_and_sort_flags(dup_flags + short_flags + coverage_flags)
    top_docs = build_top_docs_to_fix(docs, flags)

    write_flags_csv(args.flags_path, flags)
    write_report(args.report_path, docs, flags, dup_clusters, matiere_stats, top_docs)

    severity_counts = Counter(f.severity for f in flags)
    print(f"Quality audit completed: {len(flags)} flags")
    print("Severity counts:")
    for sev in ("critical", "high", "medium", "low"):
        print(f"  {sev}: {severity_counts.get(sev, 0)}")
    print("Top 10 docs to fix:")
    for idx, row in enumerate(top_docs, 1):
        print(f"  {idx:2d}. doc_id={row['doc_id']} score={row['score']} matiere={row['matiere']} titre={row['titre'][:100]}")
    print(f"Report: {args.report_path}")
    print(f"Flags : {args.flags_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
