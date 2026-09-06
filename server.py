"""
server.py - Interactive Curriculum MCP Server with SSE Transport.
Configured for Google Cloud Run deployment and local inspection.
"""
import os
from pathlib import Path
from typing import List, Optional, Dict, Any
from starlette.requests import Request
from starlette.responses import JSONResponse, HTMLResponse, FileResponse, Response
from mcp.server.fastmcp import FastMCP

from models.cv import (
    ExperienceItem,
    SkillCategory,
    ProjectItem,
    EducationItem,
    ContactDetails,
    PersonalInfo,
    FitEvaluationResult,
)
from services.cv_service import get_cv_service

# 1. Initialize FastMCP instance bound to 0.0.0.0 for Cloud Run
port = int(os.environ.get("PORT", 8080))
host = os.environ.get("HOST", "0.0.0.0")
mcp = FastMCP("Ana-Catalina Interactive Portfolio MCP", host=host, port=port)
cv_service = get_cv_service()


# 2. Register MCP Tools
@mcp.tool(
    name="obtener_experiencia",
    description="Devuelve el historial laboral y experiencia profesional de Ana-Catalina (SimpliRoute, Fracttal, etc.), con responsabilidades y tecnologías empleadas. Permite filtrar por empresa."
)
async def obtener_experiencia(empresa: Optional[str] = None) -> List[ExperienceItem]:
    """Obtiene la experiencia laboral filtrada opcionalmente por nombre de empresa."""
    return cv_service.get_experience(company=empresa)


@mcp.tool(
    name="obtener_stack_tecnologico",
    description="Devuelve las tecnologías, lenguajes (Python, SQL), herramientas de Cloud/GCP (BigQuery, Vertex AI), Docker y frameworks dominados por Ana-Catalina, organizados por categoría y con su nivel de dominio (Avanzado, Intermedio)."
)
async def obtener_stack_tecnologico(
    categoria: Optional[str] = None,
    nivel: Optional[str] = None
) -> List[SkillCategory]:
    """Obtiene las habilidades técnicas y herramientas con niveles, con filtros opcionales."""
    return cv_service.get_skills(category=categoria, level=nivel)


@mcp.tool(
    name="obtener_proyectos_destacados",
    description="Devuelve los proyectos insignia de Ana-Catalina (laborales y personales), describiendo su objetivo, arquitectura, tecnologías utilizadas (MCP, FastAPI, Vertex AI, Docker) y enlaces a repositorios o demos."
)
async def obtener_proyectos_destacados(
    tipo: Optional[str] = None,
    tecnologia: Optional[str] = None
) -> List[ProjectItem]:
    """Obtiene proyectos destacados filtrados opcionalmente por tipo ('laboral' o 'personal') o tecnología."""
    return cv_service.get_projects(project_type=tipo, technology=tecnologia)


@mcp.tool(
    name="evaluar_fit_puesto",
    description="Devuelve la evaluación de alineación técnica para escenarios predefinidos o perfiles estándar de mercado (Senior Data Scientist, Especialista en Logística/Ruteo, Ingeniera en IA/Agentes MCP)."
)
async def evaluar_fit_puesto(descripcion_vacante: str) -> FitEvaluationResult:
    """Evalúa la alineación técnica entre un rol o escenario y el perfil de Ana-Catalina."""
    return cv_service.evaluate_job_fit(scenario_or_description=descripcion_vacante)


@mcp.tool(
    name="buscar_en_curriculum",
    description="Realiza una búsqueda transversal por palabra clave en todo el currículum de Ana-Catalina (experiencia, tecnologías, proyectos y responsabilidades)."
)
async def buscar_en_curriculum(consulta: str) -> Dict[str, Any]:
    """Busca cualquier término en el historial laboral, proyectos y habilidades."""
    return cv_service.search(query=consulta)


@mcp.tool(
    name="obtener_educacion",
    description="Devuelve la formación académica formal y estudios universitarios de Ana-Catalina."
)
async def obtener_educacion() -> List[EducationItem]:
    """Obtiene el historial de formación académica formal."""
    return cv_service.get_education()


@mcp.tool(
    name="obtener_contacto",
    description="Devuelve los canales directos de contacto profesional de Ana-Catalina (Email directo y perfil de LinkedIn)."
)
async def obtener_contacto() -> ContactDetails:
    """Obtiene la información de contacto directo."""
    return cv_service.get_contact()


@mcp.tool(
    name="obtener_perfil",
    description="Devuelve el perfil general de Ana-Catalina: nombre profesional ('Ana-Catalina Villalobos Contardo'), nombre de pila ('Ana-Catalina'), segundo nombre ('Alejandra'), apellidos ('Villalobos Contardo'), nombre completo oficial ('Ana-Catalina Alejandra Villalobos Contardo'), cargo actual, ubicación y enlaces de portafolio (incluyendo GitHub)."
)
async def obtener_perfil() -> PersonalInfo:
    """Obtiene la información general del perfil profesional."""
    return cv_service.get_profile()


@mcp.tool(
    name="obtener_resumen_ejecutivo",
    description="Devuelve el resumen ejecutivo del perfil profesional de Ana-Catalina enfocado en Data Science, Machine Learning, GCP y arquitecturas MCP. Soporta idiomas 'es' o 'en'."
)
async def obtener_resumen_ejecutivo(idioma: str = "es") -> str:
    """Obtiene la síntesis ejecutiva del perfil profesional en español o inglés."""
    return cv_service.get_summary(lang=idioma)


# 3. Template Cache & Content Negotiation
_TEMPLATE_PATH = Path(__file__).resolve().parent / "templates" / "index.html"
_CACHED_HTML: Optional[str] = None


def get_showcase_html() -> str:
    """Returns the cached showcase HTML template, reloading on debug."""
    global _CACHED_HTML
    if _CACHED_HTML is None or os.environ.get("DEBUG") == "1":
        if _TEMPLATE_PATH.exists():
            with open(_TEMPLATE_PATH, "r", encoding="utf-8") as f:
                _CACHED_HTML = f.read()
        else:
            _CACHED_HTML = (
                "<!DOCTYPE html><html lang='es'><head><meta charset='UTF-8'>"
                "<title>Ana-Catalina MCP</title></head><body>"
                "<h1>Ana-Catalina Interactive Portfolio MCP</h1>"
                "<p>Showcase template not yet initialized.</p></body></html>"
            )
    return _CACHED_HTML


DISCOVERY_PAYLOAD: Dict[str, Any] = {
    "name": "Ana-Catalina Interactive Portfolio MCP",
    "status": "healthy",
    "version": "1.0.0",
    "sse_endpoint": "/sse",
    "messages_endpoint": "/messages/",
    "health_endpoint": "/health",
    "web_showcase": "/",
    "demo_endpoint": "/demo",
}


# 4. Register Custom Routes (Web Showcase, Standalone REST APIs & Health Check)
@mcp.custom_route("/", methods=["GET"])
async def root_info(request: Request):
    """Root endpoint: serves interactive showcase HTML to browsers and JSON discovery to APIs."""
    accept_header = request.headers.get("accept", "").lower()
    if "text/html" in accept_header:
        return HTMLResponse(
            content=get_showcase_html(),
            status_code=200,
            headers={"Cache-Control": "no-cache, must-revalidate"},
        )
    return JSONResponse(DISCOVERY_PAYLOAD)


@mcp.custom_route("/demo", methods=["GET"])
async def demo_page(request: Request):
    """Direct web showcase endpoint."""
    return HTMLResponse(
        content=get_showcase_html(),
        status_code=200,
        headers={"Cache-Control": "no-cache, must-revalidate"},
    )


@mcp.custom_route("/favicon.svg", methods=["GET"])
async def favicon_svg(request: Request):
    """Serves the official brand logo SVG."""
    svg_path = Path(__file__).resolve().parent / "favicon.svg"
    if svg_path.exists():
        return FileResponse(svg_path, media_type="image/svg+xml")
    return Response(status_code=404)


@mcp.custom_route("/favicon.ico", methods=["GET"])
async def favicon_ico(request: Request):
    """Serves the favicon.ico."""
    ico_path = Path(__file__).resolve().parent / "favicon.ico"
    if ico_path.exists():
        return FileResponse(ico_path, media_type="image/x-icon")
    return Response(status_code=404)


@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request):
    """Health check endpoint for Google Cloud Run container liveness."""
    return JSONResponse({
        "status": "healthy",
        "service": "anacatalina-mcp",
        "version": "1.0.0",
        "transports": ["SSE (/sse)", "POST (/messages/)"],
    })


@mcp.custom_route("/api/evaluate-fit", methods=["POST"])
async def api_evaluate_fit(request: Request):
    """Standalone REST endpoint: evaluates benchmark role compatibility via direct HTTP."""
    try:
        data = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid JSON body."}, status_code=400)

    if not isinstance(data, dict):
        return JSONResponse({"error": "Request body must be a JSON object."}, status_code=400)

    scenario = data.get("scenario") or data.get("job_description")
    if not scenario or not isinstance(scenario, str) or not scenario.strip():
        return JSONResponse(
            {"error": "Field 'scenario' or 'job_description' is required and must not be empty."},
            status_code=400,
        )

    result = cv_service.evaluate_job_fit(scenario_or_description=scenario.strip())
    return JSONResponse(result.model_dump(), status_code=200)


@mcp.custom_route("/api/search", methods=["GET"])
async def api_search(request: Request):
    """Standalone REST endpoint: cross-curriculum keyword search across experience, skills, and projects via direct HTTP."""
    query = request.query_params.get("q", "")
    res = cv_service.search(query=query)
    payload = {
        "query": res["query"],
        "matched_experiences_count": res["matched_experiences_count"],
        "experiences": [e.model_dump() for e in res["experiences"]],
        "matched_skills": res["matched_skills"],
        "matched_projects_count": res["matched_projects_count"],
        "projects": [p.model_dump() for p in res["projects"]],
    }
    return JSONResponse(payload, status_code=200)


@mcp.custom_route("/api/skills", methods=["GET"])
async def api_skills(request: Request):
    """Standalone REST endpoint: returns technical skill taxonomy with optional category and level filters."""
    category = request.query_params.get("category")
    level = request.query_params.get("level")
    skills = cv_service.get_skills(category=category, level=level)
    return JSONResponse([cat.model_dump() for cat in skills], status_code=200)


@mcp.custom_route("/api/projects", methods=["GET"])
async def api_projects(request: Request):
    """Standalone REST endpoint: returns featured projects with optional type and technology filters."""
    p_type = request.query_params.get("type")
    technology = request.query_params.get("technology")
    projects = cv_service.get_projects(project_type=p_type, technology=technology)
    return JSONResponse([proj.model_dump() for proj in projects], status_code=200)


# 5. Generate ASGI Application for SSE Transport
app = mcp.sse_app()


if __name__ == "__main__":
    import uvicorn
    print(f"Starting MCP Server on http://{host}:{port}/sse")
    uvicorn.run(app, host=host, port=port, log_level="info")

