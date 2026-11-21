# Repository Automations Inventory

This document catalogs the automated CI/CD pipelines, Git lifecycle hooks, task runners, and maintenance utilities configured in `anacatalina-mcp`.

## 1. CI/CD Workflows (`.github/workflows/`)

| Workflow | Trigger | Purpose | Status |
| :--- | :--- | :--- | :--- |
| `.github/workflows/test.yml` | `push` (`main`), `pull_request` | Runs `scripts/verify_ecosystem_invariants.py`, `pytest` with coverage (`models`, `services`, `server`), `pip_audit` on `requirements.txt`, and a `docker-smoke` job building `Dockerfile` and verifying `import server`. | Healthy |
| `.github/workflows/upstream-drift.yml` | `schedule` (`0 11 * * *`), `workflow_dispatch` | Audits `data/cv_data.json` against `AnaCataVC/anacatalina-cv` and `AnaCataVC/projects-hub`, auto-syncs directly to `main` after passing invariants, `pytest`, and a post-sync audit, closes any open drift issue automatically, and only opens/reopens an issue if auto-remediation fails. | Healthy |
| `.github/workflows/release.yml` | `push` (tags `v*`) | Verifies the tag matches `APP_VERSION` in `server.py`, runs invariants and `pytest`, and creates a GitHub Release with `--generate-notes`. | Healthy |
| `.github/dependabot.yml` | Monthly schedule | Groups `pip` and `github-actions` dependency updates while ignoring major `mcp` version bumps. | Healthy |

## 2. Git Lifecycle Hooks (`.githooks/`)

| Hook | Activation | Checks |
| :--- | :--- | :--- |
| `.githooks/pre-push` | `.\scripts\tasks.ps1 setup-hooks` (sets `git config core.hooksPath .githooks`) | Automatically resolves `.venv/Scripts/python.exe` (or `.venv/bin/python`), runs `scripts/verify_ecosystem_invariants.py`, and executes `pytest tests/ -q` before pushing. |

## 3. Unified Task Runner & Maintenance Scripts (`scripts/`)

| Command | Script | Purpose |
| :--- | :--- | :--- |
| `.\scripts\tasks.ps1 test` | `scripts/tasks.py` | Runs the full `pytest` suite (`tests/`). |
| `.\scripts\tasks.ps1 cov` | `scripts/tasks.py` | Runs `pytest` with terminal coverage report. |
| `.\scripts\tasks.ps1 invariants` | `scripts/verify_ecosystem_invariants.py` | Validates Zero Flags, Path Privacy, Candidate Identity, and the 10-tool MCP catalog. |
| `.\scripts\tasks.ps1 audit` | `scripts/sync_mcp_data.py --audit` | Checks for data drift against sibling repositories (`../anacatalina-cv`, `../projects-hub`). |
| `.\scripts\tasks.ps1 sync` | `scripts/sync_mcp_data.py --sync` | Synchronizes `data/cv_data.json`, then runs invariants and `pytest`. |
| `.\scripts\tasks.ps1 sec` | `scripts/tasks.py` | Runs `pip_audit -r requirements.txt`. |
| `.\scripts\tasks.ps1 serve` | `scripts/tasks.py` | Frees orphaned port `8080` on Windows and starts `uvicorn server:app --reload`. |
| `.\scripts\tasks.ps1 setup-hooks` | `scripts/tasks.py` | Configures `git config core.hooksPath .githooks`. |
| `.\scripts\tasks.ps1 bump -Version X.Y.Z` | `scripts/bump_version.py` | Updates `APP_VERSION` in `server.py` and validates invariants and `pytest` (rolls back on failure). |
| `.\scripts\tasks.ps1 check-all` | `scripts/tasks.py` | Runs the full local quality gate: invariants, drift check, `pytest`, and `pip_audit`. |
