# Architecture & Technical Research: Interactive Showcase & Playground for MCP Server

## 1. Executive Summary & Problem Context

The `anacatalina-mcp` service runs as a containerized Model Context Protocol (MCP) server on Google Cloud Run. While it effectively exposes 9 MCP tools over Server-Sent Events (SSE) and local `stdio` (via `conecta_cata.py`), its primary human-facing URL (`https://anacatalina-mcp-165536131179.us-central1.run.app/`) currently returns a raw JSON dictionary (`{"name": "...", "status": "healthy"}`).

Technical evaluators, hiring managers, and recruiters reviewing a candidate profile rarely configure JSON files or install local CLI bridges to evaluate a candidate's portfolio. Providing a client-side and server-rendered interactive showcase directly at `/` bridges the gap without requiring external SaaS products, additional cloud infrastructure, or LLM billing.

---

## 2. Decision Matrix: Playground Interaction Models

| Dimension | Option 1: Deterministic Engine (Selected) | Option 2: Embedded LLM Chatbot |
| :--- | :--- | :--- |
| **API Costs & Billing** | **$0.00** (Zero runtime API tokens consumed) | Variable / Open liability (risk of token exhaustion or bot abuse) |
| **Hallucination Risk** | **0%** (Strictly grounded in verified Pydantic data) | High unless bounded by heavy prompt constraints |
| **Latency** | **< 5ms** (Direct in-memory Python / Starlette evaluation) | 800ms - 2,500ms (Streaming LLM round-trip) |
| **Maintenance Complexity** | Minimal (Standard HTTP routes calling existing `cv_service`) | High (API key rotation, secret management, rate limiters) |
| **Security & DOS Vulnerability** | Low risk (In-memory substring / Pydantic queries) | Vulnerable to prompt injection and credential scraping |

**Conclusion:** Option 1 fulfills all operational and financial constraints specified by the user.

---

## 3. Server Architecture & Content Negotiation in FastMCP / Starlette

### 3.1 Transparent Content Negotiation on Root Route (`/`)
FastMCP builds upon Starlette ASGI. The root endpoint (`/`) can utilize HTTP Content Negotiation (`Accept` header inspection):
- **Browsers:** Modern browsers send `Accept: text/html,application/xhtml+xml,...`. The endpoint returns `HTMLResponse(content=rendered_html, status_code=200)`.
- **API & Discovery Clients (curl, MCP clients, Cloud Run health probes):** When `Accept` specifies `application/json` or when queried programmatically without `text/html`, the endpoint preserves existing behavior and returns `JSONResponse({...})`.
- **Explicit Fallback:** An explicit route `/demo` or `/playground` guarantees direct web access regardless of headers.

### 3.2 REST API Bridge for the Playground
The interactive web components on the showcase page consume lightweight HTTP endpoints wired directly into `cv_service`:
- `POST /api/evaluate-fit` -> Invokes `cv_service.evaluate_job_fit(job_description)` -> Returns `FitEvaluationResult` JSON.
- `GET /api/search?q={query}` -> Invokes `cv_service.search(query)` -> Returns search matches.
- `GET /api/skills` -> Returns structured skill categories.
- `GET /api/experience` -> Returns filtered or full work experience.

These endpoints reuse 100% of the existing business logic in `services/cv_service.py`, eliminating duplicate logic and ensuring `pytest` can validate both MCP tools and REST endpoints uniformly.

---

## 4. Frontend Design Guidelines & Constraints

1. **Self-Contained & Zero-Dependency:**
   - Single HTML/CSS/JS delivery without external node build pipelines or bulky frontend frameworks.
   - Embedded SVG icons (copy, check, external link, terminal, chevron).
2. **Strict Zero Flags Rule:**
   - No regional or national flag emojis or graphics. Use clean ISO language indicators (`ES`, `EN`) or explicit text links (`Español`, `English`).
3. **Accessibility & Responsive Performance:**
   - Dark/Modern tech theme with CSS custom properties (variables).
   - High contrast, semantic HTML tags (`<header>`, `<main>`, `<section>`, `<article>`), keyboard accessible controls.
4. **Interactive Playground Features:**
   - **Fit Tester:** Real-time job description analysis with pre-filled test prompts ("Data Scientist & Machine Learning", "Logistics & Cloud Specialist", "Pastry Chef (Negative test)").
   - **Keyword Search:** Instant live filter of skills, projects, and work history.
   - **MCP Client Configurator:** Interactive code tabs for Claude Desktop and Cursor with 1-click clipboard copy.
