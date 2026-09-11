"""
Curriculum service providing business logic, search, and filtering for structured CV data.
"""
import json
import os
import re
from pathlib import Path
from typing import List, Optional, Dict, Any, Set, Tuple

from models.cv import (
    CVData,
    ContactDetails,
    ExperienceItem,
    PersonalInfo,
    SkillCategory,
    SkillItem,
    ProjectItem,
    EducationItem,
    FitEvaluationResult,
)


class CVService:
    """Service to load, filter, query, and evaluate curriculum data."""

    def __init__(self, data_path: Optional[str] = None):
        if data_path is None:
            base_dir = Path(__file__).resolve().parent.parent
            data_path = os.getenv("CV_DATA_PATH", str(base_dir / "data" / "cv_data.json"))
        
        self.data_path = Path(data_path)
        self.cv: CVData = self._load_data()

    def _load_data(self) -> CVData:
        """Loads and validates JSON curriculum data against Pydantic schema."""
        if not self.data_path.exists():
            raise FileNotFoundError(f"CV data file not found at: {self.data_path}")
        
        with open(self.data_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
        
        return CVData.model_validate(raw_data)

    def get_summary(self, lang: str = "es") -> str:
        """Returns executive summary in the requested language."""
        if not self.cv.summary:
            return ""
        lang_key = lang.lower()
        if lang_key not in self.cv.summary:
            lang_key = "es" if "es" in self.cv.summary else next(iter(self.cv.summary))
        return self.cv.summary.get(lang_key, "")

    def get_contact(self) -> ContactDetails:
        """Returns direct contact details."""
        return self.cv.personal_info.contact

    def get_profile(self) -> PersonalInfo:
        """Returns the general profile: name, title, location and portfolio links."""
        return self.cv.personal_info

    def get_experience(self, company: Optional[str] = None) -> List[ExperienceItem]:
        """Returns work experience, optionally filtered by company name."""
        if not company:
            return self.cv.experience
        
        query = company.lower().strip()
        return [
            exp for exp in self.cv.experience
            if query in exp.company.lower()
        ]

    def get_skills(
        self,
        category: Optional[str] = None,
        level: Optional[str] = None
    ) -> List[SkillCategory]:
        """Returns tech stack filtered by category and/or proficiency level."""
        filtered_categories: List[SkillCategory] = []

        for cat in self.cv.skills:
            if category and category.lower() not in cat.category.lower():
                continue
            
            matching_skills: List[SkillItem] = []
            for skill in cat.skills:
                if level and level.lower() not in skill.level.lower():
                    continue
                matching_skills.append(skill)
            
            if matching_skills:
                filtered_categories.append(
                    SkillCategory(category=cat.category, skills=matching_skills)
                )

        return filtered_categories

    def get_projects(
        self,
        project_type: Optional[str] = None,
        technology: Optional[str] = None
    ) -> List[ProjectItem]:
        """Returns featured projects filtered by type ('personal', 'laboral') or technology."""
        results = self.cv.projects

        if project_type:
            pt = project_type.lower().strip()
            results = [p for p in results if pt in p.type.lower()]

        if technology:
            tech_query = technology.lower().strip()
            results = [
                p for p in results
                if any(tech_query in t.lower() for t in p.technologies)
            ]

        return results

    def get_education(self) -> List[EducationItem]:
        """Returns formal academic education history."""
        return self.cv.education

    def search(self, query: str) -> Dict[str, Any]:
        """Performs cross-cutting keyword search across experience, skills, and projects."""
        q = query.lower().strip()
        matched_experience = [
            exp for exp in self.cv.experience
            if q in exp.company.lower()
            or q in exp.role.lower()
            or any(q in r.lower() for r in exp.responsibilities)
            or any(q in t.lower() for t in exp.technologies)
        ]

        matched_skills: List[str] = []
        for cat in self.cv.skills:
            for s in cat.skills:
                if q in s.name.lower() or q in cat.category.lower():
                    matched_skills.append(f"{s.name} ({s.level} - {cat.category})")

        matched_projects = [
            proj for proj in self.cv.projects
            if q in proj.name.lower()
            or q in proj.description.lower()
            or any(q in t.lower() for t in proj.technologies)
        ]

        return {
            "query": query,
            "matched_experiences_count": len(matched_experience),
            "experiences": matched_experience,
            "matched_skills": matched_skills,
            "matched_projects_count": len(matched_projects),
            "projects": matched_projects,
        }

    def evaluate_job_fit(self, scenario_or_description: str) -> FitEvaluationResult:
        """Dynamically evaluates fit against candidate's real CV skills, technologies, and experience."""
        text = scenario_or_description.strip()
        lower_text = text.lower()

        # Handle canonical preset aliases for seamless integration
        if lower_text in ["data-science", "datascience"]:
            query_text = "data science machine learning python gcp bigquery vertex ai docker analitica"
        elif lower_text in ["logistics", "logistica", "logística"]:
            query_text = "ruteo logistica optimizacion routing python docker sql telemetria flotas"
        elif lower_text in ["agents", "agentes", "mcp-agents"]:
            query_text = "mcp model context protocol agentes llm genai fastapi docker vertex ai python"
        else:
            query_text = lower_text

        # 1. Detect matching technologies against CV skills catalog
        matched_technologies: List[str] = []
        seen_canonical: Set[str] = set()

        for pattern, canonical_name in TECH_ALIAS_MAP:
            if re.search(pattern, query_text, re.IGNORECASE):
                if canonical_name not in seen_canonical:
                    seen_canonical.add(canonical_name)
                    matched_technologies.append(canonical_name)

        # 2. Case: Zero technical matches (Non-technical or completely unrelated roles)
        if not matched_technologies:
            return FitEvaluationResult(
                target_role_detected="Vacante Fuera de Especialidad / Sin Coincidencias Técnicas",
                estimated_fit_score="0% (Sin Coincidencias Técnicas / Fuera de Especialidad)",
                technologies_matched=[],
                matching_strengths=[
                    "La descripción analizada no presenta requerimientos técnicos coincidentes con las competencias centrales de Ana-Catalina (Data Science, Machine Learning, GCP, Python, MCP)."
                ],
                added_value_summary=(
                    "No se detectó afinidad técnica directa entre el perfil solicitado y la trayectoria de Ana-Catalina. "
                    "El agente evaluador puede confirmar con certeza objetiva que esta posición queda fuera de su especialidad técnica."
                )
            )

        # 3. Calculate dynamic fit score based on matched tech density
        count = len(matched_technologies)
        if count >= 5:
            score_str = f"{min(95, 80 + count * 3)}% (Alineación Excepcional)"
        elif count >= 3:
            score_str = f"{65 + count * 5}% (Alta Compatibilidad)"
        else:
            score_str = f"{min(50, count * 25)}% (Coincidencia Parcial)"

        # 4. Generate contextual matching strengths from real career history
        strengths: List[str] = []

        simpliroute_techs = {"Python", "Google Cloud Platform (GCP)", "BigQuery", "Google Pub/Sub", "Apache Airflow", "Model Context Protocol (MCP)", "LLMs & GenAI", "Algoritmos de Ruteo & Logística", "Optimización Logística"}
        matched_simpliroute = [t for t in matched_technologies if t in simpliroute_techs]
        if matched_simpliroute:
            strengths.append(
                f"Experiencia en producción en SimpliRoute aplicando {', '.join(matched_simpliroute[:3])} en optimización logística y servidores MCP."
            )

        fracttal_techs = {"Python", "Machine Learning", "Estadística & Probabilidad", "ETLs & Pipelines de Datos", "PostgreSQL", "SQL", "Liderazgo Técnico"}
        matched_fracttal = [t for t in matched_technologies if t in fracttal_techs]
        if matched_fracttal:
            strengths.append(
                f"Trayectoria en Fracttal liderando pipelines analíticos, mantenimiento predictivo y despliegues con {', '.join(matched_fracttal[:3])}."
            )

        gcp_techs = {"Google Cloud Platform (GCP)", "BigQuery", "Vertex AI", "Google Cloud Run"}
        matched_gcp = [t for t in matched_technologies if t in gcp_techs]
        if matched_gcp:
            strengths.append(
                f"Dominio profundo del ecosistema de datos y cloud en Google Cloud ({', '.join(matched_gcp)})."
            )

        if not strengths:
            strengths.append(
                f"Competencias comprobadas en el stack técnico identificado: {', '.join(matched_technologies[:4])}."
            )

        # 5. Infer role classification
        if any(t in matched_technologies for t in ["Model Context Protocol (MCP)", "Sistemas Multi-Agente"]):
            role_detected = "Ingeniera en IA & Agentes Autónomos / Machine Learning Engineer"
        elif any(t in matched_technologies for t in ["Algoritmos de Ruteo & Logística", "Optimización Logística"]):
            role_detected = "Data Scientist Especialista en Ruteo & Logística"
        elif any(t in matched_technologies for t in ["Vertex AI", "BigQuery", "Machine Learning", "Data Science & Modelamiento Predictivo"]):
            role_detected = "Senior Data Scientist / Machine Learning Engineer"
        else:
            role_detected = "Especialista en Datos & Software / Machine Learning"

        # 6. Synthesize added value
        tech_list_str = ", ".join(matched_technologies[:4])
        added_value = (
            f"El perfil de Ana-Catalina ofrece alta sinergia en {tech_list_str}, combinando experiencia real en producción "
            "en startups tecnológicas de alto crecimiento con sólida formación en ingeniería civil, analítica avanzada y modelamiento predictivo."
        )

        return FitEvaluationResult(
            target_role_detected=role_detected,
            estimated_fit_score=score_str,
            technologies_matched=matched_technologies,
            matching_strengths=strengths,
            added_value_summary=added_value
        )


# Mapping of regex search patterns to canonical CV technologies
TECH_ALIAS_MAP: List[Tuple[str, str]] = [
    (r"\bpython\b", "Python"),
    (r"\bsql\b", "SQL"),
    (r"\bbigquery\b", "BigQuery"),
    (r"\bvertex\s*ai\b", "Vertex AI"),
    (r"\bmcp\b|\bmodel\s+context\s+protocol\b", "Model Context Protocol (MCP)"),
    (r"\bgcp\b|\bgoogle\s+cloud(\s+platform)?\b", "Google Cloud Platform (GCP)"),
    (r"\bdocker\b", "Docker"),
    (r"\bfastapi\b", "FastAPI"),
    (r"\bairflow\b|\bapache\s+airflow\b", "Apache Airflow"),
    (r"\bpub/?sub\b", "Google Pub/Sub"),
    (r"\bpostgres(ql)?\b", "PostgreSQL"),
    (r"\bmachine\s+learning\b|\bml\b", "Machine Learning"),
    (r"\bdata\s+science\b|\bciencia\s+de\s+datos\b", "Data Science & Modelamiento Predictivo"),
    (r"\bllms?\b|\bgenai\b|\bia\s+generativa\b|\bgenerative\s+ai\b", "LLMs & GenAI"),
    (r"\bagentes?\b|\bmulti-?agent\b|\bsistemas\s+multi-?agente\b", "Sistemas Multi-Agente"),
    (r"\bruteo\b|\brouting\b", "Algoritmos de Ruteo & Logística"),
    (r"\blog[ií]stica\b|\blast\s+mile\b|\b[uú]ltima\s+milla\b|\bflotas?\b", "Optimización Logística"),
    (r"\betls?\b|\bdata\s+pipelines?\b|\bpipelines?\s+de\s+datos\b", "ETLs & Pipelines de Datos"),
    (r"\blangchain\b", "LangChain"),
    (r"\btensorflow\b", "TensorFlow"),
    (r"\bcloud\s+run\b", "Google Cloud Run"),
    (r"\bprompt\s+engineering\b", "Prompt Engineering"),
    (r"\bclaude(\s+code)?\b", "Claude Code"),
    (r"\bestad[ií]stica\b", "Estadística & Probabilidad"),
    (r"\bpredictiv[oa]\b", "Mantenimiento & Modelado Predictivo"),
    (r"\btelemetr[ií]a\b", "Telemetría & IoT"),
    (r"\bwinui\s*3?\b|\bxaml\b", "WinUI 3 (.NET 9 / XAML)"),
    (r"\bc#\b|\b\.net\b", "C# (.NET)"),
    (r"\btypescript\b", "TypeScript"),
    (r"\bjavascript\b", "JavaScript"),
    (r"\bgit\b|\bgithub\b", "Git & GitHub"),
    (r"\bliderazgo(\s+t[eé]cnico)?\b|\bleadership\b", "Liderazgo Técnico"),
]


# Singleton instance
_service_instance: Optional[CVService] = None


def get_cv_service() -> CVService:
    """Returns singleton instance of CVService."""
    global _service_instance
    if _service_instance is None:
        _service_instance = CVService()
    return _service_instance
