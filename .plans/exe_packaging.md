# Implementation Specification Plan: Standalone Executable Packaging & Shared Dropbox Integration

**Architectural Role**: Lead Principal Systems Architect (Planner)  
**Status**: APPROVED via `/grill-me` & Hardened by Chaos Monkey  
**Target Specification File**: `/.plans/exe_packaging.md`

---

## Architectural Overview

This feature transforms the Home Budget Management system into a **Self-Contained Standalone Executable (`HomeBudgetManager.exe`)** designed to run locally on separate computers from within a shared Dropbox directory.

### Key Architectural Decisions:
1. **Fixed Relative Dropbox Root Context**:
   - The `.exe` expects to be placed and executed directly inside the shared Dropbox folder (or root workspace directory).
   - Paths for `data/inputs/`, `data/outputs/Master_Budget.xlsx`, `data/budget.db`, and `Vendor_Category_Mapping.xlsx` resolve dynamically relative to `Path(__file__).parent` / `sys.executable`.
2. **Single Shared SQLite Database (`data/budget.db`)**:
   - Database operations use SQLite `journal_mode=WAL` (Write-Ahead Logging) and `timeout=30.0` seconds to handle Dropbox file synchronization gracefully across separate computers.
3. **PyInstaller Packaging Engine**:
   - Uses PyInstaller (`pyinstaller --onefile`) to bundle Python 3.14 runtime, FastAPI, Uvicorn, SQLModel, Pandas, OpenPyXL, and static frontend assets (`frontend/*`) into a single executable `HomeBudgetManager.exe`.
4. **Auto-Launch & Browser Entry Point**:
   - On double-clicking `HomeBudgetManager.exe`, an entry script `app/launcher.py`:
     1. Resolves workspace root directory.
     2. Verifies/creates `data/inputs` and `data/outputs` subdirectories.
     3. Starts Uvicorn server in a background thread on an available port (default `8000`).
     4. Opens `http://localhost:8000` automatically in the user's default browser.
     5. Displays a clean console banner with instructions and press `Ctrl+C` to stop.

---

## Immutable Data Contracts

### 1. Dynamic Path Resolution Module (`app/config.py`)
```python
import sys
from pathlib import Path

def get_base_dir() -> Path:
    """Returns executable parent folder if frozen, else project root folder."""
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent

BASE_DIR = get_base_dir()
DATA_DIR = BASE_DIR / "data"
INPUTS_DIR = DATA_DIR / "inputs"
OUTPUTS_DIR = DATA_DIR / "outputs"
DATABASE_PATH = DATA_DIR / "budget.db"
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"
MASTER_EXCEL_PATH = OUTPUTS_DIR / "Master_Budget.xlsx"
```

---

## 🐒 Failure Modes & Mitigation (Chaos Monkey Threat Modeling)

1. **Failure Mode 1: PyInstaller Missing Static Assets (`_MEIxxxx` Temp Directory)**
   - *Threat*: In a bundled `.exe`, `StaticFiles(directory="frontend")` fails with `DirectoryDoesNotExist` because PyInstaller unpacks static files to `sys._MEIPASS`.
   - *Mitigation*: Implement `get_bundle_dir()` to load static frontend files from `sys._MEIPASS / "frontend"` while writing data to `BASE_DIR / "data"`.

2. **Failure Mode 2: Port 8000 Busy Conflict**
   - *Threat*: If Uvicorn fails to bind to port 8000 because another application is using it, the `.exe` crashes silently.
   - *Mitigation*: Implement dynamic port fallback (try 8000, 8001, 8002, 8080) and launch browser to the active port.

3. **Failure Mode 3: SQLite Lock & Permission Error in Dropbox**
   - *Threat*: Concurrent access or Dropbox background syncing causes `sqlite3.OperationalError: database is locked`.
   - *Mitigation*: Enable `PRAGMA journal_mode=WAL;` and `PRAGMA busy_timeout=30000;` on engine creation.

---

## Affected Files

- `app/config.py` — Update path resolution to support frozen `.exe` and `_MEIPASS` asset contexts.
- `app/launcher.py` — Create desktop application entry-point for PyInstaller.
- `app.spec` — Create PyInstaller spec file bundling static assets & templates.
- `build_exe.py` — Create one-click build script to compile `HomeBudgetManager.exe`.
- `tests/test_parsers.py` — Add unit test verifying frozen path resolution logic.

---

## Step-by-Step Micro-Tasks (for Builder Agent)

1. **Micro-Task 1 (Config)**: Update `app/config.py` to handle `sys.frozen` path resolution dynamically relative to the executable location.
2. **Micro-Task 2 (Launcher)**: Create `app/launcher.py` with Uvicorn server thread, port auto-selection, browser auto-launch, and graceful shutdown handling.
3. **Micro-Task 3 (PyInstaller Spec)**: Create `app.spec` bundling `frontend/` static assets, `openpyxl`, and `sqlmodel` dependencies into a single `.exe`.
4. **Micro-Task 4 (Build & Test)**: Create `build_exe.py` build script, compile `dist/HomeBudgetManager.exe`, verify execution, and run unit test suite `pytest`.

---

## Verification Criteria

### Automated Tests
- `python -m pytest` executes 100% clean.
- Verify `app.config.BASE_DIR` resolves correctly in standard and frozen modes.

### Manual Verification
- Run `python build_exe.py` to generate `dist/HomeBudgetManager.exe`.
- Double-click `dist/HomeBudgetManager.exe` and verify:
  1. Local server starts without errors.
  2. Browser automatically opens to `http://localhost:8000`.
  3. Dashboard renders offline Chart.js graphs, 12-month projections, and transaction table.
  4. Vendor category re-reading and Master Excel generation work relative to `data/`.

---

## Context Pruning (Permitted Files for Builder)

The Builder is strictly limited to reading ONLY these 3 files:
1. `app/config.py`
2. `app/main.py`
3. `tests/test_parsers.py`
