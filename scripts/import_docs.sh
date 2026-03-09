#!/usr/bin/env bash
set -uo pipefail

BASE_URL="${BASE_URL:-http://localhost:8000}"
DOCS_ROOT="${1:-docs}"

if ! command -v curl >/dev/null 2>&1; then
  echo "Erreur: curl est requis." >&2
  exit 1
fi

if [[ ! -d "${DOCS_ROOT}" ]]; then
  echo "Erreur: dossier introuvable: ${DOCS_ROOT}" >&2
  exit 1
fi

uploaded=0
failed=0

while IFS= read -r -d '' file_path; do
  relative_path="${file_path#${DOCS_ROOT}/}"
  matiere_slug="${relative_path%%/*}"
  chapter_path="$(dirname "${relative_path}")"
  if [[ "${chapter_path}" == "." ]]; then
    chapter_path=""
  fi

  # Map folder name to matiere_id
  matiere_id=""
  case "${matiere_slug}" in
    droit-public) matiere_id=1 ;;
    economie-finances-publiques) matiere_id=2 ;;
    questions-contemporaines) matiere_id=3 ;;
    questions-sociales) matiere_id=4 ;;
    relations-internationales) matiere_id=5 ;;
  esac

  curl_args=(-sS -X POST "${BASE_URL}/api/documents/upload"
    -F "file=@${file_path}"
    -F "chapitre=${chapter_path}"
    -F "tags=${matiere_slug}")
  if [[ -n "${matiere_id}" ]]; then
    curl_args+=(-F "matiere_id=${matiere_id}")
  fi

  payload_and_status="$(
    curl "${curl_args[@]}" -w $'\nHTTP_STATUS:%{http_code}\n'
  )"

  status_code="$(printf '%s' "${payload_and_status}" | awk -F: '/HTTP_STATUS/{print $2}' | tail -n1)"
  response_body="$(printf '%s' "${payload_and_status}" | sed '/^HTTP_STATUS:/d')"

  if [[ "${status_code}" =~ ^2[0-9][0-9]$ ]]; then
    uploaded=$((uploaded + 1))
    echo "[OK] ${file_path}"
  else
    failed=$((failed + 1))
    echo "[KO] ${file_path} (HTTP ${status_code})" >&2
    echo "${response_body}" >&2
  fi
done < <(
  find "${DOCS_ROOT}" -mindepth 2 -type f \
    \( -iname '*.pdf' -o -iname '*.pptx' -o -iname '*.docx' \) \
    -print0 | sort -z
)

echo "Import terminé: ${uploaded} uploadés, ${failed} en échec."

