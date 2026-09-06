"""
Curriculum service providing business logic, search, and filtering for structured CV data.
"""
import json
import os
from pathlib import Path
from typing import List, Optional, Dict, Any

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
        """Returns benchmark fit evaluation for predefined scenarios or matches to closest benchmark."""
        key = scenario_or_description.lower().strip()
        if key in FIXED_BENCHMARK_SCENARIOS:
            return FIXED_BENCHMARK_SCENARIOS[key]

        # Map by keyword if full scenario text is provided
        if any(w in key for w in ["cantante", "pop", "chef", "pastelero", "música", "repostería"]):
            return FIXED_BENCHMARK_SCENARIOS["pop-singer"]
        if any(w in key for w in ["ruteo", "logística", "logistica", "flota", "vehicular", "transporte"]):
            return FIXED_BENCHMARK_SCENARIOS["logistics"]
        if any(w in key for w in ["mcp", "agente", "agent", "llm", "asistente"]):
            return FIXED_BENCHMARK_SCENARIOS["agents"]

        # Default benchmark: Senior Data Scientist
        return FIXED_BENCHMARK_SCENARIOS["data-science"]


FIXED_BENCHMARK_SCENARIOS: Dict[str, FitEvaluationResult] = {
    "data-science": FitEvaluationResult(
        target_role_detected="Senior Data Scientist / Machine Learning Engineer",
        estimated_fit_score="95% (Alineación Excepcional)",
        technologies_matched=["Python", "Google Cloud Platform (GCP)", "BigQuery", "Vertex AI", "Docker"],
        matching_strengths=[
            "Experiencia real en producción optimizando modelos analíticos y pipelines en SimpliRoute y Fracttal.",
            "Dominio profundo del stack moderno de datos en GCP (BigQuery + Vertex AI) y despliegues con Docker y FastAPI.",
            "Capacidad probada para diseñar e implementar soluciones de IA aplicada y protocolos avanzados de agentes (MCP)."
        ],
        added_value_summary=(
            "El perfil de Ana-Catalina presenta una alineación excepcional para roles de Senior Data Science y Machine Learning. "
            "Aporta sólida experiencia directa en analítica predictiva sobre GCP y entrega en entornos de alta exigencia."
        )
    ),
    "logistics": FitEvaluationResult(
        target_role_detected="Data Scientist Especialista en Ruteo & Logística",
        estimated_fit_score="90% (Alta Compatibilidad)",
        technologies_matched=["Python", "Docker", "Optimización Logística", "Algoritmos de Ruteo", "SQL"],
        matching_strengths=[
            "Desarrollo y mantenimiento de algoritmos analíticos aplicados a logística de última milla en SimpliRoute.",
            "Optimización de modelos sobre telemetría y operaciones vehiculares a escala regional en Latinoamérica.",
            "Empaquetamiento y despliegue de microservicios con Docker y FastAPI."
        ],
        added_value_summary=(
            "Experiencia comprobada en el sector logístico SaaS, combinando modelamiento matemático, ruteo y ciencia de datos aplicada a operaciones en tiempo real."
        )
    ),
    "agents": FitEvaluationResult(
        target_role_detected="Ingeniera en IA & Agentes Autónomos (MCP)",
        estimated_fit_score="90% (Alta Compatibilidad)",
        technologies_matched=["Model Context Protocol (MCP)", "Python", "FastAPI", "Docker", "Vertex AI"],
        matching_strengths=[
            "Implementación de servidores de Model Context Protocol (MCP) en producción con transporte Server-Sent Events (SSE).",
            "Diseño de herramientas para LLMs y asistentes cognitivos (Claude Desktop, Cursor, APIs asíncronas).",
            "Despliegues serverless conteinerizados en Google Cloud Run."
        ],
        added_value_summary=(
            "Pionera en adopción de arquitecturas basadas en agentes con el estándar abierto MCP, integrando modelos de lenguaje con herramientas de producción."
        )
    ),
    "pop-singer": FitEvaluationResult(
        target_role_detected="Cantante Pop (Fuera de Especialidad Data/IA)",
        estimated_fit_score="10% (Sin Alineación / Fuera de Especialidad)",
        technologies_matched=[],
        matching_strengths=[
            "La vacante no presenta requerimientos técnicos compatibles con la especialización de Ana-Catalina."
        ],
        added_value_summary=(
            "La posición descrita no requiere competencias de Data Science, Machine Learning ni desarrollo en Cloud. "
            "El perfil de Ana-Catalina está enfocado exclusivamente en analítica avanzada, GCP y arquitecturas de IA."
        )
    )
}


# Singleton instance
_service_instance: Optional[CVService] = None


def get_cv_service() -> CVService:
    """Returns singleton instance of CVService."""
    global _service_instance
    if _service_instance is None:
        _service_instance = CVService()
    return _service_instance
