# Implementation Specification Plan: Separated Development & Dropbox Viewing App Workflow

**Architectural Role**: Lead Principal Systems Architect (Planner)  
**Status**: APPROVED via `/grill-me` & Hardened by Chaos Monkey  
**Target Specification File**: `/.plans/dropbox_workflow.md`

---

## Architectural Overview

This specification establishes a clean, decoupled **Development vs Shared Viewing Architecture** for the Home Budget Management System.

### Operational Roles & File Locations:

1. **Development Workspace (Your Computer)**:
   - **Path**: `c:\Users\rmelamed\Projects\home-budget-management`
   - **Role**: Source code modifications, feature enhancements, category rule updates, and running PyInstaller build/deploy commands.
   - **Working Vendor File**: `c:\Users\rmelamed\Projects\home-budget-management\data\inputs\Vendor_Category_Mapping.xlsx`

2. **Shared Dropbox Viewing Location (Dropbox)**:
   - **Root Path**: `C:\Users\rmelamed\Dropbox\Home Shared\Home Finance\`
   - **App Location**: `C:\Users\rmelamed\Dropbox\Home Shared\Home Finance\HomeBudgetApp\`
   - **Raw Credit Card Drop Location**: `C:\Users\rmelamed\Dropbox\Home Shared\Home Finance\Credit Cards\`
   - **Role**: Read raw monthly credit card files dropped by Rani & Yael, view dashboard analytics & 12-month projections, and generate `Master_Budget.xlsx`.

3. **One-Click Build & Deploy Pipeline (`build_exe.py`)**:
   - Compiles `dist/HomeBudgetManager/HomeBudgetManager.exe`.
   - Copies `HomeBudgetManager.exe`, `_internal`, and latest `Vendor_Category_Mapping.xlsx` to `C:\Users\rmelamed\Dropbox\Home Shared\Home Finance\HomeBudgetApp\`.

---

## Immutable Data Contracts

### 1. Fallback Input Path Chain (`app/config.py`)
```python
DROPBOX_CREDIT_CARDS_DIR = Path(r"C:\Users\rmelamed\Dropbox\Home Shared\Home Finance\Credit Cards")

def get_inputs_dir() -> Path:
    """Returns Dropbox Credit Cards folder if exists, else relative ./data/inputs."""
    if DROPBOX_CREDIT_CARDS_DIR.exists():
        return DROPBOX_CREDIT_CARDS_DIR
    return BASE_DIR / "data" / "inputs"

INPUTS_DIR = get_inputs_dir()
```

---

## 🐒 Failure Modes & Mitigation (Chaos Monkey Threat Modeling)

1. **Failure Mode 1: Executable File Lock during Deployment**
   - *Threat*: If `HomeBudgetManager.exe` is currently running on your computer or Yael's computer when `build_exe.py` runs, `shutil.copy2` fails with `PermissionError`.
   - *Mitigation*: Catch `PermissionError` during copy, print a clear warning instructing user to close `HomeBudgetManager.exe`, and continue deploying data files.

2. **Failure Mode 2: Missing Dropbox Path on Non-Host Computer**
   - *Threat*: If Yael's computer has Dropbox synced to a different user folder path (e.g. `C:\Users\yael\Dropbox\...`), hardcoded `C:\Users\rmelamed\...` fails.
   - *Mitigation*: Dynamically check `Path.home() / "Dropbox"` if hardcoded path does not exist, with fallback to `./data/inputs`.

---

## Affected Files

- `app/config.py` — Prioritize `C:\Users\rmelamed\Dropbox\Home Shared\Home Finance\Credit Cards` as primary `INPUTS_DIR` with dynamic user home fallback.
- `build_exe.py` — Automated build and deployment script publishing to Dropbox `HomeBudgetApp`.
- `tests/test_parsers.py` — Add unit test verifying input path fallback logic.

---

## Step-by-Step Micro-Tasks (for Builder Agent)

1. **Micro-Task 1 (Config)**: Update `app/config.py` so `INPUTS_DIR` defaults to `C:\Users\rmelamed\Dropbox\Home Shared\Home Finance\Credit Cards`.
2. **Micro-Task 2 (Build Script)**: Update `build_exe.py` to compile the app and automatically deploy binaries + `Vendor_Category_Mapping.xlsx` to `C:\Users\rmelamed\Dropbox\Home Shared\Home Finance\HomeBudgetApp`.
3. **Micro-Task 3 (Verification)**: Run `python build_exe.py` and pytest unit test suite.

---

## Verification Criteria

### Automated Tests
- `python -m pytest` executes 100% clean.
- Verify `app.config.INPUTS_DIR` resolves to `C:\Users\rmelamed\Dropbox\Home Shared\Home Finance\Credit Cards`.

### Manual Verification
- Execute `python build_exe.py`.
- Verify `C:\Users\rmelamed\Dropbox\Home Shared\Home Finance\HomeBudgetApp\HomeBudgetManager.exe` runs and reads credit card Excel files directly from `C:\Users\rmelamed\Dropbox\Home Shared\Home Finance\Credit Cards`.

---

## Context Pruning (Permitted Files for Builder)

The Builder is strictly limited to reading ONLY these 2 files:
1. `app/config.py`
2. `build_exe.py`
