---
name: ac-mcp-triage-drift-issue
description: Diagnoses and resolves GitHub drift issues opened by upstream-drift.yml when self-healing auto-sync fails (new CV skills, missing i18n keys, invariant/test failures, or push errors), then verifies live sync and production health.
tools: [view_file, replace_file_content, run_command]
---

# Skill: Triage & Resolve Upstream Drift Issues (`ac-mcp-triage-drift-issue`)

Use this skill whenever `.github/workflows/upstream-drift.yml` opens a drift issue titled `Upstream drift: data/cv_data.json is out of sync` because automated remediation to `main` could not complete.

> **Policy:** Closed drift issues are **never** reopened. Each new incident gets a fresh issue and is closed automatically once `upstream-drift.yml` passes on `main`.

---

## Step 1: Inspect the Issue and Failing Run

1. Read the open issue and extract the **Failure reason**, **Workflow run ID**, and **Discrepancies** block:
   ```bash
   gh issue list -R AnaCataVC/anacatalina-mcp --state open --json number,title,url
   gh issue view <NUMBER> -R AnaCataVC/anacatalina-mcp --json title,body,comments
   ```
2. If the failure happened during `--sync`, invariants, `pytest`, or `git push`, inspect the failed step logs:
   ```bash
   gh run view <RUN_ID> -R AnaCataVC/anacatalina-mcp --log-failed | tail -150
   ```

---

## Step 2: Classify and Fix the Root Cause

Apply the fix matching the reported failure reason:

### Case A — New skill added in `anacatalina-cv` (e.g. `[skills] ... not yet in MCP skills matrix`)
1. Inspect the skill's placement in `anacatalina-cv` without cloning:
   ```bash
   gh api "repos/AnaCataVC/anacatalina-cv/contents/src/pages/index.astro?ref=main" --jq .content | base64 -d | grep -n -C 6 -i "<SKILL_NAME>"
   ```
2. Add the skill to the matching category in **both**:
   - `scripts/sync_mcp_data.py` inside `generate_synchronized_dataset()` (under `new_data["skills"]`)
   - `data/cv_data.json` (same category and level)
3. If the skill is a high-signal job-market technology, consider adding it to `TECH_ALIAS_MAP` in `services/cv_service.py` (see `ac-mcp-tune-fit-engine`).

### Case B — Missing or renamed translation key (`[cv_translations]`)
1. Inspect `anacatalina-cv/src/i18n.js` and `src/data/cv.ts` via `gh api`:
   ```bash
   gh api "repos/AnaCataVC/anacatalina-cv/contents/src/i18n.js?ref=main" --jq .content | base64 -d | grep -n -C 3 "<KEY>"
   ```
2. Update the key lookup and fallback string in `scripts/sync_mcp_data.py` (`generate_synchronized_dataset()`), then re-sync `data/cv_data.json`.

### Case C — Invariant or `pytest` regression after `--sync`
1. Reproduce locally:
   ```bash
   python scripts/verify_ecosystem_invariants.py
   python -m pytest tests/ -v
   ```
2. Fix the underlying data/parser issue **without weakening any invariant**:
   - Candidate first name is always hyphenated (`Ana-Catalina`).
   - Zero Flags Rule (never allow country flag emojis).
   - Zero hardcoded local paths.
   - All 10 official MCP tools registered and passing Pydantic v2 validation.

### Case D — `git push to main failed` or workflow permissions error
1. Check workflow permissions, branch protection, and rulesets:
   ```bash
   gh api repos/AnaCataVC/anacatalina-mcp/actions/permissions/workflow
   gh api repos/AnaCataVC/anacatalina-mcp/branches/main/protection
   gh api repos/AnaCataVC/anacatalina-mcp/rulesets
   ```
2. Verify `.github/workflows/upstream-drift.yml` has `permissions: { contents: write, issues: write }` and `concurrency: { group: upstream-drift, cancel-in-progress: false }`.

---

## Step 3: Local Quality Gate

Run all checks before pushing:
```bash
python -c "import yaml, pathlib; [yaml.safe_load(p.read_text()) for p in pathlib.Path('.github/workflows').glob('*.yml')]; print('YAML OK')"
python scripts/verify_ecosystem_invariants.py
python -m pytest tests/ -q
```

---

## Step 4: Ship via PR and Verify End-to-End Closure

1. Push changes to a feature branch (e.g. `fix/drift-<short-topic>`) and open a PR against `main`.
2. Wait for `test` and `docker-smoke` checks to pass, then merge with `--squash --delete-branch`.
3. Trigger `upstream-drift.yml` on `main` to verify zero remaining drift and automatic closure of the open drift issue:
   ```bash
   gh workflow run upstream-drift.yml -R AnaCataVC/anacatalina-mcp --ref main
   gh run watch <NEW_RUN_ID> -R AnaCataVC/anacatalina-mcp --exit-status
   ```
4. Confirm zero open drift issues and verify production deployment:
   ```bash
   gh issue list -R AnaCataVC/anacatalina-mcp --state open --json number,title
   curl -sS https://mcp.ana-catalina.com/health
   ```
