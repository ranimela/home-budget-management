# Project Conventions (copy from master, edit per project)
Agents read this before planning and building. Anything decided here is not re-asked in /grill-me.
Lines marked EDIT are placeholders, not decisions. Fill them in yourself or let the Planner ask.
Where this file differs from a global file such as ~/.gemini/GEMINI.md, this file wins for this project.

## Stack
- Language / runtime: Python 3.10+ (FastAPI + Uvicorn backend)
- UI (if any): Local Single-Page Web UI (`frontend/index.html`) using Vanilla JS, HTML/CSS, and bundled Chart.js (`frontend/chart.min.js`)
- Data store: SQLite database (`budget.db`) via SQLModel + Excel/CSV statement inputs (`pandas`, `openpyxl`, `xlrd`) and strict read-only `Vendor_Category_Mapping.xlsx`
- Package manager: `uv` with `pyproject.toml` and `uv.lock`. The README setup steps follow this.
- Dependencies: standard library and existing `pyproject.toml` packages first; ask before adding any new package.

## Layout
- `app/` backend application code (`api/`, `core/`, `db/`, `export/`, `ingestion/`); `frontend/` static web UI; `tests/` pytest suite; `.plans/` specs and status files.

## Config & secrets
- Settings from environment variables or a `.env` file that is git-ignored. Never hardcode keys. Never print or log them.

## Logging & errors
- stdlib `logging` to a file with timestamp, level, traceback. No silent `except: pass`.
- Fail loudly with a clear message when input data is missing or malformed.

## Windows & Packaging
- `pathlib` for all paths; no hardcoded absolute paths; PowerShell commands; quote paths with spaces.
- Never compile or export the standalone `.exe` (`build_exe.py` / `deploy_to_dropbox.py`) unless explicitly requested by the user.

## Data safety
- Tests use fixtures or temp copies. Never write to or delete the user's real data files in tests.
- `Vendor_Category_Mapping.xlsx` is strictly READ-ONLY to the application and must never be overwritten or modified by code.

## Done means
- Validator PASS, README updated if CLI args / env vars / setup changed, no secrets or private financial statements/databases in the diff.
