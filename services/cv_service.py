"""
Curriculum service providing business logic, search, filtering, and job fit evaluation.
"""
import json
import os
from pathlib import Path
from typing import List, Optional, Dict, Any

from models.cv import (
    CVData,
    ContactDetails,
    ExperienceItem,
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
        lang_key = lang.lower()
        if lang_key not in self.cv.summary:
            lang_key = "es" if "es" in self.cv.summary else list(self.cv.summary.keys())[0]
        return self.cv.summary.get(lang_key, "")

    def get_contact(self) -> ContactDetails:
        """Returns direct contact details."""
        return self.cv.personal_info.contact

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

    def evaluate_job_fit(self, job_description: str) -> FitEvaluationResult:
        """Evaluates compatibility between a job description and the candidate's profile."""
        jd_lower = job_description.lower()

        # Keywords dictionary to match
        known_tech_keywords = {
            "python": "Python",
            "gcp": "Google Cloud Platform (GCP)",
            "google cloud": "Google Cloud Platform (GCP)",
            "bigquery": "BigQuery",
            "vertex ai": "Vertex AI",
            "vertex": "Vertex AI",
            "docker": "Docker",
            "fastapi": "FastAPI",
            "sql": "SQL",
            "machine learning": "Machine Learning",
            "ml": "Machine Learning",
            "scikit-learn": "Scikit-Learn",
            "mcp": "Model Context Protocol (MCP)",
            "model context protocol": "Model Context Protocol (MCP)",
            "agent": "Architecturas de Agentes & LLMs",
            "llm": "LLMs & IA Generativa",
            "pandas": "Pandas / NumPy",
            "etl": "Pipelines de Datos / ETL",
            "cloud run": "Google Cloud Run",
            "logística": "Optimización Logística & Ruteo",
            "ruteo": "Optimización Logística & Ruteo",
        }

        matched_techs = []
        for term, label in known_tech_keywords.items():
            if term in jd_lower and label not in matched_techs:
                matched_techs.append(label)

        # Detect role
        role_detected = "Data Scientist / Machine Learning Engineer / AI Engineer"
        if "lead" in jd_lower or "senior" in jd_lower:
            role_detected = "Senior Data Scientist / Learning Engineer"

        # Calculate fit percentage estimate
        if len(matched_techs) >= 4:
            fit_score = "95% (Alineación Excepcional)"
        elif len(matched_techs) >= 2:
            fit_score = "85% (Alta Compatibilidad)"
        elif len(matched_techs) >= 1:
            fit_score = "75% (Buena Compatibilidad)"
        else:
            fit_score = "70% (Perfil Transferible en Data/IA)"

        strengths = [
            "Experiencia real en producción optimizando modelos analíticos y pipelines en SimpliRoute y Fracttal.",
            "Dominio profundo del stack moderno de datos en GCP (BigQuery + Vertex AI) y despliegues con Docker y FastAPI.",
            "Capacidad probada para diseñar e implementar soluciones de IA aplicada y protocolos avanzados de agentes (MCP)."
        ]

        summary = (
            f"El perfil de Ana Catalina presenta un fit sobresaliente para la posición descrita. "
            f"Aporta experiencia directa en {', '.join(matched_techs[:4]) if matched_techs else 'Python y Data Science'}, "
            f"con fuerte capacidad de entrega tanto en ingeniería de datos como en prototipado y producción de modelos ML."
        )

        return FitEvaluationResult(
            target_role_detected=role_detected,
            estimated_fit_score=fit_score,
            matching_strengths=strengths,
            technologies_matched=matched_techs,
            added_value_summary=summary,
        )


# Singleton instance
_service_instance: Optional[CVService] = None


def get_cv_service() -> CVService:
    """Returns singleton instance of CVService."""
    global _service_instance
    if _service_instance is None:
        _service_instance = CVService()
    return _service_instance
