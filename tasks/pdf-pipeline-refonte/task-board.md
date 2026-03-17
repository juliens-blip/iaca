# PDF Pipeline Refonte — Task Board

**Objectif**: Remplacer l'extraction brute (pymupdf) par marker (markdown structuré), ajouter chunking intelligent, et regénérer fiches+flashcards de qualité sur tous les PDFs.

**Session**: iaca-orchestration | **Date**: 2026-03-17

## Task Assignment Queue

| ID | Tâche | Worker | Status | Acceptance |
|---|---|---|---|---|
| T-001 | Installer marker dans backend/.venv | w0 (bash) | COMPLETED | MARKER OK |
| T-002 | marker_parser.py — parser PDF marker → markdown | w3 (Sonnet) | COMPLETED | compileall OK |
| T-003 | claude_service.py — chunking + prompts reformulation | w5 (Codex) | COMPLETED | +117 lignes, compileall OK |
| T-004 | scripts/reextract_and_generate.py — batch | w8 (Opus) | COMPLETED | --help OK, dry-run OK |
| T-005 | Compilation backend complète | w2 (Haiku) | COMPLETED | compileall OK |
| T-006 | backend/.venv + marker editable install + validation import | Codex | DONE | MARKER OK |
| T-007 | Lister les PDFs de docs/ non en DB | w2 (Haiku) | COMPLETED | missing-pdfs.md généré |
| T-008 | Audit qualité des fiches existantes dans `data/iaca.db` | w5 (Codex) | COMPLETED | `quality-audit.md` rédigé, échantillon 20 fiches audité |
| T-009 | Endpoint POST /api/documents/{id}/reextract | Amp | COMPLETED | compileall OK |
| T-013 | Audit qualité section-level des fiches existantes dans `data/iaca.db` | w5 (Codex) | COMPLETED | `quality-audit.md` mis à jour sur 40 sections aléatoires |
| T-014 | Valider et corriger scripts/reextract_and_generate.py | Amp | COMPLETED | --help OK + --dry-run --limit 2 exit 0 |
| T-018 | Validation qualite post-generation dans claude_service.py | Amp | COMPLETED | compileall exit 0 |
| T-020 | Script d'import des PDFs manquants depuis `docs/` | w5 (Codex) | COMPLETED | `import_missing_pdfs.py` cree, `--dry-run --limit 3` OK |
| T-022 | Verification finale compilation + coherence backend | w2 (Haiku) | COMPLETED | compileall OK, 3 zones vérifiées |
| T-023 | generer_qcm() — prompt reformulation (chunking déjà présent) | Amp | COMPLETED | compileall exit 0 |
| T-011 | Review code T-002 + T-003 | w2 (Haiku) | COMPLETED | 3 bugs fixés, compileall OK |
| T-012 | scripts/test_pdf_pipeline.py — test e2e pipeline | Sonnet | COMPLETED | --help OK |
| T-016 | Améliorer fallback fitz pour markdown structuré | w2 (Haiku) | COMPLETED | Titres détectés, markdown généré, compileall OK |
| T-017 | scripts/identify_regen_targets.py — scoring docs à régénérer | Sonnet | COMPLETED | --limit 10 OK, stats affichées |
| T-021 | Exécuter identify_regen_targets et sauver résultats | Sonnet | COMPLETED | regen-priorities.md créé |
| T-025 | Dry-run batch script avec marker actif | Sonnet | COMPLETED | 5 docs traités, 0 erreur |
| T-026 | Executer test_pdf_pipeline.py sur 2 vrais PDFs | w2 (Haiku) | COMPLETED | 2 PDFs testés, résultats écrits |

## Metrics actuelles
- PDFs en DB: 688, dont 182 sans extraction exploitable
- 641 docs sans fiche, 418 sans flashcard
- Troncation actuelle: 8000 chars (seul le début du doc sert)

## Task Completion Log

| Timestamp | Worker | Task | Result |
|---|---|---|---|
| 2026-03-17 | Amp (T-003) | chunk_content() + generer_flashcards() chunked + generer_fiche() chunked + prompts reformulation | OK — compileall exit 0 |
| 2026-03-17 | Sonnet (T-002) | marker_parser.py: parse_pdf_with_marker() + _clean_markdown() + fallback fitz; document_parser.py: PDF route → _extract_pdf_async() | OK — compileall exit 0 |
| 2026-03-17 | Haiku (T-005) | Vérification compilation backend — marker_parser.py, claude_service.py, document_parser.py cohérence imports | OK — compileall exit 0, no errors |
| 2026-03-17 | Codex (T-006) | backend/.venv créé; `pip install -r backend/requirements.txt`; `pip install -e marker/`; alignement `torch 2.10.0+cpu` + `triton 3.3.0`; import `PdfConverter` validé | DONE — MARKER OK |
| 2026-03-17 | Amp (T-009) | POST /{document_id}/reextract: marker pour PDF, parse_document sinon; retourne chars_avant/chars_apres | OK — compileall exit 0 |
| 2026-03-17 | Amp (T-014) | Fix bug params SQL inversés dans fetch_docs_with_few_flashcards; --help OK; --dry-run --limit 2 exit 0 | OK |
| 2026-03-17 | Amp (T-018) | _validate_flashcard + _validate_fiche_section (difflib ratio>0.85) + regen si <50% / 0 sections valides | OK — compileall exit 0 |
| 2026-03-17 | Sonnet (T-004) | reextract_and_generate.py: 3 phases (extract/fiches/flashcards), sqlite3 direct, --dry-run/--limit/--matiere/--skip-* | OK — --help exit 0 |
| 2026-03-17 | Haiku (T-007) | Comparaison PDFs physiques docs/ (150) vs DB (688 docs, 0 match) → missing-pdfs.md | OK — 150 PDFs manquants listés |
| 2026-03-17 | Codex (T-008) | Audit manuel de 20 fiches dans `data/iaca.db`, rapport qualité et recommandations | OK — `quality-audit.md` créé, T-008 marqué COMPLETED |
| 2026-03-17 | Haiku (T-011) | Review marker_parser.py, claude_service.py, document_parser.py — 3 bugs fixés: generer_qcm chunking, PPTX/DOCX async, marker loop optimization | OK — compileall exit 0 |
| 2026-03-17 | Sonnet (T-012) | test_pdf_pipeline.py: extraction marker + chunking + stats (chars/sections/chunks), --generate pour IA | OK — --help exit 0 |
| 2026-03-17 | Codex (T-013) | Audit manuel de 40 sections aléatoires dans `data/iaca.db`, métriques section-level et exemples good/bad | OK — `quality-audit.md` mis à jour, T-013 marqué COMPLETED |
| 2026-03-17 | Haiku (T-016) | Amélioration _fallback_fitz(): détection titres (font size), conversion markdown (##/###), nettoyage artefacts, préservation listes | OK — compileall exit 0, fallback markdown structuré |
| 2026-03-17 | Codex (T-020) | `import_missing_pdfs.py`: mapping des 5 dossiers `docs/` -> `matieres.id`, dedup par titre, copie vers `data/uploads`, parse via `parse_document`, insert sqlite direct, `--dry-run/--matiere/--limit` | OK — `python3 scripts/import_missing_pdfs.py --dry-run --limit 3` exit 0, 0 candidat restant |
| 2026-03-17 | Haiku (T-022) | Verification finale: compilation backend OK, validation _validate_flashcard/_validate_fiche_section, reextract endpoint, _fallback_fitz coherence | OK — compileall exit 0, 0 warning logique |
| 2026-03-17 | Haiku (T-026) | Test fallback fitz + chunking sur Inflation et déflation_.pdf (19KB MD, 6 chunks) et ADM 2.pdf (78KB MD, 20 chunks) → test-pipeline-results.md | OK — 2 PDFs validés, extraction/chunking optimal |
