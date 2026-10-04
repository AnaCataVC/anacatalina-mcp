"""
Cleanroom Black-Box Tests for Content Negotiation & Showcase Endpoints.

Based strictly on the formal behavioral contract:
docs/contracts/mcp-landing-unification.contract.md

Contract Invariants:
1. GET / with browser Accept header containing 'text/html' returns 200 OK with HTML content
   and does NOT return a 301/302 redirect.
2. GET / with 'application/json' or without Accept header returns 200 OK with JSON matching
   the formal DISCOVERY_PAYLOAD schema.
3. GET /demo returns 200 OK with HTML content.
"""
import pytest
from starlette.testclient import TestClient

from server import app


EXPECTED_DISCOVERY_SCHEMA = {
    "name": "Ana-Catalina Interactive Portfolio MCP",
    "status": "healthy",
    "version": "1.5.0",
    "mcp_endpoint": "/mcp",
    "health_endpoint": "/health",
    "web_showcase": "/demo",
    "demo_endpoint": "/demo",
}


@pytest.fixture
def client():
    """Provides a Starlette TestClient with redirects disabled by default for strict status assertions."""
    return TestClient(app, follow_redirects=False)


class TestRootContentNegotiation:
    """Verifies content negotiation behavior at GET / based on Accept headers."""

    def test_root_with_html_accept_returns_200_html(self, client: TestClient):
        """
        Contract Scenario 1:
        Root GET / with 'Accept: text/html' MUST return status_code == 200,
        Content-Type containing 'text/html', and no redirect.
        """
        response = client.get("/", headers={"Accept": "text/html"})

        assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}"
        content_type = response.headers.get("content-type", "")
        assert "text/html" in content_type, f"Expected Content-Type to contain 'text/html', got '{content_type}'"
        assert len(response.text.strip()) > 0, "Response body must not be empty"

    def test_root_with_browser_accept_header_returns_200_html(self, client: TestClient):
        """
        Contract Scenario 1 (Browser composite Accept header):
        Typical browser Accept string prioritizing text/html must return 200 HTML.
        """
        browser_accept = "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
        response = client.get("/", headers={"Accept": browser_accept})

        assert response.status_code == 200
        content_type = response.headers.get("content-type", "")
        assert "text/html" in content_type

    def test_root_html_does_not_redirect(self, client: TestClient):
        """
        Contract Prohibited:
        Root GET / with HTML accept MUST NOT return a 301 or 302 redirect.
        """
        response = client.get("/", headers={"Accept": "text/html"})
        assert response.status_code not in (301, 302, 307, 308), (
            f"Prohibited redirect detected: status {response.status_code} with Location: {response.headers.get('location')}"
        )
        assert "location" not in response.headers

    def test_root_with_json_accept_returns_discovery_payload(self, client: TestClient):
        """
        Contract Scenario 2:
        Root GET / with 'Accept: application/json' MUST return status_code == 200,
        Content-Type containing 'application/json', and body conforming to the discovery schema.
        """
        response = client.get("/", headers={"Accept": "application/json"})

        assert response.status_code == 200
        content_type = response.headers.get("content-type", "")
        assert "application/json" in content_type

        data = response.json()
        assert isinstance(data, dict)
        assert data == EXPECTED_DISCOVERY_SCHEMA

    def test_root_without_accept_header_defaults_to_json(self, client: TestClient):
        """
        Contract Scenario 2 (Machine/Default):
        Root GET / without Accept header MUST return 200 OK with JSON discovery payload.
        """
        response = client.get("/")

        assert response.status_code == 200
        content_type = response.headers.get("content-type", "")
        assert "application/json" in content_type

        data = response.json()
        assert data == EXPECTED_DISCOVERY_SCHEMA

    def test_root_with_non_html_accept_defaults_to_json(self, client: TestClient):
        """
        Contract Scenario 2:
        Requests specifying non-HTML types (e.g. */* or application/*) fall back to JSON discovery.
        """
        response = client.get("/", headers={"Accept": "*/*"})

        assert response.status_code == 200
        content_type = response.headers.get("content-type", "")
        assert "application/json" in content_type

        data = response.json()
        assert data["mcp_endpoint"] == "/mcp"
        assert data["health_endpoint"] == "/health"
        assert data["web_showcase"] == "/demo"
        assert data["demo_endpoint"] == "/demo"


class TestDemoEndpoint:
    """Verifies the direct web showcase route GET /demo."""

    def test_demo_returns_200_html(self, client: TestClient):
        """
        Contract Requirement:
        GET /demo MUST return status_code == 200 OK and Content-Type containing 'text/html'.
        """
        response = client.get("/demo")

        assert response.status_code == 200
        content_type = response.headers.get("content-type", "")
        assert "text/html" in content_type
        assert len(response.text.strip()) > 0
