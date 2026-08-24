#!/usr/bin/env python3
"""
conecta_cata.py - Lightweight stdio-to-SSE bridge for Model Context Protocol (MCP).

This script allows local MCP clients (such as Claude Desktop or IDE extensions)
that communicate via standard I/O (stdin/stdout) to seamlessly interact with
the remote Ana Catalina MCP server hosted on Google Cloud Run via Server-Sent Events (SSE).

Usage:
    python conecta_cata.py
    (or specify custom URL via MCP_SERVER_SSE_URL environment variable)
"""
import os
import sys
import anyio
from mcp.server.stdio import stdio_server
from mcp.client.sse import sse_client

DEFAULT_REMOTE_SSE_URL = "http://localhost:8080/sse"


async def bridge_stdio_to_sse(sse_url: str):
    """
    Establishes a local stdio server and a remote SSE client connection,
    piping JSON-RPC messages bi-directionally between them.
    """
    # 1. Start local stdio server (listens to Claude Desktop via stdin/stdout)
    async with stdio_server() as (stdio_read, stdio_write):
        # 2. Connect to remote SSE server (e.g. Cloud Run endpoint)
        async with sse_client(sse_url) as (sse_read, sse_write):
            # 3. Pipe streams concurrently
            async with anyio.create_task_group() as tg:

                async def pipe_stdio_in_to_sse_out():
                    try:
                        async for msg in stdio_read:
                            await sse_write.send(msg)
                    except Exception as exc:
                        sys.stderr.write(f"[Bridge] Error sending stdio -> SSE: {exc}\n")
                        sys.stderr.flush()

                async def pipe_sse_in_to_stdio_out():
                    try:
                        async for msg in sse_read:
                            await stdio_write.send(msg)
                    except Exception as exc:
                        sys.stderr.write(f"[Bridge] Error sending SSE -> stdio: {exc}\n")
                        sys.stderr.flush()

                tg.start_soon(pipe_stdio_in_to_sse_out)
                tg.start_soon(pipe_sse_in_to_stdio_out)


def main():
    """Main entrypoint for the bridge script."""
    sse_url = os.getenv("MCP_SERVER_SSE_URL", DEFAULT_REMOTE_SSE_URL)

    # Note: ALWAYS write logs to stderr, never stdout (stdout is reserved for JSON-RPC)
    sys.stderr.write(f"[Bridge] Conectando cliente stdio con servidor MCP SSE en: {sse_url}\n")
    sys.stderr.flush()

    try:
        anyio.run(bridge_stdio_to_sse, sse_url)
    except (KeyboardInterrupt, anyio.get_cancelled_exc_class()):
        sys.stderr.write("[Bridge] Conexión puente cerrada limpiamente.\n")
        sys.stderr.flush()
    except Exception as e:
        sys.stderr.write(f"[Bridge] Error crítico en puente MCP: {e}\n")
        sys.stderr.flush()
        sys.exit(1)


if __name__ == "__main__":
    main()
