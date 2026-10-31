#!/usr/bin/env python3
"""
tasks.py — Unified cross-platform task runner for anacatalina-mcp.

Usage:
    python scripts/tasks.py test
    python scripts/tasks.py cov
    python scripts/tasks.py invariants
    python scripts/tasks.py audit
    python scripts/tasks.py sync
    python scripts/tasks.py sec
    python scripts/tasks.py serve [--port 8080]
    python scripts/tasks.py check-all
"""

from __future__ import annotations

import argparse
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


def run_cmd(cmd: list[str]) -> int:
    """Execute a command in project root and return exit code."""
    print(f"\n🚀 Running: {' '.join(cmd)}\n")
    res = subprocess.run(cmd, cwd=ROOT_DIR)
    return res.returncode


def task_test() -> int:
    return run_cmd([sys.executable, "-m", "pytest", "tests/", "-v"])


def task_cov() -> int:
    return run_cmd([
        sys.executable, "-m", "pytest", "tests/", "-v",
        "--cov=models", "--cov=services", "--cov=server", "--cov-report=term-missing"
    ])


def task_invariants() -> int:
    return run_cmd([sys.executable, "scripts/verify_ecosystem_invariants.py"])


def task_audit() -> int:
    return run_cmd([sys.executable, "scripts/sync_mcp_data.py", "--audit"])


def task_sync() -> int:
    code = run_cmd([sys.executable, "scripts/sync_mcp_data.py", "--sync"])
    if code != 0:
        return code
    inv_code = task_invariants()
    if inv_code != 0:
        return inv_code
    return task_test()


def task_sec() -> int:
    return run_cmd([sys.executable, "-m", "pip_audit", "-r", "requirements.txt"])


def task_serve(port: int = 8080) -> int:
    if sys.platform == "win32":
        # Free port if orphaned process is holding it
        kill_cmd = [
            "powershell", "-NoProfile", "-Command",
            f"$c = Get-NetTCPConnection -LocalPort {port} -ErrorAction SilentlyContinue; "
            f"if ($c) {{ Stop-Process -Id $c.OwningProcess -Force -ErrorAction SilentlyContinue }}"
        ]
        subprocess.run(kill_cmd, cwd=ROOT_DIR)
    return run_cmd([sys.executable, "-m", "uvicorn", "server:app", "--reload", "--port", str(port)])


def task_check_all() -> int:
    steps = [
        ("Ecosystem Invariants", [sys.executable, "scripts/verify_ecosystem_invariants.py"]),
        ("Upstream Data Drift Check", [sys.executable, "scripts/sync_mcp_data.py", "--check-only"]),
        ("Automated Test Suite", [sys.executable, "-m", "pytest", "tests/", "-v"]),
        ("Dependency Vulnerability Audit", [sys.executable, "-m", "pip_audit", "-r", "requirements.txt"]),
    ]
    for name, cmd in steps:
        print(f"\n=======================================================")
        print(f"▶ STEP: {name}")
        print(f"=======================================================")
        ret = run_cmd(cmd)
        if ret != 0:
            print(f"\n❌ Step '{name}' failed with exit code {ret}.", file=sys.stderr)
            return ret
    print("\n=======================================================")
    print("✅ All check-all quality gates passed successfully!")
    print("=======================================================\n")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Unified task runner for anacatalina-mcp.")
    parser.add_argument(
        "task",
        choices=["test", "cov", "invariants", "audit", "sync", "sec", "serve", "check-all"],
        help="Task to execute",
    )
    parser.add_argument("--port", type=int, default=8080, help="Port for server (default: 8080)")

    args = parser.parse_args()

    if args.task == "test":
        return task_test()
    elif args.task == "cov":
        return task_cov()
    elif args.task == "invariants":
        return task_invariants()
    elif args.task == "audit":
        return task_audit()
    elif args.task == "sync":
        return task_sync()
    elif args.task == "sec":
        return task_sec()
    elif args.task == "serve":
        return task_serve(port=args.port)
    elif args.task == "check-all":
        return task_check_all()
    return 0


if __name__ == "__main__":
    sys.exit(main())
