"""
server.py - Interactive Curriculum MCP Server with SSE Transport.
Configured for Google Cloud Run deployment and local inspection.
"""
import os
from typing import List, Optional, Dict, Any
from starlette.requests import Request
from starlette.responses import JSONResponse
from mcp.server.fastmcp import FastMCP

from models.cv import (
    ExperienceItem,
    SkillCategory,
    ProjectItem,
    EducationItem,
    ContactDetails,
    FitEvaluationResult,
)
from services.cv_service import get_cv_service

# 1. Initialize FastMCP instance bound to 0.0.0.0 for Cloud Run
port = int(os.environ.get("PORT", 8080))
host = os.environ.get("HOST", "0.0.0.0")
mcp = FastMCP("Ana Catalina Interactive Portfolio MCP", host=host, port=port)
cv_service = get_cv_service()


# 2. Register MCP Tools
@mcp.tool(
    name="obtener_experiencia",
    description="Devuelve el historial laboral y experiencia profesional de Ana Catalina (SimpliRoute, Fracttal, etc.), con responsabilidades y tecnologías empleadas. Permite filtrar por empresa."
)
async def obtener_experiencia(empresa: Optional[str] = None) -> List[ExperienceItem]:
    """Obtiene la experiencia laboral filtrada opcionalmente por nombre de empresa."""
    return cv_service.get_experience(company=empresa)


@mcp.tool(
    name="obtener_stack_tecnologico",
    description="Devuelve las tecnologías, lenguajes (Python, SQL), herramientas de Cloud/GCP (BigQuery, Vertex AI), Docker y frameworks dominados por Ana Catalina, organizados por categoría y con su nivel de dominio (Avanzado, Intermedio)."
)
async def obtener_stack_tecnologico(
    categoria: Optional[str] = None,
    nivel: Optional[str] = None
) -> List[SkillCategory]:
    """Obtiene las habilidades técnicas y herramientas con niveles, con filtros opcionales."""
    return cv_service.get_skills(category=categoria, level=nivel)


@mcp.tool(
    name="obtener_proyectos_destacados",
    description="Devuelve los proyectos insignia de Ana Catalina (laborales y personales), describiendo su objetivo, arquitectura, tecnologías utilizadas (MCP, FastAPI, Vertex AI, Docker) y enlaces a repositorios o demos."
)
async def obtener_proyectos_destacados(
    tipo: Optional[str] = None,
    tecnologia: Optional[str] = None
) -> List[ProjectItem]:
    """Obtiene proyectos destacados filtrados opcionalmente por tipo ('laboral' o 'personal') o tecnología."""
    return cv_service.get_projects(project_type=tipo, technology=tecnologia)


@mcp.tool(
    name="evaluar_fit_puesto",
    description="Analiza la descripción o requerimientos de una vacante laboral y evalúa el porcentaje de compatibilidad, fortalezas técnicas coincidentes y valor agregado del perfil de Ana Catalina."
)
async def evaluar_fit_puesto(descripcion_vacante: str) -> FitEvaluationResult:
    """Evalúa la compatibilidad entre una descripción de puesto y el perfil de Ana Catalina."""
    return cv_service.evaluate_job_fit(job_description=descripcion_vacante)


@mcp.tool(
    name="buscar_en_curriculum",
    description="Realiza una búsqueda transversal por palabra clave en todo el currículum de Ana Catalina (experiencia, tecnologías, proyectos y responsabilidades)."
)
async def buscar_en_curriculum(consulta: str) -> Dict[str, Any]:
    """Busca cualquier término en el historial laboral, proyectos y habilidades."""
    return cv_service.search(query=consulta)


@mcp.tool(
    name="obtener_educacion",
    description="Devuelve la formación académica formal y estudios universitarios de Ana Catalina."
)
async def obtener_educacion() -> List[EducationItem]:
    """Obtiene el historial de formación académica formal."""
    return cv_service.get_education()


@mcp.tool(
    name="obtener_contacto",
    description="Devuelve los canales directos de contacto profesional de Ana Catalina (Email directo y perfil de LinkedIn)."
)
async def obtener_contacto() -> ContactDetails:
    """Obtiene la información de contacto directo."""
    return cv_service.get_contact()


@mcp.tool(
    name="obtener_resumen_ejecutivo",
    description="Devuelve el resumen ejecutivo del perfil profesional de Ana Catalina enfocado en Data Science, Machine Learning, GCP y arquitecturas MCP. Soporta idiomas 'es' o 'en'."
)
async def obtener_resumen_ejecutivo(idioma: str = "es") -> str:
    """Obtiene la síntesis ejecutiva del perfil profesional en español o inglés."""
    return cv_service.get_summary(lang=idioma)


# 3. Register Custom Routes (Health Check & Info)
@mcp.custom_route("/", methods=["GET"])
async def root_info(request: Request):
    """Root endpoint for Cloud Run default probe and server discovery."""
    return JSONResponse({
        "name": "Ana Catalina Interactive Portfolio MCP",
        "status": "healthy",
        "version": "1.0.0",
        "sse_endpoint": "/sse",
        "messages_endpoint": "/messages/",
        "health_endpoint": "/health"
    })


@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request):
    """Health check endpoint for Google Cloud Run container liveness."""
    return JSONResponse({
        "status": "healthy",
        "service": "anacatalina-mcp",
        "version": "1.0.0",
        "transports": ["SSE (/sse)", "POST (/messages/)"]
    })


# 4. Generate ASGI Application for SSE Transport
app = mcp.sse_app()


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    host = os.environ.get("HOST", "0.0.0.0")
    print(f"Starting MCP Server on http://{host}:{port}/sse")
    uvicorn.run(app, host=host, port=port, log_level="info")

