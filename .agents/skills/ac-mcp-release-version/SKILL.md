---
name: ac-mcp-release-version
description: Guided release checklist to validate quality gates, bump APP_VERSION, and prepare a vX.Y.Z GitHub release tag.
tools: [view_file, run_command]
---

# Skill: Release Version (`ac-mcp-release-version`)

Use this checklist when preparing a new semantic version release of `anacatalina-mcp`.

## Workflow

1. **Pre-Release Quality Gate**
   - Verify clean git status and active GitHub account (`AnaCataVC`):
     ```powershell
     gh auth switch -u AnaCataVC --hostname github.com 2>$null
     .\scripts\tasks.ps1 check-all
     ```
   - Resolve any drift, invariant failure, test failure, or vulnerability before bumping.

2. **Bump Version**
   - Run the automated bumper (updates `APP_VERSION` in `server.py` and re-runs invariants + `pytest`):
     ```powershell
     .\scripts\tasks.ps1 bump -Version <X.Y.Z>
     ```

3. **Verify Documentation Consistency**
   - Confirm `AGENTS.md`, `README.md`, and `README.es.md` reflect any new endpoints, tools, or client configs included in this release.

4. **Commit & Tag**
   - Commit the version bump using Conventional Commits:
     ```powershell
     git add server.py
     git commit -m "chore(release): bump version to <X.Y.Z>"
     git tag "v<X.Y.Z>"
     ```
   - Pushing the `v<X.Y.Z>` tag triggers `.github/workflows/release.yml`, which validates `APP_VERSION`, runs tests, and publishes the GitHub Release.
