"""
Unit and integration tests for Ana-Catalina MCP Server.
"""
import pytest
from starlette.testclient import TestClient

from services.cv_service import CVService, get_cv_service
from server import (
    app,
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
    """Tests buscar_en_curriculum tool."""
    search_res = await buscar_en_curriculum(consulta="Docker")
    assert search_res["matched_skills"] or search_res["projects"] or search_res["experiences"]


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
    """Tests evaluar_fit_puesto with negative benchmark scenario."""
    result = await evaluar_fit_puesto(descripcion_vacante="pop-singer")
    assert result.technologies_matched == []
    assert "10%" in result.estimated_fit_score
    assert "no requiere" in result.added_value_summary


@pytest.mark.asyncio
async def test_tool_evaluar_fit_puesto_logistics():
    """Tests evaluar_fit_puesto with logistics benchmark scenario."""
    result = await evaluar_fit_puesto(descripcion_vacante="logistics")
    assert "Optimización Logística" in result.technologies_matched
    assert any("SimpliRoute" in s for s in result.matching_strengths)


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


def test_root_browser_content_negotiation_html():
    """Tests that browser requests with text/html in Accept header receive the showcase HTML."""
    client = TestClient(app)
    response = client.get("/", headers={"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"})
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "<!DOCTYPE html>" in response.text
    assert "Ana-Catalina" in response.text
    assert "Pastel-Tech" in response.text


def test_demo_endpoint():
    """Tests direct /demo route returns the HTML showcase."""
    client = TestClient(app)
    res = client.get("/demo")
    assert res.status_code == 200
    assert "text/html" in res.headers["content-type"]
    assert "Alineación" in res.text or "Interactive" in res.text


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
    """Tests POST /api/evaluate-fit with negative benchmark scenario."""
    client = TestClient(app)
    response = client.post("/api/evaluate-fit", json={"scenario": "pop-singer"})
    assert response.status_code == 200
    data = response.json()
    assert data["technologies_matched"] == []
    assert "10%" in data["estimated_fit_score"]
    assert "no requiere" in data["added_value_summary"]



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
