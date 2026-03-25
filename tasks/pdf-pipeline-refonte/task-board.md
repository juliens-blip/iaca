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
| T-027 | Réécrire prompt flashcards — qualité pédagogique | w3 (Opus) | COMPLETED | Prompt détaillé avec exemples BON/MAUVAIS, échelle difficulté |
| T-028 | Réécrire prompt fiche — qualité pédagogique + titre LLM | w3 (Opus) | COMPLETED | 4 éléments obligatoires par section, titre_fiche dynamique |
| T-029 | Réécrire prompt QCM — cas pratiques | w3 (Opus) | COMPLETED | Mises en situation, choix plausibles, explication correcte+faux |
| T-030 | Review prompts flashcards+QCM | w2 (Sonnet) | COMPLETED | JSON valide, cohérence pédagogique OK |
| T-030b | Review prompt fiche + compileall | w5 (Codex) | COMPLETED | JSON correct, compilation OK |
| T-031 | Review validation difflib | w1 (Haiku) | COMPLETED | Seuil 0.85 efficace, rejet copies confirmé |
| T-032 | Script test_new_prompts.py | w2 (Sonnet) | COMPLETED | --help OK, --dry-run OK |
| T-033 | Review batch script reextract | w1 (Haiku) | COMPLETED | batch-integration-review.md écrit |
| T-036 | Review intégration Phase 2 + Phase 3 batch | w2 (Haiku) | COMPLETED | batch-integration-review.md généré |
| T-034 | Check run_claude_cli config | w0 (Codex GPT) | COMPLETED | — |
| T-029 | Revue des prompts Claude (flashcards + QCM) | w2 (Haiku) | COMPLETED | Compilation OK, JSON cohérent, rapport écrit |
| T-037 | Diagnostic bug CLI stderr vide | w5 (AMP) | COMPLETED | Rate-limit identifié, cli-diagnostic.md écrit |
| T-038 | Stats génération par matière | w3 (Sonnet) | COMPLETED | generation-status.md: 590 sans fiche, 405 <5 FC |
| T-039 | Audit contenu L2S3 | w2 (Haiku) | COMPLETED | 46/257 docs vides, 211 exploitables |
| T-040 | Git prep | w8 (Claude) | BLOCKED | API 404, worker hors service |
| T-041 | Fix env stripping anthropic/mcp | w3 (Sonnet) | COMPLETED | Appliqué dans claude_service.py |
| T-042 | Git prep (reprise) | w2 (Haiku) | COMPLETED | git-prep.md écrit |
| T-043 | Code review fix rate-limit | w3 (Opus) + `code-reviewer` | IN_PROGRESS | — |
| T-044 | Test batch 3 docs avec fix | w5 (AMP) + `backend-architect` | IN_PROGRESS | — |
| T-045 | Validation compilation + pre-commit | w2 (Sonnet) + `agent_controle` | IN_PROGRESS | — |

## Metrics actuelles (2026-03-25)
- Docs en DB: 1614, dont 341 à contenu court (<120 chars)
- 590 docs sans fiche, 405 docs avec <5 flashcards
- Priorités: L2-S3 (138), Droit public (133), L2-S4 (88)
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
| 2026-03-18 | Haiku (T-029) | Revue prompts Flashcards (L.390-432) et QCM (L.465-503): JSON format validation, exemples bon/mauvais, cohérence pédagogique → prompt-review-sonnet.md | OK — compileall exit 0, prompts validés pour production |
| 2026-03-18 | Sonnet (T-032) | `scripts/test_new_prompts.py`: récupère doc aléatoire de DB (> 1000 chars), appelle generer_flashcards/generer_fiche, affiche JSON indent; --limit 1, --dry-run OK | OK — compile OK, --help OK, --dry-run affiche doc sans appel Claude |
| 2026-03-18 | Haiku (T-036) | Review Phase 2/3 du batch: generer_fiche(contenu, matiere, titre) L.239, generer_flashcards(contenu, matiere, nb=10) L.276, matiere via LEFT JOIN+fallback, chunking délégué interne | OK — batch-integration-review.md, intégration validée |
