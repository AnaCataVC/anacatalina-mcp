"""
Unit and integration tests for Ana-Catalina MCP Server.
"""
import pytest
from starlette.testclient import TestClient

from services.cv_service import CVService, get_cv_service
from models.cv import SearchResult
from server import (
    app,
    APP_VERSION,
    STATIC_ASSETS,
    reset_rate_limiter,
    obtener_experiencia,
    obtener_stack_tecnologico,
    obtener_proyectos_destacados,
    evaluar_fit_puesto,
    buscar_en_curriculum,
    obtener_educacion,
    obtener_contacto,
    obtener_perfil,
    obtener_resumen_ejecutivo,
)


@pytest.fixture
def service():
    """Returns CVService instance."""
    return get_cv_service()


def test_cv_data_loaded(service):
    """Verifies that CV data is properly loaded and validated."""
    assert service.cv.personal_info.name == "Ana-Catalina Villalobos Contardo"
    assert service.cv.personal_info.first_name == "Ana-Catalina"
    assert service.cv.personal_info.middle_name == "Alejandra"
    assert service.cv.personal_info.last_name == "Villalobos Contardo"
    assert service.cv.personal_info.full_name == "Ana-Catalina Alejandra Villalobos Contardo"
    assert "SimpliRoute" in [exp.company for exp in service.cv.experience]
    assert "Fracttal" in [exp.company for exp in service.cv.experience]


@pytest.mark.asyncio
async def test_tool_obtener_experiencia():
    """Tests obtener_experiencia tool."""
    all_exp = await obtener_experiencia()
    assert len(all_exp) >= 2

    simpliroute_exp = await obtener_experiencia(empresa="SimpliRoute")
    assert len(simpliroute_exp) == 1
    assert simpliroute_exp[0].company == "SimpliRoute"
    assert "Python" in simpliroute_exp[0].technologies


@pytest.mark.asyncio
async def test_tool_obtener_stack_tecnologico():
    """Tests obtener_stack_tecnologico tool."""
    all_skills = await obtener_stack_tecnologico()
    assert len(all_skills) > 0

    gcp_skills = await obtener_stack_tecnologico(categoria="Cloud")
    assert len(gcp_skills) >= 1
    skill_names = [s.name for s in gcp_skills[0].skills]
    assert "BigQuery" in skill_names or "Docker" in skill_names


@pytest.mark.asyncio
async def test_tool_obtener_proyectos_destacados():
    """Tests obtener_proyectos_destacados tool."""
    personal_projects = await obtener_proyectos_destacados(tipo="personal")
    assert len(personal_projects) >= 1
    assert personal_projects[0].type == "personal"


@pytest.mark.asyncio
async def test_tool_evaluar_fit_puesto():
    """Tests evaluar_fit_puesto tool with benchmark scenario."""
    result = await evaluar_fit_puesto(descripcion_vacante="data-science")
    assert "Python" in result.technologies_matched
    assert "Vertex AI" in result.technologies_matched
    assert "Excepcional" in result.estimated_fit_score


@pytest.mark.asyncio
async def test_tool_buscar_en_curriculum():
    """Tests buscar_en_curriculum tool and validates SearchResult contract."""
    search_res = await buscar_en_curriculum(consulta="Docker")
    assert isinstance(search_res, SearchResult)
    assert search_res.query == "Docker"
    assert search_res.matched_skills or search_res.projects or search_res.experiences
    # Backwards-compatible dict indexing
    assert search_res["matched_skills"] or search_res["projects"] or search_res["experiences"]
    dumped = search_res.model_dump()
    assert "matched_experiences_count" in dumped
    assert "matched_projects_count" in dumped


@pytest.mark.asyncio
async def test_tool_obtener_contacto():
    """Tests obtener_contacto tool."""
    contact = await obtener_contacto()
    assert "@" in contact.email
    assert "linkedin.com" in contact.linkedin


@pytest.mark.asyncio
async def test_tool_obtener_resumen_ejecutivo():
    """Tests obtener_resumen_ejecutivo in es and en."""
    resumen_es = await obtener_resumen_ejecutivo(idioma="es")
    assert "SimpliRoute" in resumen_es or "Data Scientist" in resumen_es

    resumen_en = await obtener_resumen_ejecutivo(idioma="en")
    assert "Data Scientist" in resumen_en


@pytest.mark.asyncio
async def test_tool_obtener_educacion():
    """Tests obtener_educacion tool."""
    education = await obtener_educacion()
    assert len(education) >= 1
    assert any("Chile" in e.institution for e in education)


@pytest.mark.asyncio
async def test_tool_obtener_perfil():
    """Tests obtener_perfil tool."""
    perfil = await obtener_perfil()
    assert perfil.name == "Ana-Catalina Villalobos Contardo"
    assert perfil.first_name == "Ana-Catalina"
    assert perfil.middle_name == "Alejandra"
    assert perfil.last_name == "Villalobos Contardo"
    assert perfil.full_name == "Ana-Catalina Alejandra Villalobos Contardo"
    assert "github.com" in perfil.portfolio_links.github


@pytest.mark.asyncio
async def test_tool_evaluar_fit_puesto_sin_coincidencias():
    """Tests evaluar_fit_puesto with non-matching / unrelated job description."""
    result = await evaluar_fit_puesto(descripcion_vacante="Buscamos cantante lírico para recitales y conciertos musicales.")
    assert result.technologies_matched == []
    assert "0%" in result.estimated_fit_score
    assert "No se detectó afinidad técnica" in result.added_value_summary


@pytest.mark.asyncio
async def test_tool_evaluar_fit_puesto_logistics():
    """Tests evaluar_fit_puesto with logistics benchmark scenario."""
    result = await evaluar_fit_puesto(descripcion_vacante="logistics")
    assert "Optimización Logística" in result.technologies_matched
    assert any("SimpliRoute" in s for s in result.matching_strengths)


@pytest.mark.asyncio
async def test_tool_evaluar_fit_puesto_freeform_text():
    """Tests evaluar_fit_puesto with arbitrary freeform job description."""
    jd = "Requerimos profesional para desarrollo de agentes autónomos con MCP, FastAPI y Docker sobre Google Cloud."
    result = await evaluar_fit_puesto(descripcion_vacante=jd)
    assert "Model Context Protocol (MCP)" in result.technologies_matched
    assert "FastAPI" in result.technologies_matched
    assert "Docker" in result.technologies_matched
    assert "Google Cloud Platform (GCP)" in result.technologies_matched
    assert ("Alta" in result.estimated_fit_score or "Excepcional" in result.estimated_fit_score)


def test_cv_service_missing_file(tmp_path):
    """Tests that a missing CV data file raises FileNotFoundError."""
    missing_path = tmp_path / "missing.json"
    with pytest.raises(FileNotFoundError):
        CVService(data_path=str(missing_path))


def test_root_endpoint():
    """Tests the root discovery route with default client (preserves JSON compatibility)."""
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert response.json()["name"] == "Ana-Catalina Interactive Portfolio MCP"


def test_root_browser_returns_showcase_html():
    """Tests that browser requests with text/html in Accept header return the showcase HTML directly."""
    client = TestClient(app)
    response = client.get(
        "/",
        headers={"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"},
        follow_redirects=False,
    )
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "location" not in response.headers


def test_demo_endpoint():
    """Tests direct /demo route returns the HTML showcase with the robot mascot avatar."""
    client = TestClient(app)
    res = client.get("/demo")
    assert res.status_code == 200
    assert "text/html" in res.headers["content-type"]
    assert "Alineación" in res.text or "Interactive" in res.text
    assert "/icon.png" in res.text
    assert "hero-avatar" in res.text


def test_icon_png_endpoint():
    """Tests that /icon.png returns the robot mascot avatar with image/png content type."""
    client = TestClient(app)
    res = client.get("/icon.png")
    assert res.status_code == 200
    assert "image/png" in res.headers["content-type"]
    assert len(res.content) > 1000


def test_logo_av_svg_endpoint():
    """Tests that /logo-av.svg returns the geometric AV emblem SVG with image/svg+xml content type."""
    client = TestClient(app)
    res = client.get("/logo-av.svg")
    assert res.status_code == 200
    assert "image/svg+xml" in res.headers["content-type"]
    assert len(res.content) > 500


def test_logo_av_png_endpoint():
    """Tests that /logo-av.png returns the geometric AV emblem PNG with image/png content type."""
    client = TestClient(app)
    res = client.get("/logo-av.png")
    assert res.status_code == 200
    assert "image/png" in res.headers["content-type"]
    assert len(res.content) > 1000


def test_favicon_svg_endpoint():
    """Tests that /favicon.svg returns the AV emblem SVG with image/svg+xml content type."""
    client = TestClient(app)
    res = client.get("/favicon.svg")
    assert res.status_code == 200
    assert "image/svg+xml" in res.headers["content-type"]
    assert len(res.content) > 500


def test_favicon_ico_endpoint():
    """Tests that /favicon.ico returns the favicon with image/x-icon content type."""
    client = TestClient(app)
    res = client.get("/favicon.ico")
    assert res.status_code == 200
    assert "image/x-icon" in res.headers["content-type"]
    assert len(res.content) > 1000


def test_poppy_svg_endpoint():
    """Tests that /poppy.svg returns the botanical poppy SVG with image/svg+xml content type."""
    client = TestClient(app)
    res = client.get("/poppy.svg")
    assert res.status_code == 200
    assert "image/svg+xml" in res.headers["content-type"]
    assert len(res.content) > 1000


def test_api_evaluate_fit_success():
    """Tests POST /api/evaluate-fit with valid tech vacancy."""
    client = TestClient(app)
    jd = "Buscamos Data Scientist con experiencia en Python, GCP, BigQuery y Vertex AI."
    response = client.post("/api/evaluate-fit", json={"job_description": jd})
    assert response.status_code == 200
    data = response.json()
    assert "technologies_matched" in data
    assert "Python" in data["technologies_matched"]
    assert "BigQuery" in data["technologies_matched"]
    assert "estimated_fit_score" in data


def test_api_evaluate_fit_invalid_input():
    """Tests POST /api/evaluate-fit validation errors."""
    client = TestClient(app)
    # Empty string
    res_empty = client.post("/api/evaluate-fit", json={"job_description": "   "})
    assert res_empty.status_code == 400
    assert "error" in res_empty.json()

    # Missing field
    res_missing = client.post("/api/evaluate-fit", json={})
    assert res_missing.status_code == 400

    # Non-dict body
    res_non_dict = client.post("/api/evaluate-fit", content="not json", headers={"Content-Type": "application/json"})
    assert res_non_dict.status_code == 400


def test_api_evaluate_fit_negative_test():
    """Tests POST /api/evaluate-fit with non-matching / unrelated job description."""
    client = TestClient(app)
    response = client.post("/api/evaluate-fit", json={"job_description": "Chef de cocina internacional y repostería artesanal"})
    assert response.status_code == 200
    data = response.json()
    assert data["technologies_matched"] == []
    assert "0%" in data["estimated_fit_score"]
    assert "No se detectó afinidad técnica" in data["added_value_summary"]



def test_api_search_endpoint():
    """Tests GET /api/search."""
    client = TestClient(app)
    res = client.get("/api/search?q=BigQuery")
    assert res.status_code == 200
    data = res.json()
    assert data["query"] == "BigQuery"
    assert data["matched_experiences_count"] > 0 or len(data["matched_skills"]) > 0


def test_api_skills_endpoint():
    """Tests GET /api/skills."""
    client = TestClient(app)
    res = client.get("/api/skills?category=Cloud")
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 1
    assert any("Cloud" in cat["category"] for cat in data)


def test_api_projects_endpoint():
    """Tests GET /api/projects."""
    client = TestClient(app)
    res = client.get("/api/projects?type=personal")
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 1
    assert all(p["type"] == "personal" for p in data)


def test_health_endpoint():
    """Tests the health check route and verifies Streamable HTTP is the active transport."""
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "anacatalina-mcp"
    transports = data.get("transports", [])
    assert any("Streamable HTTP" in t for t in transports), "Streamable HTTP transport must be listed"


def test_mcp_streamable_http_endpoint_accepts_post():
    """Tests that POST /mcp with proper Accept headers returns 200 (Streamable HTTP transport)."""
    with TestClient(app) as client:
        response = client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "pytest", "version": "1"},
                },
            },
            headers={"Accept": "application/json, text/event-stream"},
        )
        assert response.status_code == 200
        assert "mcp-session-id" in response.headers
        assert "protocolVersion" in response.text
        assert "serverInfo" in response.text


def test_mcp_endpoint_route_registered():
    """Verifies /mcp route is registered in the Streamable HTTP app."""
    from starlette.routing import Route
    mcp_routes = [
        r for r in app.routes
        if isinstance(r, Route) and getattr(r, "path", "") == "/mcp"
    ]
    assert len(mcp_routes) == 1, "/mcp route must be registered"


def test_discovery_json_exposes_mcp_endpoint():
    """Tests that the JSON discovery payload exposes the mcp_endpoint field."""
    client = TestClient(app)
    response = client.get("/", headers={"Accept": "application/json"})
    assert response.status_code == 200
    data = response.json()
    assert "mcp_endpoint" in data
    assert data["mcp_endpoint"] == "/mcp"


def test_benchmark_presets_semantic_coherence(service):
    """Verifies that all 4 preset benchmarks in index.html match backend evaluate_job_fit output."""
    # 1. Data Science preset
    ds_res = service.evaluate_job_fit("data-science")
    assert "Excepcional" in ds_res.estimated_fit_score
    assert "Python" in ds_res.technologies_matched
    assert "Vertex AI" in ds_res.technologies_matched

    # 2. Logistics preset
    log_res = service.evaluate_job_fit("logistics")
    assert "Excepcional" in log_res.estimated_fit_score
    assert "Optimización Logística" in log_res.technologies_matched

    # 3. Agents preset
    agent_res = service.evaluate_job_fit("agents")
    assert "Excepcional" in agent_res.estimated_fit_score
    assert "Model Context Protocol (MCP)" in agent_res.technologies_matched

    # 4. Pop-singer negative test preset
    pop_res = service.evaluate_job_fit("pop-singer")
    assert "0%" in pop_res.estimated_fit_score
    assert pop_res.technologies_matched == []


def test_static_assets_dispatcher_coverage():
    """Verifies that all routes registered in STATIC_ASSETS return 200 with matching Content-Type."""
    client = TestClient(app)
    for route, (file_path, expected_media_type) in STATIC_ASSETS.items():
        res = client.get(route)
        assert res.status_code == 200, f"Expected 200 for {route}"
        assert expected_media_type in res.headers["content-type"], f"Expected {expected_media_type} for {route}"


def test_app_version_centralized_across_endpoints():
    """Verifies that APP_VERSION is consistently exposed in both / and /health."""
    client = TestClient(app)
    root_res = client.get("/", headers={"Accept": "application/json"})
    health_res = client.get("/health")
    assert root_res.json()["version"] == APP_VERSION
    assert health_res.json()["version"] == APP_VERSION


def test_security_headers_injected_on_responses():
    """Verifies that standard HTTP security headers are injected on responses."""
    client = TestClient(app)
    res = client.get("/health")
    assert res.status_code == 200
    assert res.headers.get("x-content-type-options") == "nosniff"
    assert res.headers.get("x-frame-options") == "DENY"
    assert res.headers.get("referrer-policy") == "strict-origin-when-cross-origin"


def test_rate_limiter_enforces_429_per_ip():
    """Verifies that the sliding-window rate limiter blocks excessive API calls from a single IP."""
    reset_rate_limiter()
    client = TestClient(app)
    test_ip = "203.0.113.99"

    try:
        # Exhaust the bucket for test_ip using RATE_LIMIT_MAX_REQUESTS (default 120)
        for _ in range(120):
            res = client.get("/api/skills", headers={"X-Forwarded-For": test_ip})
            assert res.status_code == 200

        # 121st request from same IP must return 429 Too Many Requests with security headers
        blocked = client.get("/api/skills", headers={"X-Forwarded-For": test_ip})
        assert blocked.status_code == 429
        assert "Rate limit exceeded" in blocked.json()["error"]
        assert "retry-after" in blocked.headers
        assert blocked.headers.get("x-content-type-options") == "nosniff"
        assert blocked.headers.get("x-frame-options") == "DENY"

        # Another IP remains unaffected
        other_ip_res = client.get("/api/skills", headers={"X-Forwarded-For": "203.0.113.100"})
        assert other_ip_res.status_code == 200
    finally:
        reset_rate_limiter()


