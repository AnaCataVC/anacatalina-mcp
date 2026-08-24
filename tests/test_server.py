"""
Unit and integration tests for Ana Catalina MCP Server.
"""
import pytest
from services.cv_service import get_cv_service
from server import (
    obtener_experiencia,
    obtener_stack_tecnologico,
    obtener_proyectos_destacados,
    evaluar_fit_puesto,
    buscar_en_curriculum,
    obtener_educacion,
    obtener_contacto,
    obtener_resumen_ejecutivo,
)


@pytest.fixture
def service():
    """Returns CVService instance."""
    return get_cv_service()


def test_cv_data_loaded(service):
    """Verifies that CV data is properly loaded and validated."""
    assert service.cv.personal_info.name == "Ana Catalina"
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
    """Tests evaluar_fit_puesto tool."""
    sample_jd = (
        "Buscamos un Senior Data Scientist con experiencia en Python, GCP, BigQuery, "
        "Vertex AI y Docker para liderar proyectos de Machine Learning."
    )
    result = await evaluar_fit_puesto(descripcion_vacante=sample_jd)
    assert "Python" in result.technologies_matched
    assert "Vertex AI" in result.technologies_matched
    assert "Alto" in result.estimated_fit_score or "Excepcional" in result.estimated_fit_score


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
