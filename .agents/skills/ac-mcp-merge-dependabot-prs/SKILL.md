---
name: ac-mcp-merge-dependabot-prs
description: Reviews, rebases (resolving adjacent-line conflicts in requirements files), merges Dependabot PRs while enforcing AGENTS.md upper-bound pins, and verifies main CI and live Cloud Run health.
tools: [view_file, replace_file_content, run_command]
---

# Skill: Review & Merge Dependabot PRs (`ac-mcp-merge-dependabot-prs`)

Use this skill to safely clear open Dependabot dependency PRs in `anacatalina-mcp` without introducing merge conflicts, breaking upper-bound pins, or degrading the live Cloud Run deployment.

---

## Step 1: Audit All Open Dependabot PRs

1. List open PRs with their CI status:
   ```bash
   gh pr list -R AnaCataVC/anacatalina-mcp --state open --limit 30 \
     --json number,title,author,headRefName,statusCheckRollup,url
   ```
2. Inspect every diff before merging:
   ```bash
   gh pr diff <NUMBER> -R AnaCataVC/anacatalina-mcp
   ```
3. **Mandatory Pinning Gate (`AGENTS.md`):**
   - Reject or hold any bump that removes or crosses major upper bounds in `requirements.txt`:
     - `mcp<2.0.0` (FastMCP v2 has breaking API changes)
     - `uvicorn<1.0.0`
     - `starlette<2.0.0`
     - `pydantic<3.0.0`
     - `anyio<5.0.0`
     - `httpx<1.0.0`
   - Verify both `test` (invariants + pytest + `pip_audit`) and `docker-smoke` checks are `SUCCESS`.

---

## Step 2: Merge Cleanly & Resolve Adjacent-Line Conflicts

Dependabot PRs updating `requirements.txt` often touch adjacent lines and conflict after the first merge.

1. Merge conflict-free PRs first (`requirements-dev.txt`, `github-actions`, and the first `requirements.txt` PR):
   ```bash
   gh pr merge <NUMBER> -R AnaCataVC/anacatalina-mcp --squash --delete-branch
   ```
2. If a subsequent PR fails with `Pull Request has merge conflicts`:
   - Reset the PR branch onto the latest `origin/main`:
     ```bash
     git fetch origin
     git checkout -B <HEAD_REF_NAME> origin/main
     ```
   - Re-apply the PR's single version bump cleanly on top of the updated `requirements.txt` / `requirements-dev.txt`.
   - Commit and force-push back to the PR branch:
     ```bash
     git add requirements.txt
     git commit -m "<PR_TITLE>"
     git push -f origin <HEAD_REF_NAME>
     ```
   - Wait for fresh CI checks (`test` + `docker-smoke`) to pass before merging:
     ```bash
     gh pr checks <NUMBER> -R AnaCataVC/anacatalina-mcp --watch
     gh pr merge <NUMBER> -R AnaCataVC/anacatalina-mcp --squash --delete-branch
     ```

---

## Step 3: Post-Merge CI, Repo Hygiene & Production Smoke Check

1. Sync local `main`, delete any temporary local branches, and confirm clean repository state:
   ```bash
   git checkout main && git pull --ff-only origin main
   gh api repos/AnaCataVC/anacatalina-mcp/branches --jq '.[].name'
   gh pr list -R AnaCataVC/anacatalina-mcp --state open --json number
   ```
2. Watch the latest `Tests` run on `main` (verifies `pytest`, `pip_audit`, and `docker-smoke` with all merged updates combined):
   ```bash
   gh run list -R AnaCataVC/anacatalina-mcp --branch main --workflow test.yml --limit 1 --json databaseId,status,conclusion,url
   gh run watch <RUN_ID> -R AnaCataVC/anacatalina-mcp --exit-status
   ```
3. Confirm live Cloud Run service health:
   ```bash
   curl -sS --max-time 10 https://mcp.ana-catalina.com/health
   curl -sS --max-time 10 -H "Accept: application/json" https://mcp.ana-catalina.com/
   ```
