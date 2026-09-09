# AGENTS.md — AI Agent Guidelines & Architecture Manual

> This file provides architecture context, technical constraints, identity invariants, and operational guidelines for AI coding assistants (Gemini, Claude, Antigravity, etc.) working on this repository.

---

## Project Description

Official **Model Context Protocol (MCP)** server and interactive showcase for **Ana-Catalina Alejandra Villalobos Contardo**, Civil Engineer and Data Scientist & Machine Learning Engineer (Learning Engineer at SimpliRoute, ex-Fracttal).

The repository serves a dual-purpose architecture:
1. **Programmatic / Agent Interface:** Official FastMCP server operating over modern **Streamable HTTP** at `/mcp`, with JSON discovery at `/`. Enables AI agents (Claude.ai Custom Connectors, Cursor, Windsurf) to query Ana-Catalina's professional background, skills, and projects with structured JSON responses.
2. **Human / Evaluator Interface:** A single-page web showcase served at `/` and `/demo` via transparent HTTP content negotiation (`Accept: text/html`). Allows technical recruiters and engineering managers to see what the mcp offers.

**Live Production URLs:**
- Primary Custom Domain: [https://mcp.ana-catalina.com/](https://mcp.ana-catalina.com/)
- Google Cloud Run Mirror: `https://anacatalina-mcp-165536131179.us-central1.run.app/`
- MCP Streamable HTTP Endpoint: `https://mcp.ana-catalina.com/mcp`

---

## Tech Stack

| Category | Technology | Description |
| :--- | :--- | :--- |
| **Language** | Python 3.12+ | Core runtime environment |
| **MCP SDK** | `mcp>=1.3.0,<2` | Official Anthropic Model Context Protocol SDK (FastMCP) |
| **Web / ASGI Framework** | Starlette + FastAPI | High-performance async server handling SSE and HTTP negotiation |
| **Data Validation** | Pydantic v2 | Strict schema validation, typed models, and JSON serialization |
| **Templating / UI** | Vanilla HTML5 + CSS + Modern ES6 | Self-contained single-page showcase (zero Node/npm build dependencies) |
| **Containerization** | Docker | Multi-stage Debian slim container optimized for Cloud Run |
| **Deployment** | Google Cloud Run | Serverless container host with automatic scale-to-zero |
| **Test Suite** | pytest + pytest-asyncio | 100% passing automated test coverage with Starlette `TestClient` |

---

## Candidate Identity & Data Invariants (Strict Anti-Hallucination)

When generating, modifying, or querying data concerning the candidate, coding agents **MUST ALWAYS** strictly adhere to the following naming and profile invariants:

| Field | Exact Invariant Value | Rules / Constraints |
| :--- | :--- | :--- |
| **Full Legal Name** | `Ana-Catalina Alejandra Villalobos Contardo` | Official legal identity. |
| **CV / Display Name** | `Ana-Catalina Villalobos Contardo` | Standard professional heading on CVs and web apps. |
| **First Name** | `Ana-Catalina` | **CRITICAL:** Always hyphenated. NEVER use unhyphenated "Ana Catalina". |
| **Middle Name** | `Alejandra` | Second given name. |
| **Last Names** | `Villalobos Contardo` | Paternal + maternal Chilean surnames. |
| **GitHub Handle** | `AnaCataVC` | Official GitHub username. |
| **Current Headline** | `Data Scientist & Machine Learning Engineer` | Public professional headline (current SimpliRoute role title: `Learning Engineer`, since Aug 2025). |
| **Location** | `Santiago, Chile` | Base location. |
| **Contact Email** | `anacatalina@outlook.cl` | Primary contact channel. |
| **LinkedIn** | `https://linkedin.com/in/ana-catalina/` | Official LinkedIn profile. |

### Portfolio Ecosystem Links:
- **Homepage:** `https://ana-catalina.com/`
- **Interactive CV:** `https://cv.ana-catalina.com/`
- **Projects Hub:** `https://projects.ana-catalina.com/`
- **MCP Server:** `https://mcp.ana-catalina.com/`

---

## Repository Structure

```
anacatalina-mcp/
├── data/
│   └── cv_data.json            # In-memory single source of truth for the CV dataset
├── models/
│   ├── __init__.py
│   └── cv.py                   # Pydantic v2 models (PersonalInfo, ExperienceItem, Skills, etc.)
├── services/
│   ├── __init__.py
│   └── cv_service.py           # In-memory CVService singleton, search, and benchmark engine
├── templates/
│   ├── index.html              # Single-page Pastel-Tech showcase & deterministic playground
│   └── poppy.svg               # Botanical poppy SVG watermark for UI background
├── tests/
│   └── test_server.py          # 26 automated tests (Streamable HTTP, MCP tools, REST APIs)
├── Dockerfile                  # Container definition for Google Cloud Run
├── pytest.ini                  # Pytest configuration (asyncio mode)
├── requirements.txt            # Production runtime dependencies (pinned mcp<2)
├── requirements-dev.txt        # Development dependencies (pytest, pytest-asyncio, httpx)
├── server.py                   # Main entrypoint: FastMCP server, route handlers, Streamable HTTP
├── favicon.svg                 # Official ACVC geometric monogram SVG
├── favicon.ico                 # Fallback favicon
├── icon.png                    # Repository and client avatar
├── AGENTS.md                   # This file
└── README.md                   # Bilingual portfolio README
```

---

## Deterministic Benchmark Engine ("Forma 1" Architecture)

The showcase playground and job fit evaluator run on **Forma 1** architecture:
- **Zero External LLM Calls at Runtime:** 100% deterministic, eliminating third-party API dependencies, token fees ($0.00 cost), rate limits, and risk of hallucinations.
- **Sub-5ms Latency:** Instant evaluation executed entirely in memory using pre-compiled benchmark models.
- **Curated Benchmark Scenarios (`FIXED_BENCHMARK_SCENARIOS` in `services/cv_service.py`):**
  1. `data-science`: *Senior Data Scientist / Machine Learning Engineer* &rarr; **95% (Alineación Excepcional)**. Highlights GCP, BigQuery, Vertex AI, and predictive modeling.
  2. `logistics`: *Data Scientist Especialista en Ruteo & Logística* &rarr; **90% (Alta Compatibilidad)**. Highlights last-mile telemetry, routing algorithms, and dispatch optimization at SimpliRoute.
  3. `agents`: *Ingeniera en IA & Agentes Autónomos (MCP)* &rarr; **90% (Alta Compatibilidad)**. Highlights production MCP servers, Streamable HTTP transport, and LLM tool engineering.
  4. `pop-singer`: *Cantante Pop (Test Negativo)* &rarr; **10% (Sin Alineación / Fuera de Especialidad)**. Serves as a transparent control scenario proving zero false positives.
- **Invariant:** Open-ended, fuzzy free-text parsing heuristics were intentionally removed to keep the server reliable and predictable. Any incoming request either directly selects a benchmark or cleanly falls back to the primary Data Science archetype.

---

## Official MCP Tools Catalog

The FastMCP server exposes **9 official tools** via the standard MCP protocol:

| Tool Name | Parameters | Return Type | Purpose |
| :--- | :--- | :--- | :--- |
| `obtener_experiencia` | `empresa` *(str, optional)* | `List[ExperienceItem]` | Work history at SimpliRoute, Fracttal, etc., with roles, achievements, and tech stack. |
| `obtener_stack_tecnologico` | `categoria` *(str, optional)*<br/>`nivel` *(str, optional)* | `List[SkillCategory]` | Technical skill matrix (Python, SQL, BigQuery, Vertex AI, Docker) with proficiency levels. |
| `obtener_proyectos_destacados` | `tipo` *(str, optional)*<br/>`tecnologia` *(str, optional)* | `List[ProjectItem]` | Flagship personal and professional projects with architectures and demo links. |
| `evaluar_fit_puesto` | `descripcion_vacante` *(str, required)* | `FitEvaluationResult` | Deterministic benchmark fit analysis returning score, matching technologies, and value proposition. |
| `buscar_en_curriculum` | `consulta` *(str, required)* | `Dict[str, Any]` | Cross-cutting keyword search across experience, skills, and projects in memory. |
| `obtener_educacion` | *None* | `List[EducationItem]` | Formal degree and academic background from Universidad de Chile. |
| `obtener_contacto` | *None* | `ContactDetails` | Direct professional contact email and LinkedIn URL. |
| `obtener_perfil` | *None* | `PersonalInfo` | General profile: display name, first/middle/last names, full name, headline, location, and GitHub. |
| `obtener_resumen_ejecutivo` | `idioma` *(str, default="es")* | `str` | Executive summary focused on Data Science, ML, and MCP in Spanish (`es`) or English (`en`). |

---

## HTTP Endpoints & Content Negotiation

In `server.py`, the Starlette application routes requests as follows:

| Route | Method | Content-Type | Behavior |
| :--- | :--- | :--- | :--- |
| `/` | `GET` | `text/html` or `application/json` | **Transparent Content Negotiation:** If `Accept: text/html` is present (browsers), serves the web showcase. Otherwise serves JSON discovery metadata. |
| `/demo` | `GET` | `text/html` | Direct access to the web showcase and interactive playground. |
| `/mcp` | `POST` | `application/json` or `text/event-stream` | **Streamable HTTP MCP Endpoint:** Unified MCP transport for Claude.ai, Cursor, and modern AI clients. |
| `/health` | `GET` | `application/json` | Cloud Run container liveness probe. |
| `/api/evaluate-fit` | `POST` | `application/json` | Standalone REST endpoint for benchmark role fit evaluation via direct HTTP. |
| `/api/search` | `GET` | `application/json` | Standalone REST endpoint for cross-curriculum keyword search (`?q=...`) via direct HTTP. |
| `/api/skills` | `GET` | `application/json` | Standalone REST endpoint returning technical skill taxonomy with category and level filters. |
| `/api/projects` | `GET` | `application/json` | Standalone REST endpoint returning featured projects filtered by type or tech. |

---

## UI & Design System Guidelines (Pastel-Tech)

When modifying `templates/index.html`:

1. **Card Hierarchy:**
   - **Card 1 (Top Priority):** Conectar con Asistentes de IA (MCP) &mdash; tabs for Cursor (`mcp.json`), Claude Desktop (`conecta_cata.py`), and cURL.
   - **Card 2:** Catálogo Oficial de 9 Herramientas MCP.
   - **Card 3:** Escenarios de Alineación Técnica (Ejemplos Fijos: Data Science, Ruteo/Logística, Agentes MCP, Test Negativo).
2. **Zero Flags Rule (STRICT INVARIANT):**
   - **NEVER** use country flag emojis (`🇺🇸`, `🇬🇧`, `🇪🇸`, `🇲🇽`, etc.) or flag graphics anywhere in the UI or documentation.
   - Flags represent sovereign states, not languages or technologies. Terminal emulators, Windows consoles, and various web browsers render them as broken letter pairs (`[U][S]`) or monochrome squares (`□□`).
   - Use clean text (`ES`, `EN`, `Español`, `English`) or neutral icons.
3. **Zero Broken Mockups:**
   - Every single button, chip, tab switcher, and copy block must be 100% operational in live production.
   - Do not leave decorative placeholders, non-functional inputs, or broken links.
4. **Color Tokens (Pastel Palette):**
   - `--color-pastel-lilac`: `#C7B8EA`
   - `--color-pastel-accent`: `#8F6FFF`
   - `--color-pastel-mint`: `#C8F3E0`
   - `--color-pastel-pink`: `#F7C6D9`
   - `--color-pastel-blue`: `#BCDFFB`
   - Base canvas uses Dark Theme (`#1E1A2B`) by default with clean Slate grays.
5. **Mobile Responsiveness:**
   - Use elastic `1fr` grid columns on mobile screens (`@media (max-width: 768px)`).
   - Stack header actions vertically with centered brand icon.
   - Ensure the code container has `padding-top: 44px` on mobile so the absolute copy button never obscures configuration text.

---

## Development & Testing Commands

All commands assume a local Python 3.12 virtual environment (`.venv`):

```powershell
# Activate virtual environment
.venv\Scripts\Activate.ps1

# Run full test suite (26 tests)
.venv\Scripts\python.exe -m pytest tests/ -v

# Run local development server (with hot reload)
.venv\Scripts\uvicorn.exe server:app --reload --port 8080
```

---

## Agent Operational Invariants & Knowledge Synchronization

1. **Mandatory Documentation Auto-Update (Self-Maintaining `AGENTS.md`):**
   - AI coding assistants working in this repository **MUST PROACTIVELY** keep `AGENTS.md` up to date.
   - Any architectural modification, schema adjustment (`models/cv.py`), tool signature change (`server.py`), dataset update (`data/cv_data.json`), UI layout reordering (`templates/index.html`), or technical dependency adjustment must be immediately documented in this file without waiting for explicit user prompting.

2. **Canonical Baseline Data Source (`anacatalina-cv`):**
   - The primary source of truth and baseline data for candidate information (work history, skills taxonomy, projects, academic background, achievements, and bilingual summaries) is the sibling repository `anacatalina-cv` ([github.com/AnaCataVC/anacatalina-cv](https://github.com/AnaCataVC/anacatalina-cv) or locally at `../anacatalina-cv`, specifically its structured Astro components and i18n dictionaries in `src/pages/index.astro` and `src/i18n.js`).
   - `anacatalina-mcp` packages its own verified in-memory dataset in `data/cv_data.json` and operates fully standalone without hard external build-time dependencies.
   - When updating or auditing `data/cv_data.json` or curriculum benchmarks in this repository, agents can inspect and pull verified baseline data directly from `anacatalina-cv` to maintain 100% cross-portfolio ecosystem consistency.
   - Known gap: `anacatalina-cv` also has Publications and Courses & Certifications sections with no equivalent in `models/cv.py` (`CVData`). Adding them is a schema change (new Pydantic models, likely a new/extended MCP tool), not a data sync — deliberately left out of `data/cv_data.json` until requested as its own task.

---

## Operational Constraints & Architectural Decisions

These items document deliberate architectural choices and operational boundaries:

1. **`mcp` SDK Pinning (`mcp>=1.3.0,<2`):**
   - In `requirements.txt`, the official `mcp` dependency is explicitly pinned below `2.0.0`.
   - The release of `mcp==2.0.0` introduced backward-incompatible API changes to `FastMCP` and transport handlers that broke production deployment.
   - Any future migration to `mcp 2.x` must be conducted in an isolated staging branch with comprehensive local and Cloud Run verification before updating production.

2. **Unversioned `cloudbuild.yaml`:**
   - Cloud Run continuous deployment is triggered via a Google Cloud Build trigger configured directly in the GCP console.
   - The build configuration lives outside the repository. Before committing a local `cloudbuild.yaml`, verify the production build steps using `gcloud builds triggers describe <trigger>` to prevent configuration drift.

3. **Deterministic Evaluation vs. In-Memory Search:**
   - Free-text heuristic role detection was replaced with the 4 curated Forma 1 benchmarks to ensure 100% verifiable scoring and eliminate non-deterministic parsing bugs.
   - Cross-curriculum search (`buscar_en_curriculum`) performs fast, safe in-memory substring filtering across ~10 items. Because Cloud Run already caps HTTP request body sizes and memory usage is trivial (<100KB), artificial input length capping was evaluated and deemed unnecessary complexity.

4. **Streamable HTTP Migration (Zero Legacy SSE / Zero Stdio):**
   - In accordance with the March 2025 MCP specification update deprecating HTTP+SSE, the server operates exclusively via **Streamable HTTP** (`/mcp`).
   - Legacy SSE endpoints (`/sse`, `/messages/`) and the local stdio bridge (`conecta_cata.py`) were eliminated to keep the architecture clean, high-performance, and directly cloud-native for Claude.ai Custom Connectors, Cursor, and modern MCP clients.

