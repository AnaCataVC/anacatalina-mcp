> **Created:** 2026-09-08
> **Last Updated:** 2026-09-08

# MCP Streamable HTTP Transport & Claude Custom Connectors

## 1. Context & Motivation
When adding a custom connector in Claude.ai (`Claude.ai -> Settings -> Connectors -> Add Custom Connector`), Anthropic has deprecated the older multi-endpoint HTTP+SSE transport (`/sse` + `/messages/`). Claude.ai now recommends and expects **Streamable HTTP**.

Furthermore, Claude.ai performs verification requests using `POST` directly to the connector URL. When pointing to `/sse` (which in FastMCP only accepts `GET`), the server returns `HTTP 405 Method Not Allowed`, triggering the error:
> *"Ana-Catalina MCP está configurado para no requerir inicio de sesión, pero el servidor solicitó inicio de sesión al verificarlo (estado 405)."*

## 2. FastMCP Streamable HTTP Architecture
In the official Python MCP SDK (`mcp>=1.3.0,<2`):
- `FastMCP.streamable_http_app()` generates a Starlette application serving Streamable HTTP at `settings.streamable_http_path` (default: `/mcp`).
- The endpoint supports single-endpoint bidirectional communication via `POST` with `Content-Type: application/json` and `Accept: application/json, text/event-stream`.
- Session management is handled by `StreamableHTTPSessionManager`, run asynchronously via the ASGI application lifespan (`mcp.session_manager.run()`).

## 3. Dual-Transport Architecture (Backward Compatibility Invariant)
To maintain 100% backward compatibility with:
1. Existing Cursor setups (`mcp.json` pointing to `/sse`)
2. Local `conecta_cata.py` stdio bridge (`sse_client` pointing to `/sse`)
3. New Claude.ai Custom Connectors (`https://mcp.ana-catalina.com/mcp`)
4. Web showcase and REST discovery routes (`/`, `/demo`, `/health`, `/api/*`)

The server application can mount both transports simultaneously under a unified Starlette ASGI app:
- `/mcp`: Streamable HTTP endpoint for Claude.ai and modern MCP clients.
- `/sse` & `/messages`: SSE transport endpoints for Cursor and `conecta_cata.py`.
- `/` (HTML/JSON), `/demo`, `/health`, `/api/*`: Web showcase and REST utilities.
- Lifespan runner: `mcp.session_manager.run()` ensures Streamable HTTP sessions are managed properly.

## 4. Claude.ai Setup Target
- **Connector Name:** `Ana-Catalina MCP`
- **URL:** `https://mcp.ana-catalina.com/mcp`
- **Transport:** Streamable HTTP
- **Authentication:** None (public showcase server)
