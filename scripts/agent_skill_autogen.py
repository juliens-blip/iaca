#!/usr/bin/env python3
"""
Generate agent skills automatically from new entries in probleme.Md.

Usage:
  ./scripts/agent_skill_autogen.py run
  ./scripts/agent_skill_autogen.py watch --interval 5
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import time
import unicodedata
from dataclasses import dataclass
from pathlib import Path


SKIP_AGENT_FILES = {"README.md", "agents_supreme.md", "agent_controle.md"}
IGNORED_PROBLEM_TITLES = {
    "format",
    "historique",
    "problemes rencontres",
    "problemes rencontres pendant l execution des taches",
}
STOP_WORDS = {
    "a",
    "an",
    "and",
    "au",
    "aux",
    "avec",
    "ce",
    "cet",
    "cette",
    "comment",
    "dans",
    "de",
    "des",
    "du",
    "en",
    "est",
    "et",
    "for",
    "how",
    "il",
    "la",
    "le",
    "les",
    "mais",
    "or",
    "ou",
    "par",
    "pour",
    "que",
    "qui",
    "se",
    "sur",
    "the",
    "to",
    "un",
    "une",
}

AGENT_HINTS = {
    "backend-architect": "api backend database microservice schema scalability performance",
    "code-reviewer": "review quality maintainability security",
    "content-marketer": "marketing content campaign blog social seo",
    "context-manager": "context memory handoff sync",
    "debugger": "debug bug stacktrace crash error",
    "explore-code": "search code exploration architecture",
    "explore-style": "style conventions lint formatting",
    "frontend-developer": "ui ux react css html frontend",
    "fullstack-developer": "frontend backend integration end-to-end",
    "legal-advisor": "legal terms privacy policy gdpr compliance",
    "mcp-creator": "mcp server tool creation",
    "mcp-doctor": "mcp diagnostic troubleshooting fix",
    "mcp-expert": "mcp config integration setup",
    "mcp-server-architect": "mcp architecture design scaling",
    "mcp-testing-engineer": "mcp tests validation",
    "prompt-engineer": "prompt llm instruction specification",
    "seo-analyzer": "seo audit indexing metadata",
    "seo-podcast-optimizer": "podcast seo discoverability",
    "test-code": "tests unit integration regression",
    "test-engineer": "qa unit integration e2e",
    "ui-ux-designer": "design ux ui accessibility wireframe",
    "video-editor": "video ffmpeg editing montage",
    "epct": "reasoning thinking analysis",
    "moana-epct": "reasoning planning analysis",
    "universal-orchestrator": "orchestrate agents workflow coordination",
    "apex-workflow": "workflow analysis planning implementation",
}

SUB_AGENT_MAP = {
    "backend-architect": "explore-code",
    "code-reviewer": "test-engineer",
    "content-marketer": "seo-analyzer",
    "context-manager": "universal-orchestrator",
    "debugger": "test-code",
    "explore-code": "debugger",
    "explore-style": "code-reviewer",
    "frontend-developer": "ui-ux-designer",
    "fullstack-developer": "backend-architect",
    "mcp-creator": "mcp-testing-engineer",
    "mcp-doctor": "mcp-expert",
    "mcp-expert": "mcp-doctor",
    "mcp-server-architect": "mcp-testing-engineer",
    "prompt-engineer": "context-manager",
    "seo-analyzer": "content-marketer",
    "test-code": "debugger",
    "test-engineer": "debugger",
    "ui-ux-designer": "frontend-developer",
}

AGENT_ALIASES = {
    "agent-orchestrator-universal": "universal-orchestrator",
    "agent-orchestrator-uniersal": "universal-orchestrator",
    "orchestrator-universal": "universal-orchestrator",
}


@dataclass(frozen=True)
class AgentSpec:
    name: str
    file_path: Path
    skills_dir: Path
    description: str
    keywords: set[str]


@dataclass(frozen=True)
class Problem:
    problem_id: str
    title: str
    content: str


def normalize_text(value: str) -> str:
    stripped = unicodedata.normalize("NFKD", value)
    ascii_only = stripped.encode("ascii", "ignore").decode("ascii")
    return ascii_only.lower()


def tokenize(value: str) -> set[str]:
    normalized = normalize_text(value)
    words = re.findall(r"[a-z0-9]+", normalized)
    return {word for word in words if len(word) > 2 and word not in STOP_WORDS}


def slugify(value: str, max_length: int = 48) -> str:
    normalized = normalize_text(value)
    normalized = re.sub(r"[^a-z0-9]+", "-", normalized)
    normalized = normalized.strip("-")
    if not normalized:
        normalized = "probleme"
    return normalized[:max_length].rstrip("-")


def normalize_agent_identifier(value: str) -> str:
    normalized = normalize_text(value)
    normalized = re.sub(r"[^a-z0-9\-]", "-", normalized)
    normalized = re.sub(r"-{2,}", "-", normalized).strip("-")
    return AGENT_ALIASES.get(normalized, normalized)


def read_frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---"):
        return {}
    match = re.match(r"^---\n(.*?)\n---\n?", text, re.DOTALL)
    if not match:
        return {}
    metadata: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip().strip("'").strip('"')
    return metadata


def load_agents(agents_dir: Path) -> list[AgentSpec]:
    if not agents_dir.exists():
        raise FileNotFoundError(f"Agents directory not found: {agents_dir}")

    candidate_files: list[Path] = []
    candidate_files.extend(sorted(agents_dir.glob("*.md")))
    nested_orchestrator = agents_dir / "agent-orchestrator-universal" / "universal-orchestrator.md"
    if nested_orchestrator.exists():
        candidate_files.append(nested_orchestrator)

    agents_by_name: dict[str, AgentSpec] = {}
    for file_path in candidate_files:
        if file_path.name in SKIP_AGENT_FILES:
            continue
        text = file_path.read_text(encoding="utf-8")
        metadata = read_frontmatter(text)
        if not metadata:
            continue
        agent_name = normalize_agent_identifier(metadata.get("name", file_path.stem))
        description = metadata.get("description", "")
        hints = AGENT_HINTS.get(agent_name, "")
        keywords = tokenize(f"{agent_name} {description} {hints}")
        if file_path.parent == agents_dir:
            skills_dir = agents_dir / agent_name / "skills"
        else:
            skills_dir = file_path.parent / "skills"

        new_spec = AgentSpec(
            name=agent_name,
            file_path=file_path,
            skills_dir=skills_dir,
            description=description,
            keywords=keywords,
        )

        current = agents_by_name.get(agent_name)
        if current is None:
            agents_by_name[agent_name] = new_spec
            continue

        current_is_redirect = "redirect" in current.description.lower()
        new_is_redirect = "redirect" in new_spec.description.lower()
        if current_is_redirect and not new_is_redirect:
            agents_by_name[agent_name] = new_spec
            continue
        if current.file_path.parent == agents_dir and new_spec.file_path.parent != agents_dir:
            agents_by_name[agent_name] = new_spec

    agents = sorted(agents_by_name.values(), key=lambda item: item.name)
    if not agents:
        raise RuntimeError(f"No agent specs found in {agents_dir}")
    return agents


def parse_heading_blocks(text: str) -> list[Problem]:
    heading_entries: list[tuple[str, int, int]] = []
    in_code_fence = False
    cursor = 0

    for line in text.splitlines(keepends=True):
        stripped = line.lstrip()
        if stripped.startswith("```"):
            in_code_fence = not in_code_fence
        if not in_code_fence:
            match = re.match(r"^(#{2,6})\s+(.+)$", line.rstrip("\n"))
            if match:
                title = match.group(2).strip()
                heading_start = cursor
                heading_end = cursor + len(line)
                heading_entries.append((title, heading_start, heading_end))
        cursor += len(line)

    if not heading_entries:
        return []

    blocks: list[Problem] = []
    for index, (title, _, block_start) in enumerate(heading_entries):
        block_end = heading_entries[index + 1][1] if index + 1 < len(heading_entries) else len(text)
        body = text[block_start:block_end].strip()
        raw = f"{title}\n{body}".strip()
        if not raw:
            continue
        normalized_title = normalize_text(title)
        normalized_body = normalize_text(body)
        if normalized_title in IGNORED_PROBLEM_TITLES:
            continue
        if "aucun probleme" in normalized_body:
            continue
        if "```" in body and "probleme:" not in normalized_body:
            continue
        problem_id = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]
        blocks.append(Problem(problem_id=problem_id, title=title, content=raw))
    return blocks


def parse_paragraph_blocks(text: str) -> list[Problem]:
    blocks: list[Problem] = []
    for paragraph in re.split(r"\n\s*\n", text):
        cleaned = paragraph.strip()
        if not cleaned:
            continue
        if cleaned.startswith("#"):
            continue
        first_line = cleaned.splitlines()[0]
        title = re.sub(r"^[\-\*\s]+", "", first_line).strip()
        if not title:
            title = "Probleme sans titre"
        problem_id = hashlib.sha1(cleaned.encode("utf-8")).hexdigest()[:12]
        blocks.append(Problem(problem_id=problem_id, title=title, content=cleaned))
    return blocks


def parse_problems(problems_file: Path) -> list[Problem]:
    if not problems_file.exists():
        return []
    text = problems_file.read_text(encoding="utf-8")
    if not text.strip():
        return []
    has_heading_outside_code = False
    in_code_fence = False
    for line in text.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("```"):
            in_code_fence = not in_code_fence
        if not in_code_fence and re.match(r"^#{2,6}\s+", stripped):
            has_heading_outside_code = True
            break
    heading_blocks = parse_heading_blocks(text)
    if has_heading_outside_code:
        return heading_blocks
    return parse_paragraph_blocks(text)


def parse_explicit_agents(problem_text: str) -> list[str]:
    lines = problem_text.splitlines()
    for line in lines:
        marker_match = re.search(r"(?:@agents?|agents?)\s*:\s*(.+)$", line, re.IGNORECASE)
        if not marker_match:
            continue
        raw_names = marker_match.group(1)
        names: list[str] = []
        for item in re.split(r"[,\s]+", raw_names):
            normalized = normalize_agent_identifier(item.strip())
            if normalized:
                names.append(normalized)
        return names
    by_handles: list[str] = []
    for handle in re.findall(r"@([a-z0-9\-]+)", problem_text.lower()):
        normalized = normalize_agent_identifier(handle)
        if normalized and normalized not in by_handles:
            by_handles.append(normalized)
    if by_handles:
        return by_handles
    return []


def parse_context_agents(agent_context_file: Path, agents: list[AgentSpec]) -> list[str]:
    if not agent_context_file.exists():
        return []

    raw_text = agent_context_file.read_text(encoding="utf-8")
    if not raw_text.strip():
        return []

    by_name = {agent.name.lower(): agent for agent in agents}
    selected: list[str] = []

    # Preferred format:
    #   agent: backend-architect
    #   agents: backend-architect, code-reviewer
    for line in raw_text.splitlines():
        marker_match = re.search(
            r"(?:@)?agent(?:_name|_concerne)?s?\s*[:=]\s*(.+)$",
            line,
            re.IGNORECASE,
        )
        if not marker_match:
            continue
        for item in re.split(r"[,\s]+", marker_match.group(1)):
            normalized = normalize_agent_identifier(item.strip())
            if normalized in by_name and normalized not in selected:
                selected.append(normalized)

    if selected:
        return selected

    # Alternative compact format:
    #   @backend-architect @code-reviewer
    for handle in re.findall(r"@([a-z0-9\-]+)", raw_text.lower()):
        normalized = normalize_agent_identifier(handle)
        if normalized in by_name and normalized not in selected:
            selected.append(normalized)

    if selected:
        return selected

    # Last resort: if the file contains a single raw token and it is an agent name.
    compact_lines = [
        line.strip().lower()
        for line in raw_text.splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    if len(compact_lines) == 1:
        token = normalize_agent_identifier(compact_lines[0])
        if token in by_name:
            selected.append(token)

    return selected


def select_agents(
    problem: Problem,
    agents: list[AgentSpec],
    mode: str,
    context_agents: list[str],
) -> list[AgentSpec]:
    by_name = {agent.name.lower(): agent for agent in agents}
    explicit_agents = parse_explicit_agents(problem.content)
    if explicit_agents:
        selected = [by_name[name] for name in explicit_agents if name in by_name]
        if selected:
            return selected

    if context_agents:
        selected = [by_name[name] for name in context_agents if name in by_name]
        if selected:
            return selected

    if mode == "all":
        return agents

    problem_tokens = tokenize(problem.content)
    ranked: list[tuple[int, AgentSpec]] = []
    for agent in agents:
        score = len(problem_tokens.intersection(agent.keywords))
        if score > 0:
            ranked.append((score, agent))
    ranked.sort(key=lambda row: row[0], reverse=True)
    top_matches = [agent for _, agent in ranked[:4]]
    if top_matches:
        return top_matches
    fallback_names = ["debugger", "code-reviewer", "test-engineer"]
    fallback_agents = [by_name[name] for name in fallback_names if name in by_name]
    if fallback_agents:
        return fallback_agents
    return agents[:3]


def load_state(state_file: Path) -> dict:
    if not state_file.exists():
        return {"processed_problem_ids": []}
    try:
        return json.loads(state_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"processed_problem_ids": []}


def save_state(state_file: Path, state: dict) -> None:
    state_file.parent.mkdir(parents=True, exist_ok=True)
    temp_file = state_file.with_suffix(state_file.suffix + ".tmp")
    temp_file.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
    temp_file.replace(state_file)


def pick_sub_agent(agent: AgentSpec, agents: list[AgentSpec]) -> str:
    available_names = {item.name for item in agents}
    mapped = SUB_AGENT_MAP.get(agent.name)
    if mapped and mapped in available_names and mapped != agent.name:
        return mapped
    if "explore-code" in available_names and agent.name != "explore-code":
        return "explore-code"
    for fallback in ("debugger", "code-reviewer", "test-engineer"):
        if fallback in available_names and fallback != agent.name:
            return fallback
    for candidate in sorted(available_names):
        if candidate != agent.name:
            return candidate
    return agent.name


def render_skill_config(
    agent: AgentSpec,
    problem: Problem,
    source_file: Path,
    skill_name: str,
    sub_agent: str,
) -> str:
    now_iso = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    return f"""---
name: {skill_name}
description: Skill de remediation pour {agent.name}. Utiliser ce skill quand un probleme similaire a "{problem.title}" reapparait.
arguments:
  - name: source_problem_markdown
    required: true
    description: Fichier markdown du probleme source.
  - name: output_file
    required: false
    default: reports/{skill_name}-solution.md
    description: Fichier de sortie pour le plan de correction.
  - name: evidence_dir
    required: false
    default: reports/evidence
    description: Dossier pour stocker les preuves et validations.
---

# Skill auto-genere: {problem.title}

## Metadata
- created_at: `{now_iso}`
- source_problem_file: `{source_file.name}`
- source_problem_id: `{problem.problem_id}`
- agent_cible: `{agent.name}`
- sub_agent_recommande: `{sub_agent}`

## Objectifs
- Detecter vite le probleme et son impact.
- Produire un plan de correction executable.
- Verifier le correctif avec une preuve concrete.

## Etapes
1. Lancer `bash scripts/preflight-check.sh` pour valider la structure du skill.
2. Lire `references/problem-context.md` pour comprendre les symptomes et le contexte.
3. Utiliser `references/agent-rules.md` pour appliquer la logique metier de `{agent.name}`.
4. Copier le template `templates/solution-template.md` et completer le plan.
5. Lancer `bash scripts/build-solution-report.sh references/problem-context.md "$output_file"` pour generer le rapport.
6. Ajouter les preuves de validation dans `evidence_dir`.

## Arguments
- `source_problem_markdown` (obligatoire): chemin du probleme source.
- `output_file` (optionnel): rapport final.
- `evidence_dir` (optionnel): preuves de tests, logs, captures.

## Exemples d'utilisation
### Exemple 1
Input:
- source_problem_markdown: `probleme.Md`
- output_file: `reports/{skill_name}-solution.md`

Commande:
`bash scripts/build-solution-report.sh references/problem-context.md reports/{skill_name}-solution.md`

Resultat attendu:
- Un rapport structure avec cause racine, fix, verification et evidences.

## Integrations avancees (Hooks et Agents)
- Hook pre-run: `bash scripts/preflight-check.sh`
- Hook report-build: `bash scripts/build-solution-report.sh ...`
- Sub-agent recommande: `{sub_agent}`
- Handoff suggere: deleguer l'exploration detaillee au sub-agent, puis revenir ici pour compiler la solution.
"""


def update_agent_file(agent_file: Path, skill_rel_path: Path) -> bool:
    text = agent_file.read_text(encoding="utf-8")
    section_title = "## Skills auto-generes"
    new_entry = f"- `{skill_rel_path.as_posix()}`"
    if new_entry in text:
        return False

    if section_title in text:
        section_match = re.search(rf"^{re.escape(section_title)}\s*$", text, re.MULTILINE)
        if not section_match:
            return False
        insert_start = section_match.end()
        after_section = text[insert_start:]
        next_heading = re.search(r"^##\s+", after_section, re.MULTILINE)
        insert_at = insert_start + next_heading.start() if next_heading else len(text)
        section_body = text[insert_start:insert_at].strip()
        if section_body:
            replacement = f"\n\n{section_body}\n{new_entry}\n\n"
        else:
            replacement = f"\n\n{new_entry}\n\n"
        updated = text[:insert_start] + replacement + text[insert_at:].lstrip("\n")
    else:
        updated = text.rstrip() + f"\n\n{section_title}\n\n{new_entry}\n"

    agent_file.write_text(updated, encoding="utf-8")
    return True


def create_skill_for_agent(
    agent: AgentSpec,
    all_agents: list[AgentSpec],
    problem: Problem,
    agents_dir: Path,
    source_file: Path,
    dry_run: bool,
) -> Path:
    timestamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    skill_slug = f"{timestamp}-{problem.problem_id}-{slugify(problem.title)}"
    skill_name = f"auto-{agent.name}-{problem.problem_id}"
    skill_root = agent.skills_dir / skill_slug
    scripts_dir = skill_root / "scripts"
    templates_dir = skill_root / "templates"
    references_dir = skill_root / "references"
    resources_dir = skill_root / "resources"
    skill_config_path = skill_root / "skill.md"

    sub_agent = pick_sub_agent(agent, all_agents)
    skill_config = render_skill_config(
        agent=agent,
        problem=problem,
        source_file=source_file,
        skill_name=skill_name,
        sub_agent=sub_agent,
    )
    problem_reference = f"""# Problem Context

- source_file: `{source_file.name}`
- problem_id: `{problem.problem_id}`
- agent_cible: `{agent.name}`

## Original Problem
{problem.content}
"""
    agent_reference = f"""# Agent Rules

## Mission
{agent.description or "Analyser et proposer une remediation concrete."}

## Decision Rules
1. Prioriser la correction du risque le plus impactant.
2. Eviter les changements larges sans preuve.
3. Ajouter une validation executable avant de marquer la correction comme complete.

## Collaboration
- Sub-agent recommande: `{sub_agent}`
- Escalade: si blocage apres 2 essais, produire un mini post-mortem avec hypotheses et preuves.
"""
    template_content = f"""# Solution Report Template

## Problem Summary
- ID: {problem.problem_id}
- Agent: {agent.name}
- Title: {problem.title}

## Root Cause
- Cause principale:
- Contexte technique:

## Fix Plan
1. 
2. 
3. 

## Validation Plan
- Tests:
- Logs:
- Regression checks:

## Result
- Statut:
- Risques residuels:
"""
    preflight_script = """#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

required_files=(
  "${SKILL_DIR}/skill.md"
  "${SKILL_DIR}/templates/solution-template.md"
  "${SKILL_DIR}/references/problem-context.md"
  "${SKILL_DIR}/references/agent-rules.md"
  "${SKILL_DIR}/resources/sub-agent-config.json"
)

for file in "${required_files[@]}"; do
  if [ ! -f "${file}" ]; then
    echo "Missing required file: ${file}" >&2
    exit 1
  fi
done

echo "Preflight OK: skill bundle is complete."
"""
    build_report_script = """#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 1 ] || [ "$#" -gt 2 ]; then
  echo "Usage: $0 <problem_context_md> [output_md]" >&2
  exit 1
fi

PROBLEM_CONTEXT="$1"
OUTPUT_FILE="${2:-solution-report.md}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
TEMPLATE_FILE="${SKILL_DIR}/templates/solution-template.md"
RULES_FILE="${SKILL_DIR}/references/agent-rules.md"

if [ ! -f "${PROBLEM_CONTEXT}" ]; then
  echo "Problem context file not found: ${PROBLEM_CONTEXT}" >&2
  exit 1
fi
if [ ! -f "${TEMPLATE_FILE}" ]; then
  echo "Template file not found: ${TEMPLATE_FILE}" >&2
  exit 1
fi
if [ ! -f "${RULES_FILE}" ]; then
  echo "Rules file not found: ${RULES_FILE}" >&2
  exit 1
fi

mkdir -p "$(dirname "${OUTPUT_FILE}")"
cat "${TEMPLATE_FILE}" > "${OUTPUT_FILE}"

{
  echo ""
  echo "## Imported Problem Context"
  cat "${PROBLEM_CONTEXT}"
  echo ""
  echo "## Agent Rules Snapshot"
  cat "${RULES_FILE}"
} >> "${OUTPUT_FILE}"

echo "Report generated: ${OUTPUT_FILE}"
"""
    resource_content = json.dumps(
        {
            "skill_name": skill_name,
            "agent": agent.name,
            "problem_id": problem.problem_id,
            "problem_title": problem.title,
            "sub_agent": sub_agent,
            "hooks": {
                "preflight": "scripts/preflight-check.sh",
                "build_report": "scripts/build-solution-report.sh",
            },
        },
        indent=2,
        ensure_ascii=False,
    )

    if not dry_run:
        scripts_dir.mkdir(parents=True, exist_ok=True)
        templates_dir.mkdir(parents=True, exist_ok=True)
        references_dir.mkdir(parents=True, exist_ok=True)
        resources_dir.mkdir(parents=True, exist_ok=True)

        skill_config_path.write_text(skill_config, encoding="utf-8")
        (scripts_dir / "preflight-check.sh").write_text(preflight_script, encoding="utf-8")
        (scripts_dir / "build-solution-report.sh").write_text(build_report_script, encoding="utf-8")
        (templates_dir / "solution-template.md").write_text(template_content, encoding="utf-8")
        (references_dir / "problem-context.md").write_text(problem_reference, encoding="utf-8")
        (references_dir / "agent-rules.md").write_text(agent_reference, encoding="utf-8")
        (resources_dir / "sub-agent-config.json").write_text(resource_content, encoding="utf-8")

        (scripts_dir / "preflight-check.sh").chmod(0o755)
        (scripts_dir / "build-solution-report.sh").chmod(0o755)

        skill_rel_path = skill_config_path.relative_to(agents_dir.parent)
        update_agent_file(agent.file_path, skill_rel_path)
    return skill_config_path


def process_once(
    problems_file: Path,
    agents_dir: Path,
    state_file: Path,
    agent_context_file: Path,
    mode: str,
    dry_run: bool,
) -> tuple[int, int]:
    agents = load_agents(agents_dir)
    context_agents = parse_context_agents(agent_context_file, agents)
    state = load_state(state_file)
    known_ids = set(state.get("processed_problem_ids", []))
    problems = parse_problems(problems_file)

    new_problem_count = 0
    generated_count = 0

    for problem in problems:
        if problem.problem_id in known_ids:
            continue
        new_problem_count += 1
        selected_agents = select_agents(problem, agents, mode, context_agents)
        for agent in selected_agents:
            create_skill_for_agent(
                agent=agent,
                all_agents=agents,
                problem=problem,
                agents_dir=agents_dir,
                source_file=problems_file,
                dry_run=dry_run,
            )
            generated_count += 1
        if not dry_run:
            known_ids.add(problem.problem_id)

    if not dry_run:
        state["processed_problem_ids"] = sorted(known_ids)
        save_state(state_file, state)

    return new_problem_count, generated_count


def print_log(message: str) -> None:
    now = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{now}] {message}", flush=True)


def watch_loop(
    problems_file: Path,
    agents_dir: Path,
    state_file: Path,
    agent_context_file: Path,
    mode: str,
    dry_run: bool,
    interval: int,
) -> None:
    last_mtime = problems_file.stat().st_mtime if problems_file.exists() else 0.0
    new_problems, generated = process_once(
        problems_file,
        agents_dir,
        state_file,
        agent_context_file,
        mode,
        dry_run,
    )
    print_log(f"Initial scan: {new_problems} new problem(s), {generated} skill(s) generated.")

    while True:
        time.sleep(interval)
        current_mtime = problems_file.stat().st_mtime if problems_file.exists() else 0.0
        if current_mtime == last_mtime:
            continue
        last_mtime = current_mtime
        new_problems, generated = process_once(
            problems_file,
            agents_dir,
            state_file,
            agent_context_file,
            mode,
            dry_run,
        )
        print_log(f"Update detected: {new_problems} new problem(s), {generated} skill(s) generated.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Auto-generate skills for agents when new problems are added to probleme.Md."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    run_parser = subparsers.add_parser("run", help="Process the problems file once.")
    add_common_arguments(run_parser)
    run_parser.add_argument("--dry-run", action="store_true", help="Compute actions without writing files.")
    watch_parser = subparsers.add_parser("watch", help="Watch the problems file and process updates continuously.")
    add_common_arguments(watch_parser)
    watch_parser.add_argument("--interval", type=int, default=5, help="Polling interval in seconds (default: 5).")
    watch_parser.add_argument("--dry-run", action="store_true", help="Compute actions without writing files.")
    return parser


def add_common_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--problems-file",
        default="probleme.Md",
        help="Path to the markdown file containing problems (default: probleme.Md).",
    )
    parser.add_argument(
        "--agents-dir",
        default="agents_library",
        help="Directory containing agent markdown files (default: agents_library).",
    )
    parser.add_argument(
        "--state-file",
        default=".auto-skills/state.json",
        help="State file used to avoid duplicate generation (default: .auto-skills/state.json).",
    )
    parser.add_argument(
        "--agent-context-file",
        default="AGENT.md",
        help="File that names the agent(s) to improve (default: AGENT.md).",
    )
    parser.add_argument(
        "--selection-mode",
        choices=["all", "matched"],
        default="all",
        help="Select all agents or only keyword-matched agents (default: all).",
    )


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    problems_file = Path(args.problems_file).resolve()
    agents_dir = Path(args.agents_dir).resolve()
    state_file = Path(args.state_file).resolve()
    agent_context_file = Path(args.agent_context_file).resolve()

    if args.command == "run":
        new_problems, generated = process_once(
            problems_file=problems_file,
            agents_dir=agents_dir,
            state_file=state_file,
            agent_context_file=agent_context_file,
            mode=args.selection_mode,
            dry_run=args.dry_run,
        )
        print_log(f"Run complete: {new_problems} new problem(s), {generated} skill(s) generated.")
        return 0

    watch_loop(
        problems_file=problems_file,
        agents_dir=agents_dir,
        state_file=state_file,
        agent_context_file=agent_context_file,
        mode=args.selection_mode,
        dry_run=args.dry_run,
        interval=args.interval,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
