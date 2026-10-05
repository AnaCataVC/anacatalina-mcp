"""
Unit tests for the MCP data synchronization script (scripts/sync_mcp_data.py).
"""
from pathlib import Path
import pytest
from models.cv import CVData
from scripts.sync_mcp_data import (
    clean_html,
    parse_i18n_js,
    parse_cv_ts,
    parse_project_markdown,
    normalize_skill,
    parse_skills_from_cv_astro,
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


def test_parse_project_markdown_ignores_nested_keys(tmp_path: Path):
    md_file = tmp_path / "nested.md"
    md_file.write_text(
        '---\n'
        'title: "Cute Agents Desk"\n'
        'highlights:\n'
        '  - icon: "shield"\n'
        '    title: "Pipeline Seguro de PRs"\n'
        '---\n',
        encoding="utf-8"
    )
    assert parse_project_markdown(md_file)["title"] == "Cute Agents Desk"


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
    assert len(cv_data_obj.projects) >= 2


def test_auditor_audit_reports_missing_translation_keys(tmp_path: Path):
    cv_dir = tmp_path / "anacatalina-cv"
    (cv_dir / "src").mkdir(parents=True)
    (cv_dir / "src" / "i18n.js").write_text(
        'export const translations = {\n'
        '  "hero.subtitle": {\n'
        '    es: "Data Scientist & Machine Learning Engineer",\n'
        '    en: "Data Scientist & Machine Learning Engineer"\n'
        '  }\n'
        '};\n',
        encoding="utf-8"
    )
    projects_dir = tmp_path / "projects-hub"
    projects_dir.mkdir()
    auditor = DataAuditor(
        base_dir=tmp_path,
        cv_dir=cv_dir,
        projects_dir=projects_dir,
        data_file=tmp_path / "cv_data.json"
    )

    report = auditor.audit()
    missing = [d["issue"] for d in report["discrepancies"] if d["component"] == "cv_translations"]
    assert any("'exp.simpliroute.b1'" in issue for issue in missing)
    assert not any("'hero.subtitle'" in issue for issue in missing)
    assert report["in_sync"] is False


def test_auditor_audit_executes_cleanly():
    root_dir = Path(__file__).resolve().parent.parent
    auditor = DataAuditor(base_dir=root_dir)

    report = auditor.audit()
    assert "sources" in report
    assert "stats" in report
    assert "discrepancies" in report
    assert isinstance(report["in_sync"], bool)


def test_normalize_skill():
    assert normalize_skill("Google Cloud (GCP)") == "google cloud platform (gcp)"
    assert normalize_skill("NodeJS") == "node.js"
    assert normalize_skill("Plotly/Dash") == "plotly / dash"
    assert normalize_skill("Python") == "python"


def test_parse_skills_from_cv_astro(tmp_path: Path):
    astro_file = tmp_path / "index.astro"
    astro_file.write_text(
        '<section id="skills">\n'
        '  <div class="skill-group reveal">\n'
        '    <h3>Category 1</h3>\n'
        '    <span class="rounded-lg">Skill Alpha</span>\n'
        '    <span class="rounded-lg"><span data-i18n="test">Skill Beta</span></span>\n'
        '  </div>\n'
        '  <div data-category="test" class="skill-group reveal">\n'
        '    <h3>Category 2</h3>\n'
        '    <span class="rounded-lg">Skill Gamma</span>\n'
        '  </div>\n'
        '</section>\n',
        encoding="utf-8"
    )
    parsed = parse_skills_from_cv_astro(astro_file)
    assert "Category 1" in parsed
    assert "Skill Alpha" in parsed["Category 1"]
    assert "Skill Beta" in parsed["Category 1"]
    assert "Category 2" in parsed
    assert "Skill Gamma" in parsed["Category 2"]


def test_parse_cv_ts(tmp_path: Path):
    ts_file = tmp_path / "cv.ts"
    ts_file.write_text(
        'export const cvData = {\n'
        '  basics: {\n'
        '    contact: {\n'
        '      title: { es: "Data Scientist", en: "Data Scientist" },\n'
        '      location: { es: "Chile", en: "Chile" }\n'
        '    }\n'
        '  },\n'
        '  experience: [\n'
        '    {\n'
        '      id: "simpliroute",\n'
        '      company: "SimpliRoute",\n'
        '      role: { es: "Learning Engineer", en: "Learning Engineer" },\n'
        '      date: { es: "Agosto 2025 - Presente", en: "August 2025 - Present" },\n'
        '      location: { es: "Santiago (Remoto)", en: "Santiago (Remote)" },\n'
        '      bullets: [\n'
        '        { es: "<strong>Arquitectura</strong> multi-proveedor.", en: "Multi-provider architecture." }\n'
        '      ],\n'
        '      pdfBullets: []\n'
        '    }\n'
        '  ]\n'
        '};\n',
        encoding="utf-8"
    )
    res = parse_cv_ts(ts_file)
    assert res["hero.subtitle"]["es"] == "Data Scientist"
    assert res["exp.simpliroute.title"]["es"] == "Learning Engineer"
    assert res["exp.simpliroute.date"]["es"] == "Agosto 2025 - Presente"
    assert "Arquitectura multi-proveedor." in res["exp.simpliroute.b1"]["es"]
    assert "<strong>" not in res["exp.simpliroute.b1"]["es"]


def test_auditor_audit_detects_project_drift(tmp_path: Path):
    import json
    cv_dir = tmp_path / "anacatalina-cv"
    (cv_dir / "src").mkdir(parents=True)
    projects_dir = tmp_path / "projects-hub"
    es_dir = projects_dir / "src" / "content" / "projects" / "es"
    es_dir.mkdir(parents=True)

    (es_dir / "active-app.md").write_text(
        '---\n'
        'title: "Active App"\n'
        'description: "Updated description"\n'
        'technologies: ["Rust", "Tauri v2"]\n'
        'githubUrl: "https://github.com/AnaCataVC/active-app"\n'
        'websiteUrl: "https://active-app.ana-catalina.com"\n'
        'status: "Activo"\n'
        '---\n',
        encoding="utf-8"
    )
    (es_dir / "archived-app.md").write_text(
        '---\n'
        'title: "Archived App"\n'
        'description: "Old app"\n'
        'technologies: ["C#"]\n'
        'githubUrl: "https://github.com/AnaCataVC/archived-app"\n'
        'status: "Archivado"\n'
        '---\n',
        encoding="utf-8"
    )

    data_file = tmp_path / "cv_data.json"
    data_file.write_text(
        json.dumps({
            "projects": [
                {
                    "name": "Archived App",
                    "type": "personal",
                    "description": "Old app",
                    "technologies": ["C#"],
                    "repo_url": "https://github.com/AnaCataVC/archived-app",
                    "demo_url": None
                }
            ]
        }),
        encoding="utf-8"
    )

    auditor = DataAuditor(
        base_dir=tmp_path,
        cv_dir=cv_dir,
        projects_dir=projects_dir,
        data_file=data_file
    )
    report = auditor.audit()
    components = {d["component"] for d in report["discrepancies"]}
    assert "projects.active-app" in components
    assert "projects.archived-app" in components
    assert report["in_sync"] is False



