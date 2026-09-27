#!/usr/bin/env python3
"""
sync_mcp_data.py — Cross-repository data auditor and synchronizer for anacatalina-mcp.

Audits and synchronizes `data/cv_data.json` with baseline candidate data from
`../anacatalina-cv` (i18n dictionaries, experience bullets, skills, education)
and `../projects-hub` (project frontmatter, technologies, repo/demo URLs).

Enforces:
- Zero hardcoded paths (dynamically resolves sibling workspaces).
- Candidate identity invariants (Ana-Catalina Villalobos Contardo).
- Strict Pydantic v2 validation via models.cv.CVData.
- Zero Flags policy.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

try:
    from models.cv import CVData
except ImportError:
    # Handle running script directly from repo root or subfolder
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from models.cv import CVData


def clean_html(raw_html: str) -> str:
    """Strip HTML formatting tags while preserving text content."""
    clean = re.sub(r"<br\s*/?>", " ", raw_html, flags=re.IGNORECASE)
    clean = re.sub(r"<[^>]+>", "", clean)
    clean = re.sub(r"\s+", " ", clean)
    return clean.strip()


def parse_cv_ts(cv_ts_path: Path) -> Dict[str, Dict[str, str]]:
    """
    Extract structured text from anacatalina-cv/src/data/cv.ts SSOT file.
    Maps hero keys and experience keys (e.g. 'exp.simpliroute.b1', 'exp.simpliroute.date').
    """
    if not cv_ts_path.exists():
        return {}

    content = cv_ts_path.read_text(encoding="utf-8")
    trans: Dict[str, Dict[str, str]] = {}

    title_m = re.search(r'title:\s*\{\s*es:\s*[\'"]([^\'"]+)[\'"],\s*en:\s*[\'"]([^\'"]+)[\'"]', content)
    if title_m:
        trans["hero.subtitle"] = {"es": clean_html(title_m.group(1)), "en": clean_html(title_m.group(2))}

    loc_m = re.search(r'location:\s*\{\s*es:\s*[\'"]([^\'"]+)[\'"],\s*en:\s*[\'"]([^\'"]+)[\'"]', content)
    if loc_m:
        trans["hero.location"] = {"es": clean_html(loc_m.group(1)), "en": clean_html(loc_m.group(2))}

    exp_pattern = re.compile(
        r'\{\s*id:\s*[\'"]([^\'"]+)[\'"].*?company:\s*[\'"]([^\'"]+)[\'"].*?role:\s*\{([^}]+)\}.*?date:\s*\{([^}]+)\}.*?location:\s*\{([^}]+)\}.*?bullets:\s*\[(.*?)\]\s*,\s*pdfBullets',
        re.DOTALL
    )
    for m in exp_pattern.finditer(content):
        exp_id = m.group(1)
        role_body, date_body, loc_body, bullets_raw = m.group(3), m.group(4), m.group(5), m.group(6)

        for key_suffix, body in [("title", role_body), ("date", date_body), ("location", loc_body)]:
            es_m = re.search(r'es\s*:\s*[\'"`](.*?)[\'"`]', body)
            en_m = re.search(r'en\s*:\s*[\'"`](.*?)[\'"`]', body)
            trans[f"exp.{exp_id}.{key_suffix}"] = {
                "es": clean_html(es_m.group(1)) if es_m else "",
                "en": clean_html(en_m.group(1)) if en_m else ""
            }

        bullet_items = re.findall(r'\{\s*es:\s*([\'"`].*?[\'"`])\s*,\s*en:\s*([\'"`].*?[\'"`])\s*\}', bullets_raw, re.DOTALL)
        for idx, (es, en) in enumerate(bullet_items):
            trans[f"exp.{exp_id}.b{idx+1}"] = {
                "es": clean_html(es[1:-1]),
                "en": clean_html(en[1:-1])
            }

    return trans


def parse_i18n_js(file_path: Path) -> Dict[str, Dict[str, str]]:
    """
    Parse export const translations = { ... } from anacatalina-cv/src/i18n.js
    Also parses and merges structured data from anacatalina-cv/src/data/cv.ts if present.
    Returns a dictionary mapping string keys to {'es': '...', 'en': '...'}.
    """
    translations: Dict[str, Dict[str, str]] = {}

    if file_path.exists():
        content = file_path.read_text(encoding="utf-8")
        block_pattern = re.compile(
            r'["\']([^"\']+)["\']\s*:\s*\{([^}]+)\}',
            re.DOTALL
        )

        for match in block_pattern.finditer(content):
            key = match.group(1)
            body = match.group(2)

            es_match = re.search(r'es\s*:\s*["\'`](.*?)["\'`]\s*(?:,|$)', body, re.DOTALL)
            en_match = re.search(r'en\s*:\s*["\'`](.*?)["\'`]\s*(?:,|$)', body, re.DOTALL)

            es_val = clean_html(es_match.group(1)) if es_match else ""
            en_val = clean_html(en_match.group(1)) if en_match else ""

            translations[key] = {
                "es": es_val,
                "en": en_val
            }

    # If sibling SSOT cv.ts exists, merge it so keys referencing cvData are fully resolved
    cv_ts_path = file_path.parent / "data" / "cv.ts"
    if cv_ts_path.exists():
        translations.update(parse_cv_ts(cv_ts_path))

    return translations


SKILL_ALIASES: Dict[str, str] = {
    "google cloud (gcp)": "google cloud platform (gcp)",
    "gcp": "google cloud platform (gcp)",
    "google cloud": "google cloud platform (gcp)",
    "node": "node.js",
    "nodejs": "node.js",
    "html & css": "html & css",
    "html/css": "html & css",
    "plotly / dash": "plotly / dash",
    "plotly/dash": "plotly / dash",
}


def normalize_skill(name: str) -> str:
    """Normalize skill name for comparison and alias resolution."""
    cleaned = re.sub(r"\s+", " ", name).strip().lower()
    return SKILL_ALIASES.get(cleaned, cleaned)


def parse_skills_from_cv_astro(astro_path: Path) -> Dict[str, List[str]]:
    """
    Extract skill badge names grouped by category from anacatalina-cv/src/pages/index.astro.
    Captures all skill-group containers regardless of whether data-category is present.
    """
    if not astro_path.exists():
        return {}

    content = astro_path.read_text(encoding="utf-8")
    categories: Dict[str, List[str]] = {}

    skills_sec_match = re.search(
        r'<section[^>]*id=["\']skills["\'][^>]*>(.*?)</section>',
        content,
        re.DOTALL
    )
    search_text = skills_sec_match.group(1) if skills_sec_match else content

    group_splits = re.split(r'<div[^>]*class=["\'][^"\']*skill-group[^"\']*["\'][^>]*>', search_text)
    badge_regex = re.compile(
        r'<span[^>]*class=["\'][^"\']*rounded-lg[^"\']*["\'][^>]*>(.*?)</span>',
        re.DOTALL
    )
    title_regex = re.compile(r'<h3[^>]*>(.*?)</h3>', re.DOTALL)

    for block in group_splits[1:]:
        h3_match = title_regex.search(block)
        category_name = clean_html(h3_match.group(1)) if h3_match else "General"

        skills: List[str] = []
        for b in badge_regex.finditer(block):
            badge_text = clean_html(b.group(1))
            if badge_text and not badge_text.startswith("<"):
                skills.append(badge_text)

        if skills:
            categories[category_name] = skills

    return categories


def parse_project_markdown(file_path: Path) -> Optional[Dict[str, Any]]:
    """
    Parse frontmatter from a projects-hub Markdown file (src/content/projects/es/*.md).
    """
    if not file_path.exists():
        return None

    content = file_path.read_text(encoding="utf-8")
    if not content.startswith("---"):
        return None

    parts = content.split("---", 2)
    if len(parts) < 3:
        return None

    frontmatter_text = parts[1]
    data: Dict[str, Any] = {}

    for raw_line in frontmatter_text.splitlines():
        # Only top-level keys: indented lines belong to nested blocks whose keys
        # (e.g. a nested "title") would otherwise overwrite the project's own.
        if raw_line[:1].isspace():
            continue
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        if ":" in line:
            key, val = line.split(":", 1)
            key = key.strip()
            val = val.strip()

            if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                data[key] = val[1:-1]
            elif val.startswith("[") and val.endswith("]"):
                raw_items = val[1:-1].split(",")
                items = [item.strip().strip('"\'') for item in raw_items if item.strip()]
                data[key] = items
            elif val.lower() == "true":
                data[key] = True
            elif val.lower() == "false":
                data[key] = False
            elif val.lower() in ("null", "~"):
                data[key] = None
            else:
                data[key] = val

    return data


def scan_projects_hub(projects_dir: Path) -> List[Dict[str, Any]]:
    """
    Scan all projects in projects-hub/src/content/projects/es/*.md
    """
    es_dir = projects_dir / "src" / "content" / "projects" / "es"
    if not es_dir.exists():
        return []

    projects = []
    for md_file in sorted(es_dir.glob("*.md")):
        frontmatter = parse_project_markdown(md_file)
        if frontmatter and frontmatter.get("title"):
            slug = md_file.stem
            projects.append({
                "slug": slug,
                "name": frontmatter.get("title"),
                "type": "personal",
                "description": frontmatter.get("description", ""),
                "technologies": frontmatter.get("technologies", []),
                "repo_url": frontmatter.get("githubUrl"),
                "demo_url": frontmatter.get("websiteUrl"),
                "status": frontmatter.get("status", "Activo")
            })
    return projects


class DataAuditor:
    """Audits and syncs data between sibling repos and anacatalina-mcp."""

    def __init__(
        self,
        base_dir: Path,
        cv_dir: Optional[Path] = None,
        projects_dir: Optional[Path] = None,
        data_file: Optional[Path] = None
    ):
        self.base_dir = base_dir.resolve()
        self.cv_dir = (cv_dir or (self.base_dir.parent / "anacatalina-cv")).resolve()
        self.projects_dir = (projects_dir or (self.base_dir.parent / "projects-hub")).resolve()
        self.data_file = (data_file or (self.base_dir / "data" / "cv_data.json")).resolve()

    def load_current_cv_data(self) -> Dict[str, Any]:
        """Load and parse current local data/cv_data.json."""
        if not self.data_file.exists():
            return {}
        with open(self.data_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def audit(self) -> Dict[str, Any]:
        """
        Compare local cv_data.json against anacatalina-cv and projects-hub.
        Returns a comprehensive report of status, matches, and discrepancies.
        """
        current_data = self.load_current_cv_data()
        cv_translations = parse_i18n_js(self.cv_dir / "src" / "i18n.js")
        hub_projects = scan_projects_hub(self.projects_dir)

        report: Dict[str, Any] = {
            "sources": {
                "cv_repo_found": self.cv_dir.exists(),
                "cv_repo_path": str(self.cv_dir),
                "projects_hub_found": self.projects_dir.exists(),
                "projects_hub_path": str(self.projects_dir),
                "data_file_found": self.data_file.exists(),
                "data_file_path": str(self.data_file),
            },
            "discrepancies": [],
            "stats": {
                "current_experience_count": len(current_data.get("experience", [])),
                "current_skills_categories": len(current_data.get("skills", [])),
                "current_projects_count": len(current_data.get("projects", [])),
                "hub_projects_found": len(hub_projects),
                "i18n_keys_found": len(cv_translations),
            },
            "in_sync": True
        }

        if not self.cv_dir.exists():
            report["discrepancies"].append({
                "component": "sources",
                "issue": f"Sibling repository anacatalina-cv not found at {self.cv_dir}"
            })
            report["in_sync"] = False

        if not self.projects_dir.exists():
            report["discrepancies"].append({
                "component": "sources",
                "issue": f"Sibling repository projects-hub not found at {self.projects_dir}"
            })
            report["in_sync"] = False

        # 1. Audit Experience Bullets (e.g. SimpliRoute updates)
        if cv_translations:
            experiences = current_data.get("experience", [])
            simpli_item = next((e for e in experiences if e.get("company") == "SimpliRoute"), None)
            if simpli_item:
                current_resps = simpli_item.get("responsibilities", [])
                for b_idx in range(1, 5):
                    target_b = cv_translations.get(f"exp.simpliroute.b{b_idx}", {}).get("es")
                    if target_b and (
                        b_idx > len(current_resps)
                        or target_b != current_resps[b_idx - 1]
                    ):
                        report["discrepancies"].append({
                            "component": f"experience.SimpliRoute.b{b_idx}",
                            "issue": f"SimpliRoute b{b_idx} wording updated in anacatalina-cv: '{target_b[:70]}...'"
                        })
                        report["in_sync"] = False

        # 2. Audit Skills Matrix (Dynamically compare against anacatalina-cv index.astro & i18n)
        all_current_skills = {
            normalize_skill(s.get("name", ""))
            for cat in current_data.get("skills", [])
            for s in cat.get("skills", [])
        }
        
        astro_skills_map = parse_skills_from_cv_astro(self.cv_dir / "src" / "pages" / "index.astro")
        all_astro_skills = [
            s for skill_list in astro_skills_map.values()
            for s in skill_list
            if s.strip()
        ]
        
        missing_skills = []
        for s in all_astro_skills:
            s_clean = s.strip()
            s_norm = normalize_skill(s_clean)
            # Check if skill exists or is alias / matched in current skills
            matched = (
                s_norm in all_current_skills
                or any(
                    s_norm == curr or (len(s_norm) > 4 and (s_norm in curr or curr in s_norm))
                    for curr in all_current_skills
                )
            )
            if not matched:
                missing_skills.append(s_clean)

        if missing_skills:
            report["discrepancies"].append({
                "component": "skills",
                "issue": f"Recently added technical skills in anacatalina-cv not yet in MCP skills matrix: {missing_skills}"
            })
            report["in_sync"] = False

        # 3. Audit Projects Hub Alignment (Dynamically compare showcase projects)
        current_project_names = {p.get("name") for p in current_data.get("projects", [])}
        target_flagship_slugs = ["cute-agents-desk", "work-activity-panel", "anacatalina-mcp"]
        for p in hub_projects:
            if p.get("slug") in target_flagship_slugs:
                if p.get("name") not in current_project_names and p.get("slug") != "anacatalina-mcp":
                    report["discrepancies"].append({
                        "component": "projects",
                        "issue": f"Flagship project '{p.get('name')}' ({p.get('slug')}) from projects-hub can be synchronized into MCP featured projects."
                    })
                    report["in_sync"] = False

        # 4. Audit i18n keys the sync depends on (a missing key silently falls back to hardcoded text)
        if cv_translations:
            self.generate_synchronized_dataset()
            for key in sorted(self.missing_translation_keys):
                report["discrepancies"].append({
                    "component": "cv_translations",
                    "issue": f"Key '{key}' missing in anacatalina-cv i18n.js; sync would use the hardcoded fallback."
                })
                report["in_sync"] = False

        return report

    def _es(self, translations: Dict[str, Dict[str, str]], key: str, fallback: str) -> str:
        """Return the Spanish translation for key, recording the key when the fallback is used."""
        value = translations.get(key, {}).get("es")
        if value is None:
            self.missing_translation_keys.add(key)
            return fallback
        return value

    def generate_synchronized_dataset(self) -> Dict[str, Any]:
        """
        Merge and build the complete updated CVData structure.
        """
        self.missing_translation_keys: Set[str] = set()
        current_data = self.load_current_cv_data()
        cv_translations = parse_i18n_js(self.cv_dir / "src" / "i18n.js")
        hub_projects = scan_projects_hub(self.projects_dir)

        new_data = json.loads(json.dumps(current_data)) if current_data else {}

        # 1. Personal Info
        new_data["personal_info"] = {
            "name": "Ana-Catalina Villalobos Contardo",
            "first_name": "Ana-Catalina",
            "middle_name": "Alejandra",
            "last_name": "Villalobos Contardo",
            "full_name": "Ana-Catalina Alejandra Villalobos Contardo",
            "title": self._es(cv_translations, "hero.subtitle", "Data Scientist & Machine Learning Engineer"),
            "location": "Santiago, Chile",
            "contact": {
                "email": "anacatalina@outlook.cl",
                "linkedin": "https://linkedin.com/in/ana-catalina/"
            },
            "portfolio_links": {
                "github": "https://github.com/AnaCataVC"
            }
        }

        # 2. Executive Summaries
        new_data["summary"] = {
            "es": (
                "Data Scientist y Machine Learning Engineer con sólida experiencia en diseño e "
                "implementación de modelos de Machine Learning, pipelines analíticos escalables y "
                "arquitecturas basadas en agentes con Model Context Protocol (MCP). Especializada en "
                "el ecosistema de Google Cloud Platform (BigQuery, Vertex AI), Python y containerización "
                "con Docker para optimización logística y soluciones de Inteligencia Artificial aplicada."
            ),
            "en": (
                "Data Scientist and Machine Learning Engineer with solid experience in designing and "
                "deploying Machine Learning models, scalable analytical pipelines, and agentic "
                "architectures with Model Context Protocol (MCP). Specialized in Google Cloud Platform "
                "(BigQuery, Vertex AI), Python, and Docker containerization for logistics optimization "
                "and applied AI solutions."
            )
        }

        # 3. Synchronize Experience
        new_data["experience"] = [
            {
                "company": "SimpliRoute",
                "role": "Learning Engineer",
                "period": self._es(cv_translations, "exp.simpliroute.date", "Agosto 2025 - Presente"),
                "location": self._es(cv_translations, "exp.simpliroute.location", "Santiago, Chile (Remoto)"),
                "type": "laboral",
                "responsibilities": [
                    self._es(cv_translations, "exp.simpliroute.b1", "Arquitectura e implementación de un sistema distribuido de geolocalización y geocodificación multi-proveedor, diseñando pipelines asíncronos desacoplados, estrategias de alta disponibilidad y estandarización de microservicios con tolerancia a fallos."),
                    self._es(cv_translations, "exp.simpliroute.b2", "Diseño y despliegue en producción de infraestructura agéntica basada en Model Context Protocol (MCP) para motores logísticos, implementando guardrails deterministas, permisos de ejecución de herramientas de mínimo privilegio y persistencia distribuida con Redis en Kubernetes."),
                    self._es(cv_translations, "exp.simpliroute.b3", "Gestión y modelado de datos a gran escala en Google BigQuery y orquestación de flujos de eventos mediante Google Pub/Sub y Apache Airflow, garantizando alta confiabilidad operativa, linaje de datos y telemetría crítica."),
                    self._es(cv_translations, "exp.simpliroute.b4", "Impulso de la adopción de IA Generativa en el ciclo de desarrollo (DevEx) y productos, diseñando flujos de trabajo asistidos por agentes para optimizar pruebas, acelerar ciclos de iteración y elevar la eficiencia operativa.")
                ],
                "technologies": [
                    "Python",
                    "GCP",
                    "BigQuery",
                    "Pub/Sub",
                    "Airflow",
                    "Model Context Protocol (MCP)",
                    "LLMs & GenAI",
                    "Claude Code & Antigravity",
                    "FastAPI",
                    "Redis",
                    "Kubernetes"
                ]
            },
            {
                "company": "Fracttal",
                "role": "Tech Lead Fracttal Hub",
                "period": self._es(cv_translations, "exp.fracttal1.date", "Noviembre 2023 - Julio 2025"),
                "location": self._es(cv_translations, "exp.fracttal1.location", "Santiago, Chile"),
                "type": "laboral",
                "responsibilities": [
                    self._es(cv_translations, "exp.fracttal1.b1", "Liderazgo de equipo multidisciplinario de integraciones con personas en distintos países, enfocado en mentoría técnica, desarrollo profesional y un entorno colaborativo."),
                    self._es(cv_translations, "exp.fracttal1.b2", "Planificación estratégica del roadmap de Fracttal Hub, alineando los objetivos de negocio y la entrega continua de valor a clientes."),
                    self._es(cv_translations, "exp.fracttal1.b3", "Desarrollo en Python para librerías de procesamiento de datos y orquestación de tareas, habilitando la integración con múltiples fuentes y destinos, con más de 100 acciones posibles y capacidades avanzadas de transformación."),
                    self._es(cv_translations, "exp.fracttal1.b4", "Supervisión y coordinación de proyectos de integración para decenas de clientes, aplicando gestión eficiente de recursos, plazos y flujos de datos confiables.")
                ],
                "technologies": [
                    "Python",
                    "Integraciones API",
                    "ETLs",
                    "Liderazgo Técnico"
                ]
            },
            {
                "company": "Fracttal",
                "role": "Data Scientist",
                "period": self._es(cv_translations, "exp.fracttal2.date", "Agosto 2021 - Noviembre 2023"),
                "location": self._es(cv_translations, "exp.fracttal2.location", "Santiago, Chile"),
                "type": "laboral",
                "responsibilities": [
                    self._es(cv_translations, "exp.fracttal2.b1", "Diseño e implementación de procesos de ciencia de datos para las plataformas Predictto y Fracttal One, con foco en generar valor a partir de datos operacionales de maquinaria."),
                    self._es(cv_translations, "exp.fracttal2.b2", "Desarrollo de modelos analíticos aplicados a mantenimiento predictivo, priorización de activos y predicción de fallas, combinando ML, estadística y conocimiento del dominio."),
                    self._es(cv_translations, "exp.fracttal2.b3", "Colaboración en la creación y desarrollo de producto para gestionar integraciones entre Fracttal y otras plataformas de software empresariales."),
                    self._es(cv_translations, "exp.fracttal2.b4", "Evaluación continua de modelos en producción, optimizando pipelines de datos para garantizar la precisión y robustez en entornos reales.")
                ],
                "technologies": [
                    "Python",
                    "Machine Learning",
                    "Estadística",
                    "Data Pipelines"
                ]
            },
            {
                "company": "Fracttal",
                "role": "Analista de Datos",
                "period": self._es(cv_translations, "exp.fracttal3.date", "Febrero 2020 - Julio 2021"),
                "location": self._es(cv_translations, "exp.fracttal3.location", "Santiago, Chile"),
                "type": "laboral",
                "responsibilities": [
                    self._es(cv_translations, "exp.fracttal3.b1", "Desarrollo desde cero de la herramienta de mantenimiento predictivo, utilizando análisis estadístico avanzado y modelos preliminares de Machine Learning."),
                    self._es(cv_translations, "exp.fracttal3.b2", "Diseño, manejo y optimización de bases de datos relacionales para almacenar lecturas de telemetría e historial de mantenimiento."),
                    self._es(cv_translations, "exp.fracttal3.b3", "Apoyo en el desarrollo web frontend/backend básico de visualizaciones de datos y métricas para tomadores de decisiones.")
                ],
                "technologies": [
                    "Python",
                    "SQL",
                    "Bases de Datos Relacionales",
                    "Machine Learning"
                ]
            }
        ]

        # 4. Synchronize Skills Matrix (Fully enriched with newly added technologies)
        new_data["skills"] = [
            {
                "category": "IA Agéntica & Machine Learning",
                "skills": [
                    {"name": "Sistemas Multi-Agente", "level": "Avanzado"},
                    {"name": "LLMs & GenAI", "level": "Avanzado"},
                    {"name": "Model Context Protocol (MCP)", "level": "Avanzado"},
                    {"name": "Claude Code & Antigravity", "level": "Avanzado"},
                    {"name": "Prompt Engineering", "level": "Avanzado"},
                    {"name": "Monitoreo de Modelos ML", "level": "Intermedio"},
                    {"name": "Automatización CI/CD con IA", "level": "Intermedio"}
                ]
            },
            {
                "category": "Ciencia de Datos & Librerías ML",
                "skills": [
                    {"name": "Vertex AI", "level": "Avanzado"},
                    {"name": "LangChain", "level": "Avanzado"},
                    {"name": "Analítica de Datos", "level": "Avanzado"},
                    {"name": "Estadística & Probabilidad", "level": "Avanzado"},
                    {"name": "Pandas & NumPy", "level": "Avanzado"},
                    {"name": "Scikit-learn", "level": "Avanzado"},
                    {"name": "TensorFlow", "level": "Intermedio"},
                    {"name": "Teoría de Grafos", "level": "Intermedio"}
                ]
            },
            {
                "category": "Lenguajes de Programación",
                "skills": [
                    {"name": "Python", "level": "Avanzado"},
                    {"name": "SQL", "level": "Avanzado"},
                    {"name": "Rust", "level": "Intermedio"},
                    {"name": "Kotlin", "level": "Intermedio"},
                    {"name": "TypeScript", "level": "Intermedio"},
                    {"name": "JavaScript", "level": "Intermedio"},
                    {"name": "C# (.NET)", "level": "Intermedio"},
                    {"name": "Java", "level": "Intermedio"},
                    {"name": "MATLAB", "level": "Intermedio"},
                    {"name": "Node.js", "level": "Intermedio"},
                    {"name": "Bash / Shell", "level": "Intermedio"}
                ]
            },
            {
                "category": "Frontend, Mobile & Desarrollo Web",
                "skills": [
                    {"name": ".NET 9 (WPF / WinUI 3)", "level": "Intermedio"},
                    {"name": "Android & Jetpack Compose", "level": "Intermedio"},
                    {"name": "FastHTML & HTMX", "level": "Intermedio"},
                    {"name": "React JS", "level": "Intermedio"},
                    {"name": "Astro", "level": "Intermedio"},
                    {"name": "Tailwind CSS", "level": "Intermedio"},
                    {"name": "Vite", "level": "Intermedio"},
                    {"name": "Streamlit", "level": "Intermedio"},
                    {"name": "HTML & CSS", "level": "Intermedio"},
                    {"name": "Plotly / Dash", "level": "Intermedio"},
                    {"name": "Figma", "level": "Intermedio"}
                ]
            },
            {
                "category": "Backend, Bases de Datos & Big Data",
                "skills": [
                    {"name": "FastAPI", "level": "Avanzado"},
                    {"name": "BigQuery", "level": "Avanzado"},
                    {"name": "PostgreSQL", "level": "Avanzado"},
                    {"name": "Pub/Sub", "level": "Avanzado"},
                    {"name": "ETLs", "level": "Avanzado"},
                    {"name": "Redis", "level": "Intermedio"},
                    {"name": "Pydantic", "level": "Avanzado"},
                    {"name": "Django", "level": "Intermedio"},
                    {"name": "SQL Server", "level": "Intermedio"},
                    {"name": "MySQL", "level": "Intermedio"},
                    {"name": "SQLite", "level": "Intermedio"},
                    {"name": "MongoDB", "level": "Intermedio"},
                    {"name": "SQLModel", "level": "Intermedio"},
                    {"name": "Dexie.js (IndexedDB)", "level": "Básico"}
                ]
            },
            {
                "category": "Contenedores, Orquestación & Cloud",
                "skills": [
                    {"name": "Google Cloud Platform (GCP)", "level": "Avanzado"},
                    {"name": "Google Cloud Run & Artifact Registry", "level": "Avanzado"},
                    {"name": "Docker", "level": "Avanzado"},
                    {"name": "Airflow", "level": "Avanzado"},
                    {"name": "Git", "level": "Avanzado"},
                    {"name": "GitHub", "level": "Avanzado"},
                    {"name": "Kubernetes", "level": "Intermedio"},
                    {"name": "ArgoCD", "level": "Intermedio"},
                    {"name": "Bitbucket", "level": "Intermedio"},
                    {"name": "Vercel", "level": "Intermedio"}
                ]
            },
            {
                "category": "Metodologías & Gestión de Producto",
                "skills": [
                    {"name": "Metodologías Ágiles", "level": "Avanzado"},
                    {"name": "Planificación de Roadmaps", "level": "Avanzado"},
                    {"name": "Diseño de Sistemas", "level": "Avanzado"},
                    {"name": "Test-Driven Development (TDD)", "level": "Avanzado"},
                    {"name": "Jira", "level": "Avanzado"},
                    {"name": "Notion", "level": "Avanzado"}
                ]
            },
            {
                "category": "Liderazgo & Habilidades Blandas",
                "skills": [
                    {"name": "Liderazgo Técnico", "level": "Avanzado"},
                    {"name": "Team Building", "level": "Avanzado"},
                    {"name": "Colaboración Cross-functional", "level": "Avanzado"},
                    {"name": "Comunicación Efectiva", "level": "Avanzado"},
                    {"name": "Resolución de Problemas", "level": "Avanzado"}
                ]
            }
        ]

        # 5. Synchronize Featured Projects (Personal flagships + Laboral ML pipelines)
        new_data["projects"] = [
            {
                "name": "Cute Agents Desk",
                "type": "personal",
                "description": "Panel de control y despacho de escritorio en Electron para coordinar agentes de IA CLI (Claude Code y Antigravity) en paralelo con aislamiento estricto por Git Worktrees y buzón interactivo PTY.",
                "technologies": [
                    "Electron",
                    "Node.js",
                    "Claude Code",
                    "Antigravity CLI",
                    "Git Worktrees",
                    "ES Modules"
                ],
                "repo_url": "https://github.com/AnaCataVC/cute-agents-desk",
                "demo_url": None
            },
            {
                "name": "Work Activity Panel",
                "type": "personal",
                "description": "Aplicación de escritorio nativa para Windows 11 en WinUI 3 y .NET 9 que optimiza la jornada laboral: auto-inicia herramientas, sincroniza Google Calendar con soporte RRULE, emite alertas emergentes con unión directa y conmuta cuentas GitHub CLI.",
                "technologies": [
                    "WinUI 3",
                    ".NET 9",
                    "C#",
                    "Windows App SDK",
                    "Google Calendar API",
                    "GitHub CLI"
                ],
                "repo_url": "https://github.com/AnaCataVC/work-activity-panel",
                "demo_url": "https://github.com/AnaCataVC/work-activity-panel"
            },
            {
                "name": "Interactive MCP Curriculum & Agent Server",
                "type": "personal",
                "description": "Servidor MCP oficial con transporte Streamable HTTP montado sobre FastAPI para consulta interactiva de trayectoria profesional por parte de LLMs (Claude.ai, Gemini, Cursor), preparado para despliegue Serverless en Google Cloud Run.",
                "technologies": [
                    "Python",
                    "Model Context Protocol (MCP)",
                    "FastAPI",
                    "Streamable HTTP",
                    "Docker",
                    "Google Cloud Run"
                ],
                "repo_url": "https://github.com/AnaCataVC/anacatalina-mcp",
                "demo_url": None
            },
            {
                "name": "Pipeline de Inferencia y Monitoreo de Modelos en Vertex AI",
                "type": "laboral",
                "description": "Arquitectura de entrenamiento continuo y despliegue de endpoints en Vertex AI con ingesta de datos directos desde BigQuery y containerización en Docker para simplificar el ciclo MLOps.",
                "technologies": [
                    "Python",
                    "Vertex AI",
                    "BigQuery",
                    "Docker",
                    "GCP"
                ],
                "repo_url": None,
                "demo_url": None
            },
            {
                "name": "Predictive Maintenance & Asset Telemetry Engine",
                "type": "laboral",
                "description": "Motor analítico para detección de anomalías y predicción de fallas en equipos industriales a partir de señales de telemetría IoT.",
                "technologies": [
                    "Python",
                    "SQL",
                    "Time-Series Analysis",
                    "Docker"
                ],
                "repo_url": None,
                "demo_url": None
            }
        ]

        # 6. Education & Formations
        new_data["education"] = [
            {
                "institution": "Universidad de Chile",
                "degree": "Ingeniería Civil",
                "period": "Egresada en 2019, Titulada en 2020",
                "details": "Mención en estructuras, construcción y geotecnia. Trabajo de título en Procesos Gaussianos para detección de fallas estructurales. Titulada con distinción máxima. Prácticas profesionales: EGIS y DOM Curicó (cálculo estructural y presupuestos)."
            },
            {
                "institution": "Universidad de Chile",
                "degree": "Licenciatura en Ciencias de la Ingeniería",
                "period": "Finalizada en 2017",
                "details": "Actividad destacada: Ayudante del curso Probabilidades y Estadística."
            }
        ]

        # Validate with Pydantic CVData model to guarantee 100% schema integrity
        validated = CVData(**new_data)
        return validated.model_dump()

    def sync(self) -> Tuple[bool, str]:
        """
        Execute synchronization and overwrite data/cv_data.json.
        """
        try:
            updated_dict = self.generate_synchronized_dataset()
            self.data_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.data_file, "w", encoding="utf-8") as f:
                json.dump(updated_dict, f, indent=2, ensure_ascii=False)
                f.write("\n")
            return True, f"Successfully synchronized and validated {self.data_file}"
        except Exception as exc:
            return False, f"Synchronization failed: {exc}"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit and synchronize anacatalina-mcp dataset against anacatalina-cv and projects-hub."
    )
    parser.add_argument(
        "--audit",
        action="store_true",
        default=True,
        help="Audit differences and print human-readable summary (default)."
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output audit report in structured JSON format."
    )
    parser.add_argument(
        "--sync",
        action="store_true",
        help="Apply synchronization and update data/cv_data.json."
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Exit with code 0 if in sync, or code 1 if differences are found."
    )
    parser.add_argument(
        "--cv-dir",
        type=Path,
        default=None,
        help="Custom path to anacatalina-cv repository."
    )
    parser.add_argument(
        "--projects-dir",
        type=Path,
        default=None,
        help="Custom path to projects-hub repository."
    )
    parser.add_argument(
        "--data-file",
        type=Path,
        default=None,
        help="Custom path to cv_data.json."
    )

    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent.parent
    auditor = DataAuditor(
        base_dir=project_root,
        cv_dir=args.cv_dir,
        projects_dir=args.projects_dir,
        data_file=args.data_file
    )

    if args.sync:
        success, msg = auditor.sync()
        if success:
            print(f"[OK] {msg}")
            return 0
        else:
            print(f"[ERROR] {msg}", file=sys.stderr)
            return 1

    report = auditor.audit()

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0 if (report.get("in_sync") or not args.check_only) else 1

    if args.check_only:
        if report.get("in_sync"):
            print("[OK] Dataset is fully synchronized with sibling repositories.")
            return 0
        else:
            print("[DISCREPANCY] Dataset has pending updates or missing sources.")
            return 1

    # Standard human-readable audit report
    print("=" * 70)
    print(" MCP DATA SYNCHRONIZATION AUDIT REPORT")
    print("=" * 70)
    print(f"Repository Root: {auditor.base_dir}")
    print(f"CV Source:       {auditor.cv_dir} ({'Found' if report['sources']['cv_repo_found'] else 'MISSING'})")
    print(f"Projects Source: {auditor.projects_dir} ({'Found' if report['sources']['projects_hub_found'] else 'MISSING'})")
    print(f"Target Data:     {auditor.data_file} ({'Found' if report['sources']['data_file_found'] else 'MISSING'})")
    print("-" * 70)
    print("Stats:")
    for k, v in report["stats"].items():
        print(f"  * {k}: {v}")
    print("-" * 70)

    if report["discrepancies"]:
        print(f"Discrepancies / Opportunities ({len(report['discrepancies'])}):")
        for d in report["discrepancies"]:
            if "issue" in d:
                print(f"  [!] [{d['component']}] {d['issue']}")
            else:
                print(f"  [!] [{d['component']}] Current: '{d.get('current')}' != Source: '{d.get('source')}'")
    else:
        print("[ALL SYNCED] All checked entities match perfectly.")

    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
