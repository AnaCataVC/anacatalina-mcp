"""
server.py - Interactive Curriculum MCP Server with Streamable HTTP Transport.
Configured for Google Cloud Run deployment and local inspection.
"""
import functools
import os
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
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
    SearchResult,
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
    description="Evalúa dinámicamente la afinidad técnica entre cualquier descripción de vacante o rol y el currículum de Ana-Catalina, identificando tecnologías coincidentes, nivel de compatibilidad objetivo (0% a 95%) y fortalezas laborales en SimpliRoute y Fracttal."
)
async def evaluar_fit_puesto(descripcion_vacante: str) -> FitEvaluationResult:
    """Evalúa la alineación técnica entre una vacante y el perfil de Ana-Catalina."""
    return cv_service.evaluate_job_fit(scenario_or_description=descripcion_vacante)


@mcp.tool(
    name="buscar_en_curriculum",
    description="Realiza una búsqueda transversal por palabra clave en todo el currículum de Ana-Catalina (experiencia, tecnologías, proyectos y responsabilidades)."
)
async def buscar_en_curriculum(consulta: str) -> SearchResult:
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
_BASE_DIR = Path(__file__).resolve().parent
_TEMPLATE_PATH = _BASE_DIR / "templates" / "index.html"


@functools.lru_cache(maxsize=1)
def _read_showcase_template() -> str:
    """Reads and caches the showcase HTML template from disk."""
    if not _TEMPLATE_PATH.exists():
        raise FileNotFoundError(f"Showcase template not found at: {_TEMPLATE_PATH}")
    return _TEMPLATE_PATH.read_text(encoding="utf-8")


def get_showcase_html() -> str:
    """Returns the cached showcase HTML template, clearing cache on debug."""
    if os.environ.get("DEBUG") == "1":
        _read_showcase_template.cache_clear()
    return _read_showcase_template()


DISCOVERY_PAYLOAD: Dict[str, Any] = {
    "name": "Ana-Catalina Interactive Portfolio MCP",
    "status": "healthy",
    "version": "1.7.0",
    "mcp_endpoint": "/mcp",
    "health_endpoint": "/health",
    "web_showcase": "/demo",
    # demo_endpoint is kept as a backwards-compatible alias of web_showcase
    "demo_endpoint": "/demo",
}


# 4. Register Custom Routes (Web Showcase, Standalone REST APIs & Health Check)
@mcp.custom_route("/", methods=["GET"])
async def root_info(request: Request):
    """Root endpoint: serves interactive showcase HTML to browsers and JSON discovery to MCP clients/APIs."""
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


# Declarative static assets mapping: route -> (Path, media_type)
STATIC_ASSETS: Dict[str, Tuple[Path, str]] = {
    "/favicon.svg": (_BASE_DIR / "favicon.svg", "image/svg+xml"),
    "/logo-av.svg": (_BASE_DIR / "logo-av.svg", "image/svg+xml"),
    "/logo-av.png": (_BASE_DIR / "logo-av.png", "image/png"),
    "/favicon.ico": (_BASE_DIR / "favicon.ico", "image/x-icon"),
    "/favicon-32x32.png": (_BASE_DIR / "favicon-32x32.png", "image/png"),
    "/favicon-96x96.png": (_BASE_DIR / "favicon-96x96.png", "image/png"),
    "/apple-touch-icon.png": (_BASE_DIR / "apple-touch-icon.png", "image/png"),
    "/icon.png": (_BASE_DIR / "icon.png", "image/png"),
    "/poppy.svg": (_BASE_DIR / "templates" / "poppy.svg", "image/svg+xml"),
}


def _register_static_asset(route: str, file_path: Path, media_type: str) -> None:
    async def serve_asset(request: Request):
        if file_path.exists():
            return FileResponse(file_path, media_type=media_type)
        return Response(status_code=404)

    serve_asset.__name__ = f"serve_{route.strip('/').replace('.', '_').replace('-', '_')}"
    serve_asset.__doc__ = f"Serves static asset {route} ({media_type})"
    mcp.custom_route(route, methods=["GET"])(serve_asset)


for _route, (_file_path, _media_type) in STATIC_ASSETS.items():
    _register_static_asset(_route, _file_path, _media_type)


@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request):
    """Health check endpoint for Google Cloud Run container liveness."""
    return JSONResponse({
        "status": "healthy",
        "service": "anacatalina-mcp",
        "version": "1.7.0",
        "transports": ["Streamable HTTP (/mcp)"],
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
    return JSONResponse(res.model_dump(), status_code=200)


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


# 5. Generate ASGI Application — Streamable HTTP Transport (/mcp)
app = mcp.streamable_http_app()


if __name__ == "__main__":
    import uvicorn
    print(f"Starting MCP Server on http://{host}:{port}/mcp")
    uvicorn.run(app, host=host, port=port, log_level="info")
