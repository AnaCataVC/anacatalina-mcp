#!/usr/bin/env python3
"""
bump_version.py — Automated version bumper and release validator for anacatalina-mcp.

Usage:
    python scripts/bump_version.py 1.10.0
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


def bump_version(new_version: str) -> int:
    if not re.match(r"^\d+\.\d+\.\d+$", new_version):
        print(f"❌ Invalid semantic version: '{new_version}'. Expected format: X.Y.Z", file=sys.stderr)
        return 1

    server_py = ROOT_DIR / "server.py"
    content = server_py.read_text(encoding="utf-8")

    old_match = re.search(r'APP_VERSION\s*=\s*["\']([^"\']+)["\']', content)
    if not old_match:
        print("❌ Could not find APP_VERSION in server.py", file=sys.stderr)
        return 1

    old_version = old_match.group(1)
    if old_version == new_version:
        print(f"ℹ️ Version is already {new_version}.", file=sys.stderr)
        return 0

    new_content = re.sub(
        r'APP_VERSION\s*=\s*["\'][^"\']+["\']',
        f'APP_VERSION = "{new_version}"',
        content,
    )
    server_py.write_text(new_content, encoding="utf-8")
    print(f"✅ Bumped server.py APP_VERSION: {old_version} ➔ {new_version}")

    # Validate ecosystem invariants and automated tests
    print("\n🔍 Validating ecosystem invariants...")
    inv_res = subprocess.run([sys.executable, "scripts/verify_ecosystem_invariants.py"], cwd=ROOT_DIR)
    if inv_res.returncode != 0:
        print("❌ Ecosystem invariants failed. Reverting...", file=sys.stderr)
        server_py.write_text(content, encoding="utf-8")
        return inv_res.returncode

    print("\n🧪 Running automated test suite...")
    test_res = subprocess.run([sys.executable, "-m", "pytest", "tests/", "-q"], cwd=ROOT_DIR)
    if test_res.returncode != 0:
        print("❌ Tests failed. Reverting version bump...", file=sys.stderr)
        server_py.write_text(content, encoding="utf-8")
        return test_res.returncode

    print(f"\n🎉 Version successfully bumped to {new_version} with 100% passing tests!")
    print(f"\nSuggested git commit:")
    print(f"    git add server.py")
    print(f"    git commit -m \"chore(release): bump version to {new_version}\"")
    return 0


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python scripts/bump_version.py <NEW_VERSION>", file=sys.stderr)
        return 1
    return bump_version(sys.argv[1])


if __name__ == "__main__":
    sys.exit(main())
