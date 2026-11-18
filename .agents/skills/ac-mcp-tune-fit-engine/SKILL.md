---
name: ac-mcp-tune-fit-engine
description: Safely update TECH_ALIAS_MAP, regex matching, scoring tiers, and showcase presets for the deterministic job fit evaluator.
tools: [view_file, grep_search, replace_file_content, run_command]
---

# Skill: Tune Deterministic Job Fit Engine (`ac-mcp-tune-fit-engine`)

Use this workflow when adding technology aliases, adjusting regex boundary matching, or modifying scoring tiers in `evaluar_fit_puesto` and `/api/evaluate-fit`.

## Rules & Invariants

- **Zero External LLM Calls:** All matching must remain 100% deterministic, regex/in-memory based, and execute in under 5ms.
- **Zero False Positives:** Unrelated or non-technical roles (such as the `pop-singer` negative test preset) must continue returning `0%`.
- **Word Boundaries:** Watch for short tokens (e.g., `R`, `Go`, `AI`, `SQL`) so they do not match substrings inside unrelated words.

## Workflow

1. **Inspect Current Engine**
   - Read `TECH_ALIAS_MAP` and `evaluate_fit` in `services/cv_service.py`.
   - Check the 4 showcase presets (`data-science`, `logistics`, `agents`, `pop-singer`) in `templates/index.html` and `services/cv_service.py`.

2. **Apply Changes**
   - Update `TECH_ALIAS_MAP` or scoring thresholds in `services/cv_service.py`.
   - Ensure any new technology referenced in `TECH_ALIAS_MAP` corresponds to real verified experience or skills in `data/cv_data.json`.

3. **Update Documentation & Tests**
   - Add positive and negative boundary test cases in `tests/test_server.py`.
   - If scoring tier ranges or presets changed, update `AGENTS.md`.

4. **Verification Gate**
   - Run:
     ```powershell
     .\scripts\tasks.ps1 test
     .\scripts\tasks.ps1 invariants
     ```
