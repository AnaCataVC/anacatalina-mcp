"""
test_invariants.py — Automated test verifying ecosystem invariants and data integrity.
"""
from scripts.verify_ecosystem_invariants import run_all_checks


def test_ecosystem_invariants_pass():
    """Verify that Zero Flags, Path Privacy, Identity, and MCP Tool catalog pass 100%."""
    success, errors = run_all_checks()
    assert success, f"Ecosystem invariant violations: {errors}"
