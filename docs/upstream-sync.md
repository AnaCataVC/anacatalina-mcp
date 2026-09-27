# Upstream sync and drift detection

`data/cv_data.json` is this server's own copy of the candidate data. Its sources of truth live in two sibling repositories, and this document explains how the copy is kept current and how drift is detected.

## What is synced, and from where

| Source repo | Files read | Feeds |
| :--- | :--- | :--- |
| [anacatalina-cv](https://github.com/AnaCataVC/anacatalina-cv) | `src/i18n.js`, `src/data/cv.ts` | Headline, experience periods, locations and bullets |
| anacatalina-cv | `src/pages/index.astro` (`#skills` badges) | Skills matrix |
| [projects-hub](https://github.com/AnaCataVC/projects-hub) | `src/content/projects/es/*.md` (frontmatter) | Featured projects |

`scripts/sync_mcp_data.py` does both jobs:

- `--audit` (default) compares `data/cv_data.json` against the sources and lists discrepancies. `--check-only` exits `1` when there are discrepancies; `--json` prints the report as JSON.
- `--sync` rebuilds `data/cv_data.json` and validates it against `models.cv.CVData`.

The script expects the three repos side by side (`../anacatalina-cv`, `../projects-hub`); `--cv-dir` and `--projects-dir` override that.

## How drift is detected

`.github/workflows/upstream-drift.yml` runs daily (and on demand via *Run workflow*):

1. It checks out this repo plus `main` of both sources as sibling folders, so the audit always compares against published content, never a local branch or uncommitted edits.
2. It runs `sync_mcp_data.py --check-only`.
3. On drift, it opens (or reopens and comments on) a single issue titled *Upstream drift: data/cv_data.json is out of sync* with the full report. Once the audit passes again, it closes that issue.

The workflow is deliberately separate from `test.yml`: a drift is caused by a commit in another repo, so it must not fail the PR under review.

### Why content comparison instead of pinned SHAs

Some projects pin the blob SHA of each upstream file and flag any change. That fits upstreams owned by other teams, where you can only react by reading the diff. Here all three repos share an owner and are public, and the audit already compares the content itself, so it reports *what* changed. A pinned SHA would also fire on every commit that touches a source file without changing the CV data.

## Missing translation keys

`--sync` reads each text from `i18n.js` by key and, if the key is absent, falls back to a hardcoded string in the script. Without a check, renaming or deleting a key in anacatalina-cv would make `--sync` silently revert to stale text.

The audit therefore reports every key the sync depends on that is missing from `i18n.js` (component `cv_translations`). To resolve one, either restore the key in anacatalina-cv, or update the key name and fallback in `generate_synchronized_dataset()` if the rename was intentional.

## Resolving a drift issue

```powershell
.venv\Scripts\python.exe scripts/sync_mcp_data.py --audit     # read the discrepancies
.venv\Scripts\python.exe scripts/sync_mcp_data.py --sync      # rebuild data/cv_data.json
.venv\Scripts\python.exe -m pytest tests/ -v                  # quality gate
```

Review the diff of `data/cv_data.json` before committing: identity fields (name spelling, GitHub handle) must match the invariants in `AGENTS.md`. The next scheduled run closes the issue.

## Limitations

- The audit does not cover every field `--sync` writes. It checks SimpliRoute bullets, the skills matrix, flagship projects and missing translation keys. Other experience entries, education and the summaries are rebuilt by `--sync` but not compared.
- Flagship projects are a fixed slug list inside `audit()`; a new flagship project in projects-hub needs that list updated.
