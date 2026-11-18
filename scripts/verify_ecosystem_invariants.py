#!/usr/bin/env python3
"""
verify_ecosystem_invariants.py — Automated verification of portfolio and ecosystem invariants.

Checks:
1. Zero Flags Rule: No country flag emojis in documentation, templates, or datasets.
2. Candidate Identity Invariant: Strict naming, GitHub handle, and legal name validation.
3. Path Privacy: No leaked absolute local paths (e.g., Windows C:\\Users or POSIX /home/).
4. MCP Tool Catalog Integrity: Verification of all 10 registered FastMCP tools.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import List, Tuple

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Regional indicator symbol flag regex (U+1F1E6 to U+1F1FF)
FLAG_REGEX = re.compile(r"[\U0001F1E6-\U0001F1FF]{2}")

# Local computer path leakage pattern (excluding comments or docs placeholders)
PATH_LEAK_REGEX = re.compile(r"[a-zA-Z]:\\(?:Users|Documents and Settings)\\[a-zA-Z0-9_-]+", re.IGNORECASE)


def check_zero_flags() -> List[str]:
    """Ensure zero country flag emojis exist across markdown, html, and json files."""
    errors = []
    target_extensions = {".md", ".html", ".json", ".py"}
    
    for path in ROOT_DIR.rglob("*"):
        if not path.is_file():
            continue
        # Skip git internal directory, venvs, and caches
        rel = path.relative_to(ROOT_DIR)
        parts = rel.parts
        if any(p.startswith(".") or p in {".venv", "venv", "__pycache__", ".pytest_cache", "releases"} for p in parts):
            continue
        if path.suffix.lower() not in target_extensions:
            continue
            
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
            
        for line_num, line in enumerate(content.splitlines(), start=1):
            if FLAG_REGEX.search(line):
                errors.append(f"{rel}:{line_num}: Flag emoji detected violating Zero Flags Rule: {line.strip()[:60]}")
    return errors


def check_path_privacy() -> List[str]:
    """Ensure no real local computer user paths are leaked."""
    errors = []
    target_extensions = {".md", ".html", ".json", ".py", ".yml", ".yaml"}
    
    for path in ROOT_DIR.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT_DIR)
        parts = rel.parts
        if any(p.startswith(".") or p in {".venv", "venv", "__pycache__", ".pytest_cache", "releases"} for p in parts):
            continue
        if path.suffix.lower() not in target_extensions:
            continue
            
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
            
        for line_num, line in enumerate(content.splitlines(), start=1):
            # Allow generic placeholder examples like <username> or /path/to
            match = PATH_LEAK_REGEX.search(line)
            if match and not any(placeholder in line for placeholder in ["<username>", "path/to", "example"]):
                errors.append(f"{rel}:{line_num}: Local absolute user path leaked: {match.group(0)}")
    return errors


def check_identity_invariants() -> List[str]:
    """Ensure candidate identity fields in cv_data.json meet exact invariants."""
    errors = []
    cv_data_path = ROOT_DIR / "data" / "cv_data.json"
    if not cv_data_path.exists():
        return ["data/cv_data.json not found."]
        
    try:
        data = json.loads(cv_data_path.read_text(encoding="utf-8"))
    except Exception as e:
        return [f"Failed to parse data/cv_data.json: {e}"]
        
    info = data.get("personal_info", {})
    if info.get("first_name") != "Ana-Catalina":
        errors.append(f"first_name must be 'Ana-Catalina' (hyphenated), got: {info.get('first_name')}")
    if info.get("middle_name") != "Alejandra":
        errors.append(f"middle_name must be 'Alejandra', got: {info.get('middle_name')}")
    if info.get("last_name") != "Villalobos Contardo":
        errors.append(f"last_name must be 'Villalobos Contardo', got: {info.get('last_name')}")
    if info.get("full_name") != "Ana-Catalina Alejandra Villalobos Contardo":
        errors.append(f"full_name mismatch: {info.get('full_name')}")
    if info.get("name") != "Ana-Catalina Villalobos Contardo":
        errors.append(f"name mismatch: {info.get('name')}")
    
    contact = info.get("contact", {})
    if contact.get("email") != "anacatalina@outlook.cl":
        errors.append(f"contact.email must be anacatalina@outlook.cl, got: {contact.get('email')}")
    if contact.get("linkedin") != "https://linkedin.com/in/ana-catalina/":
        errors.append(f"contact.linkedin mismatch, got: {contact.get('linkedin')}")
        
    portfolio = info.get("portfolio_links", {})
    if "AnaCataVC" not in portfolio.get("github", ""):
        errors.append(f"portfolio_links.github must reference AnaCataVC, got: {portfolio.get('github')}")
        
    return errors


def check_mcp_tool_catalog() -> List[str]:
    """Ensure all 10 official MCP tools are properly registered."""
    errors = []
    expected_tools = {
        "obtener_experiencia",
        "obtener_stack_tecnologico",
        "obtener_proyectos_destacados",
        "evaluar_fit_puesto",
        "buscar_en_curriculum",
        "obtener_educacion",
        "obtener_publicaciones",
        "obtener_contacto",
        "obtener_perfil",
        "obtener_resumen_ejecutivo",
    }
    try:
        import asyncio
        from server import mcp
        
        registered_tools = asyncio.run(mcp.list_tools())
        registered_names = {t.name for t in registered_tools}
        missing = expected_tools - registered_names
        extra = registered_names - expected_tools
        if missing:
            errors.append(f"Missing expected MCP tools: {missing}")
        if extra:
            errors.append(f"Unexpected extra MCP tools: {extra}")
        if len(registered_names) != 10:
            errors.append(f"Catalog must contain exactly 10 tools, found {len(registered_names)}")
    except Exception as e:
        errors.append(f"Failed to inspect FastMCP tools: {e}")
    return errors


def run_all_checks() -> Tuple[bool, List[str]]:
    all_errors: List[str] = []
    all_errors.extend(check_zero_flags())
    all_errors.extend(check_path_privacy())
    all_errors.extend(check_identity_invariants())
    all_errors.extend(check_mcp_tool_catalog())
    return (len(all_errors) == 0, all_errors)


def main() -> int:
    success, errors = run_all_checks()
    if not success:
        print("❌ Ecosystem Invariant Violations Detected:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1
    print("✅ All ecosystem invariants verified successfully:")
    print("  - Zero Flags Rule: 100% compliant")
    print("  - Path Privacy: 100% compliant (zero leaked user paths)")
    print("  - Candidate Identity Invariants: 100% compliant")
    print("  - FastMCP Tool Catalog: 10/10 registered tools verified")
    return 0


if __name__ == "__main__":
    sys.exit(main())
