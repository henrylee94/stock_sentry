# Project Structure Review – Stock Sentry (GEEWONI)

Analysis per project-structure-reviewer: repository scan, stack detection, issues, recommendations, and refactor plan. **No files were modified or moved.**

---

## 1. Summary (5 bullets)

- **Stack:** Python 3.12 monolith (Telegram bot + Streamlit backoffice + agents); `requirements.txt` present; no `pyproject.toml`.
- **Root clutter:** Several modules and data files at root (`telegram_bot.py`, `tradesniper.py`, `intent_detector.py`, `rules_engine.py`, `backtester.py`, `strategies.json`, `nasdaq_screener_*.csv`, `new_requirement.md`, `user_qna.md`, `geewoni_config.json`) — app entry and domain logic mixed with config and ad‑hoc docs.
- **Clear boundaries:** `core/`, `agents/`, `strategy_agents/`, `news/`, `ai_rules/`, `skills/`, `scripts/`, `docs/` exist and have clear roles; missing a single **app/entry** layer and a dedicated **config/data** location for generated and user CSVs/JSON.
- **Naming/boundary:** `backtester.py` (root) vs `agents/backtester_agent.py` (wrapper) can confuse; `strategy_agents` vs `agents` is intentional (strategy evaluators vs pipeline agents) but could be documented in README.
- **Tests / CI:** No `tests/` or `test/` directory and no test files found; no `.github/workflows` — add tests and optional CI in a later phase.

---

## 2. Stack Detection

| Marker | Detected stack |
|--------|----------------|
| `requirements.txt` | Python (no `pyproject.toml` or `setup.py`) |
| `streamlit`, `python-telegram-bot`, `openai`, `yfinance`, `pandas` | Monolith: Telegram bot + Streamlit dashboard + data/ML |
| No `Dockerfile` in scan, no `k8s/` | Deploy likely via Zeabur / single process |

**Architecture style:** Monolith — one repo, two runnables (`telegram_bot.py`, `tradesniper.py`), shared `core/`, `agents/`, `skills/`, `ai_rules/`.

---

## 3. Visual Comparison

### BEFORE (current structure, relevant portions)

```
stock_sentry/
├── .gitignore
├── README.md
├── requirements.txt
├── geewoni_config.json          # config at root
├── strategies.json              # runtime/generated at root
├── stock_aliases_override.json   # override config at root
├── nasdaq_screener_1770573113664.csv   # data at root
├── new_requirement.md           # planning doc at root
├── user_qna.md                  # planning/doc at root
├── telegram_bot.py              # entry
├── tradesniper.py               # entry
├── intent_detector.py
├── rules_engine.py
├── skillset_manager.py
├── strategy_orchestrator.py
├── backtester.py                # domain module at root
├── agents/
│   ├── __init__.py
│   ├── analyzer.py
│   ├── technical_analyst.py
│   ├── strategy_generator.py
│   ├── backtester_agent.py      # thin wrapper around backtester
│   ├── final_decision.py
│   └── tools.py
├── strategy_agents/
│   ├── __init__.py
│   └── base_agent.py
├── core/
│   ├── __init__.py
│   ├── config.py
│   ├── data_manager.py
│   └── rate_limiter.py
├── news/
│   ├── __init__.py
│   ├── news_scheduler.py
│   └── news_system.py
├── dashboard_components/
│   ├── __init__.py
│   └── charts.py
├── ai_rules/                    # markdown rules
├── skills/                      # JSON skills by category
├── scripts/
│   └── update_stock_list.py
└── docs/
    ├── Complete Integration guide.md   # spaces in name
    ├── Startup guide.md
    ├── FIXES_QUICK_REFERENCE.md
    ├── PHASE1_PROGRESS.md
    ├── SKILLS_LIBRARY.md
    └── tradesniper_guide.md
```

### AFTER (proposed structure)

```
stock_sentry/
├── .gitignore
├── README.md
├── requirements.txt
├── config/                          # consolidated config (optional)
│   ├── geewoni_config.json          # or keep at root and document
│   └── stock_aliases_override.json
├── data/                            # generated / large files (optional)
│   ├── strategies.json
│   └── nasdaq_screener_*.csv        # or keep at root if script expects it
├── docs/
│   ├── planning/                    # planning / Q&A
│   │   ├── new_requirement.md
│   │   └── user_qna.md
│   ├── complete_integration_guide.md
│   ├── startup_guide.md
│   ├── fixes_quick_reference.md
│   ├── phase1_progress.md
│   ├── skills_library.md
│   └── tradesniper_guide.md
├── src/                             # application code (optional)
│   ├── bot/
│   │   └── telegram_bot.py
│   ├── backoffice/
│   │   └── tradesniper.py
│   ├── agents/
│   ├── strategy_agents/
│   ├── core/
│   ├── news/
│   ├── dashboard_components/
│   ├── intent_detector.py
│   ├── rules_engine.py
│   ├── skillset_manager.py
│   ├── strategy_orchestrator.py
│   └── backtester.py
├── ai_rules/
├── skills/
└── scripts/
```

**Note:** The AFTER tree shows a **moderate** refactor (config + data + docs cleanup). A **minimal** refactor (recommended first) is in the Move/Rename table below — only root clutter and doc naming, no `src/` move.

---

## 4. Issues by Category

### Structure (clutter, duplicates, separation)

| Issue | Severity | Description |
|-------|----------|-------------|
| Root clutter | 🟡 Medium | Many files at root: two entry points, four domain/orchestration modules (`intent_detector`, `rules_engine`, `skillset_manager`, `strategy_orchestrator`, `backtester`), three JSON/CSV files, two markdown planning docs. Hard to see “where the app starts” vs “where domain lives.” |
| Config at root | 🟡 Medium | `geewoni_config.json`, `strategies.json`, `stock_aliases_override.json` live at root. `core/config.py` already centralizes paths — only path constants would need to change if moved. |
| Planning docs at root | 🟢 Low | `new_requirement.md` and `user_qna.md` are planning/Q&A; moving to `docs/planning/` (or `docs/`) would reduce root noise. |
| No `tests/` | 🟡 Medium | No test directory or test files; refactors and upgrades are harder to validate. |

### Naming (casing, vague names)

| Issue | Severity | Description |
|-------|----------|-------------|
| Doc filenames with spaces | 🟢 Low | `docs/Complete Integration guide.md`, `docs/Startup guide.md` use spaces; rest use snake_case or PascalCase. Inconsistent and awkward in shells. |
| `backtester.py` vs `backtester_agent.py` | 🟢 Low | Root `backtester.py` is the engine; `agents/backtester_agent.py` is a thin wrapper. Name is clear but placement (root vs under agents) can confuse; README can clarify. |

### Boundaries (utils, mixed concerns)

| Issue | Severity | Description |
|-------|----------|-------------|
| No single “app” folder | 🟢 Low | Entry points and main orchestration are at root. Grouping them under e.g. `app/` or `src/` would clarify boundaries but requires import path changes; optional. |
| `agents` vs `strategy_agents` | 🟢 Low | Intentional: `agents/` = pipeline (analyzer, technical, strategy pick, backtest wrapper, final decision); `strategy_agents/` = per-strategy evaluators. README or `docs/ARCHITECTURE.md` would help. |

### Tests

| Issue | Severity | Description |
|-------|----------|-------------|
| No tests | 🟡 Medium | No `tests/` or colocated test files; no test runner config. Adding `tests/` and a few smoke/unit tests would improve safety for refactors. |

### Config

| Issue | Severity | Description |
|-------|----------|-------------|
| Config spread | 🟡 Medium | `geewoni_config.json` and `stock_aliases_override.json` at root; `core/config.py` references `Path("geewoni_config.json")`. Consolidating under `config/` is optional and requires path updates. |
| Generated/runtime files | 🟢 Low | `strategies.json` and `stock_aliases.json` (gitignored) are generated/runtime; could live in `data/` or stay at root with README note. |

### Documentation

| Issue | Severity | Description |
|-------|----------|-------------|
| Scattered planning docs | 🟢 Low | `new_requirement.md` and `user_qna.md` at root; better in `docs/` or `docs/planning/`. |
| Doc filename consistency | 🟢 Low | Mix of spaces and snake_case in `docs/`; standardizing to snake_case improves consistency and scripting. |

---

## 5. Move/Rename Mapping

Minimal, safe moves (no `src/` restructure):

| Source | Destination | Action / note |
|--------|-------------|----------------|
| `new_requirement.md` | `docs/planning/new_requirement.md` | Move; reduces root clutter. |
| `user_qna.md` | `docs/planning/user_qna.md` | Move; same. |
| `docs/Complete Integration guide.md` | `docs/complete_integration_guide.md` | Rename; consistent snake_case. |
| `docs/Startup guide.md` | `docs/startup_guide.md` | Rename; same. |
| `docs/FIXES_QUICK_REFERENCE.md` | `docs/fixes_quick_reference.md` | Rename; lowercase for consistency. |
| `docs/PHASE1_PROGRESS.md` | `docs/phase1_progress.md` | Rename; same. |
| `docs/SKILLS_LIBRARY.md` | `docs/skills_library.md` | Rename; same. |

Optional (higher impact, more changes):

| Source | Destination | Action / note |
|--------|-------------|----------------|
| `geewoni_config.json` | `config/geewoni_config.json` | Move; update `core/config.py` `CONFIG_FILE` path. |
| `stock_aliases_override.json` | `config/stock_aliases_override.json` | Move; update `intent_detector.py` and `scripts/update_stock_list.py` paths. |
| `strategies.json` | `data/strategies.json` | Move; update `core/config.py` `STRATEGIES_FILE`. |

---

## 6. Prioritized Recommendations

### 🔴 High priority

- **Add a test layout and baseline:** Create `tests/` and add at least one smoke test (e.g. import main modules or run `intent_detector.resolve_symbol`) so refactors can be verified. No file moves required for this.

### 🟡 Medium priority

- **Reduce root clutter:** Move `new_requirement.md` and `user_qna.md` to `docs/planning/` (or `docs/`). Update any references (links in README, other docs).
- **Document architecture:** Add a short `docs/ARCHITECTURE.md` (or a README section) explaining: two entry points (`telegram_bot.py`, `tradesniper.py`), role of `agents/` vs `strategy_agents/`, and where config/data live.
- **Consolidate config paths (optional):** If you introduce `config/`, move `geewoni_config.json` and `stock_aliases_override.json` and update `core/config.py`, `intent_detector.py`, and `scripts/update_stock_list.py`; then document in README.

### 🟢 Low priority

- **Rename docs to snake_case:** Rename the listed `docs/` files to lowercase snake_case and fix any links (README, internal doc links).
- **Clarify backtester placement:** In README or ARCHITECTURE, state that `backtester.py` is the engine and `agents/backtester_agent.py` is the pipeline wrapper.

---

## 7. Phased Refactor Plan

### Phase 1: Preparation (no moves)

1. Create a branch for structure changes.
2. Ensure bot and backoffice run: `python telegram_bot.py` (Ctrl+C after start), `streamlit run tradesniper.py`.
3. Add `tests/` and one smoke test, e.g. `tests/test_imports.py` that imports `core`, `agents`, `intent_detector`, `resolve_symbol` and optionally calls `resolve_symbol("AAPL")`. Run: `python -m pytest tests/` or `python tests/test_imports.py`.
4. **Risks:** None if only adding tests.  
5. **Verification:** Imports and (if added) one resolve_symbol check pass.

### Phase 2: Docs only (low risk)

1. Create `docs/planning/` if you use it.
2. Move `new_requirement.md` and `user_qna.md` to `docs/planning/` (or `docs/`).
3. Search repo for links/references to `new_requirement.md` and `user_qna.md`; update paths.
4. **Risks:** Broken links in README or other docs.  
5. **Verification:** `grep -r "new_requirement\|user_qna" --include="*.md" .` and open moved files from new paths.

### Phase 3: Doc renames (low risk)

1. Rename files in `docs/` to snake_case (see table above). Use git mv to preserve history.
2. Update README and any cross-references in `docs/`.
3. **Risks:** Links or scripts that reference old filenames.  
4. **Verification:** `ls docs/`; run any doc build or link checker if you have one.

### Phase 4 (optional): Config consolidation

1. Create `config/` (and optionally `data/`).
2. Move JSON config files; update `core/config.py`, `intent_detector.py`, `scripts/update_stock_list.py`.
3. **Risks:** Runtime errors if paths are wrong or env/cwd-dependent.  
4. **Verification:** Run bot and backoffice; run `python scripts/update_stock_list.py`; confirm strategies and alias resolution work.

---

## 8. Verification Checklist

- [ ] `python telegram_bot.py` starts (no import/path errors).
- [ ] `streamlit run tradesniper.py` starts.
- [ ] `python scripts/update_stock_list.py` runs (with or without CSV).
- [ ] `python -m pytest tests/` or minimal test script passes (after adding tests).
- [ ] README and docs still point to correct paths after moves/renames.
- [ ] No new circular imports after any move.

---

## 9. Import Path Changes (if you introduce `src/`)

If you later move app code under `src/` (e.g. `src/bot/telegram_bot.py`, `src/backoffice/tradesniper.py`), imports would change as follows (only if you do this refactor):

| Current | After (example) |
|---------|------------------|
| `from core import ...` | Same if `src/` is on `PYTHONPATH` or run as `python -m src.bot.telegram_bot` |
| `from intent_detector import ...` | `from src.intent_detector import ...` (or keep at root and avoid `src/`) |
| `from agents import ...` | `from src.agents import ...` |

**Recommendation:** Do not introduce `src/` unless you need a clearer split for packaging or deployment; the current flat layout is acceptable for a monolith.

---

## 10. Migration Script (optional)

Optional script to perform Phase 2 + 3 (docs move and rename). Run from repo root after backup/branch.

```bash
#!/usr/bin/env bash
# Run from stock_sentry/
set -e
mkdir -p docs/planning
git mv new_requirement.md docs/planning/ 2>/dev/null || mv new_requirement.md docs/planning/
git mv user_qna.md docs/planning/ 2>/dev/null || mv user_qna.md docs/planning/
cd docs
for f in "Complete Integration guide.md" "Startup guide.md"; do
  [ -f "$f" ] && git mv "$f" "$(echo "$f" | tr ' ' '_' | tr 'A-Z' 'a-z')" 2>/dev/null || true
done
git mv FIXES_QUICK_REFERENCE.md fixes_quick_reference.md 2>/dev/null || true
git mv PHASE1_PROGRESS.md phase1_progress.md 2>/dev/null || true
git mv SKILLS_LIBRARY.md skills_library.md 2>/dev/null || true
# Fix "Complete_Integration_guide.md" -> "complete_integration_guide.md" if needed
```

Then update README and any links to the new paths and names.

---

**End of review.** No files were modified. Apply changes incrementally and re-run the verification checklist after each phase.
