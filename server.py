"""
server.py - Interactive Curriculum MCP Server with SSE Transport over FastAPI.
Configured for Google Cloud Run deployment and local inspection.
"""
import os
import sys
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, Request
from starlette.routing import Route, Mount
from starlette.applications import Starlette
from mcp.server.fastmcp import FastMCP
from mcp.server.sse import SseServerTransport

from models.cv import (
    ExperienceItem,
    SkillCategory,
    ProjectItem,
    EducationItem,
    ContactDetails,
    FitEvaluationResult,
)
from services.cv_service import get_cv_service

# 1. Initialize FastMCP instance
mcp = FastMCP("Ana Catalina Interactive Portfolio MCP")
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


# 3. Setup SSE Transport & FastAPI Application
sse_transport = SseServerTransport("/messages/")


async def handle_sse(request: Request):
    """GET /sse endpoint establishing bidirectional MCP event stream."""
    async with sse_transport.connect_sse(
        request.scope, request.receive, request._send
    ) as (read_stream, write_stream):
        await mcp._mcp_server.run(
            read_stream,
            write_stream,
            mcp._mcp_server.create_initialization_options()
        )


# Starlette Sub-App for SSE streaming & POST message routing
sse_app = Starlette(
    routes=[
        Route("/sse", endpoint=handle_sse, methods=["GET"]),
        Mount("/messages/", app=sse_transport.handle_post_message),
    ]
)

# FastAPI Main Application
app = FastAPI(
    title="Ana Catalina - Interactive Curriculum MCP Server",
    description="Official Model Context Protocol (MCP) server providing interactive CV data via SSE.",
    version="1.0.0",
)


@app.get("/health", tags=["Monitoring"])
async def health_check():
    """Health check endpoint for Google Cloud Run container liveness."""
    return {
        "status": "healthy",
        "service": "anacatalina-mcp",
        "version": "1.0.0",
        "transports": ["SSE (/sse)", "POST (/messages/)"]
    }


# Mount SSE routes at root level
app.mount("/", sse_app)


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8080"))
    host = os.getenv("HOST", "0.0.0.0")
    print(f"Starting MCP Server on http://{host}:{port}/sse")
    uvicorn.run("server:app", host=host, port=port, reload=True)
