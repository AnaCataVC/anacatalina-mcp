"""
Unit tests for the MCP data synchronization script (scripts/sync_mcp_data.py).
"""
from pathlib import Path
import pytest
from models.cv import CVData
from scripts.sync_mcp_data import (
    clean_html,
    parse_i18n_js,
    parse_project_markdown,
    DataAuditor
)


def test_clean_html():
    raw = 'Diseño e implementación de <strong class="text-slate-800">soluciones</strong>.<br />Con foco en <a href="#test">ML</a>.'
    cleaned = clean_html(raw)
    assert cleaned == "Diseño e implementación de soluciones. Con foco en ML."
    assert "<" not in cleaned
    assert ">" not in cleaned


def test_parse_project_markdown_valid(tmp_path: Path):
    md_file = tmp_path / "test-project.md"
    md_file.write_text(
        '---\n'
        'title: "Test Project"\n'
        'description: "A cool test project"\n'
        'technologies: ["Python", "Docker"]\n'
        'githubUrl: "https://github.com/AnaCataVC/test"\n'
        'websiteUrl: "https://test.ana-catalina.com"\n'
        'type: "personal"\n'
        'status: "Activo"\n'
        '---\n\n'
        '# Detailed markdown content\n',
        encoding="utf-8"
    )

    parsed = parse_project_markdown(md_file)
    assert parsed is not None
    assert parsed["title"] == "Test Project"
    assert parsed["description"] == "A cool test project"
    assert parsed["technologies"] == ["Python", "Docker"]
    assert parsed["githubUrl"] == "https://github.com/AnaCataVC/test"
    assert parsed["websiteUrl"] == "https://test.ana-catalina.com"


def test_parse_project_markdown_invalid(tmp_path: Path):
    md_file = tmp_path / "invalid.md"
    md_file.write_text("No frontmatter here", encoding="utf-8")
    assert parse_project_markdown(md_file) is None


def test_parse_i18n_js(tmp_path: Path):
    js_file = tmp_path / "i18n.js"
    js_file.write_text(
        'export const translations = {\n'
        '  "hero.subtitle": {\n'
        '    es: "Data Scientist & Machine Learning Engineer",\n'
        '    en: "Data Scientist & Machine Learning Engineer"\n'
        '  },\n'
        '  "exp.simpliroute.date": {\n'
        '    es: "Agosto 2025 - Presente",\n'
        '    en: "August 2025 - Present"\n'
        '  }\n'
        '};\n',
        encoding="utf-8"
    )

    translations = parse_i18n_js(js_file)
    assert "hero.subtitle" in translations
    assert translations["hero.subtitle"]["es"] == "Data Scientist & Machine Learning Engineer"
    assert translations["exp.simpliroute.date"]["es"] == "Agosto 2025 - Presente"


def test_auditor_generate_synchronized_dataset_validates_pydantic():
    root_dir = Path(__file__).resolve().parent.parent
    auditor = DataAuditor(base_dir=root_dir)

    dataset = auditor.generate_synchronized_dataset()
    assert isinstance(dataset, dict)
    
    # Must pass strict Pydantic validation
    cv_data_obj = CVData(**dataset)
    assert cv_data_obj.personal_info.first_name == "Ana-Catalina"
    assert cv_data_obj.personal_info.name == "Ana-Catalina Villalobos Contardo"
    assert len(cv_data_obj.experience) >= 4
    assert len(cv_data_obj.projects) >= 3


def test_auditor_audit_executes_cleanly():
    root_dir = Path(__file__).resolve().parent.parent
    auditor = DataAuditor(base_dir=root_dir)

    report = auditor.audit()
    assert "sources" in report
    assert "stats" in report
    assert "discrepancies" in report
    assert isinstance(report["in_sync"], bool)
