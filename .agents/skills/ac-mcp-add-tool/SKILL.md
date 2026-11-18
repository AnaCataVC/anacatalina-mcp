---
name: ac-mcp-add-tool
description: Procedural checklist to add or modify an MCP tool across schemas, services, server, invariants, tests, UI showcase, and docs.
tools: [view_file, grep_search, replace_file_content, multi_replace_file_content, run_command]
---

# Skill: Add or Modify an MCP Tool (`ac-mcp-add-tool`)

Use this procedural workflow whenever adding a new `@mcp.tool()` or modifying an existing tool signature in `anacatalina-mcp`.

## Workflow

1. **Schema (`models/cv.py`)**
   - Define or update the Pydantic v2 request/response models with strict types and docstrings.
   - Export any new model in `models/__init__.py` if needed.

2. **Service Logic (`services/cv_service.py`)**
   - Implement the deterministic in-memory query or transformation on `CVService`.
   - Keep responses sub-5ms with zero external network or LLM calls.

3. **MCP Tool & Optional REST Endpoint (`server.py`)**
   - Register or update `@mcp.tool()` with clear Spanish/English parameter descriptions matching existing conventions.
   - If the tool should also be exposed to the web showcase or direct HTTP clients, add or update the corresponding `/api/...` Starlette route.

4. **Invariant & Test Synchronization**
   - Update `scripts/verify_ecosystem_invariants.py` if the official tool count or expected tool name list changed.
   - Add protocol, schema, and edge-case tests in `tests/test_server.py` and `tests/test_invariants.py`.

5. **Showcase & Documentation Parity**
   - Update Card 2 (MCP Tools Catalog) in `templates/index.html` if a tool was added, renamed, or changed parameters.
   - Update the Official MCP Tools Catalog table in `AGENTS.md`, `README.md`, and `README.es.md`.
   - Follow the Zero Flags Rule and Path Privacy Rule across all edited files.

6. **Verification Gate**
   - Run:
     ```powershell
     .\scripts\tasks.ps1 invariants
     .\scripts\tasks.ps1 test
     ```
