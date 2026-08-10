# Home Budget & Expense Management System - Architectural Specification

## Architectural Overview
This system is a 100% offline, privacy-first local financial management application.
It processes Israeli credit card (Max, Isracard, Cal) and bank account (Hapoalim, Leumi, Mizrahi, etc.) statement exports (Excel/CSV) stored in a designated local folder (`C:\Budget\Inputs` or `./data/inputs`), normalizes transaction data into a local SQLite database (`./data/budget.db`), and exposes both an interactive Web Dashboard UI (`http://localhost:8000`) and structured Excel reports (`Master_Budget.xlsx`).

### Core Subsystems & Boundaries
1. **Local Folder Scanner & Ingestion Pipeline (`app/ingestion/`)**:
   - Watches/scans designated local directory for raw `.xlsx`, `.xls`, and `.csv` files.
   - Detects statement type (Max, Isracard, Cal, Bank) using header signatures and sheet structure.
   - Extracts account holder, last 4 digits, billing date, currency, raw transactions, and installment metadata.
2. **Normalizer & Deduplication Engine (`app/core/dedup.py`, `app/core/normalizer.py`)**:
   - Hashes transaction attributes (`transaction_date`, `amount`, `vendor`, `card_last_4`, `current_installment`) to ensure idempotent ingestion.
   - Handles multi-currency amounts (original transaction currency vs charged currency ILS/USD/EUR).
   - Extracts installment details (e.g. payment 2 of 5, total installments, remaining balance).
3. **Category & Mapping Engine (`app/core/categories.py`)**:
   - Rule-based regex matching for automatic category assignment (e.g. Supermarket, Utilities, Dining, Subscriptions).
   - Maps credit cards and bank accounts to specific family members via dynamic user rules.
4. **Local Database & Storage (`app/db/`)**:
   - SQLite database (`budget.db`) managed with SQLModel / SQLAlchemy & Alembic.
   - 100% offline: zero cloud endpoints or remote telemetry calls.
5. **Excel Exporter (`app/export/excel_generator.py`)**:
   - Generates and updates `Master_Budget.xlsx` using `openpyxl`.
   - Worksheets: `All Transactions`, `Monthly Summary`, `Category Breakdown`, `Installments Schedule`, `Accounts & Cards`.
6. **Local Web UI & REST API (`app/main.py`, `frontend/`)**:
   - FastAPI server serving local REST APIs and static React/Vite dashboard assets.
   - Displays real-time ingestion logs, interactive transaction editor, category management, cards/users mapping, and monthly budget projection overview.

---

## Immutable Data Contracts

### 1. Ingested Standard Transaction Interface (Python / Pydantic)
```python
from pydantic import BaseModel
from datetime import date
from typing import Optional

class RawTransaction(BaseModel):
    source_file: str
    card_or_account_id: str  # e.g., "MAX_1234"
    institution: str  # "MAX", "ISRACARD", "CAL", "LEUMI", "HAPOALIM"
    user_name: Optional[str] = None
    transaction_date: date
    charge_date: Optional[date] = None
    vendor: str
    original_amount: float
    original_currency: str  # "ILS", "USD", "EUR"
    charged_amount: float
    charged_currency: str = "ILS"
    category: Optional[str] = "Uncategorized"
    current_installment: int = 1
    total_installments: int = 1
    notes: Optional[str] = None
    hash_key: str  # SHA256 unique fingerprint
```

### 2. Family Card Mapping Contract
```json
{
  "mappings": [
    {
      "card_last_4": "1234",
      "institution": "MAX",
      "owner_name": "Dan",
      "display_name": "Dan Max Executive"
    },
    {
      "card_last_4": "5678",
      "institution": "ISRACARD",
      "owner_name": "Sarah",
      "display_name": "Sarah Corporate"
    }
  ]
}
```

### 3. Category Rule Specification
```json
{
  "rules": [
    { "pattern": "(?i)shufersal|rami levy|victory|yohananof", "category": "Groceries" },
    { "pattern": "(?i)super-pharm|be", "category": "Health & Pharmacy" },
    { "pattern": "(?i)paz|sonol|delek", "category": "Transportation & Fuel" }
  ]
}
```

---

## Affected Files
The codebase will be initialized with the following structure:

- `pyproject.toml` [NEW] - Dependencies (`fastapi`, `uvicorn`, `sqlmodel`, `openpyxl`, `pandas`, `pydantic`, `pytest`, `ruff`)
- `app/__init__.py` [NEW]
- `app/main.py` [NEW] - FastAPI application launcher & local server routes
- `app/config.py` [NEW] - Paths (`C:\Budget\Inputs`, `./data/budget.db`, `./data/Master_Budget.xlsx`)
- `app/db/database.py` [NEW] - SQLite connection & session management
- `app/db/models.py` [NEW] - SQLModel schema for Transactions, Cards, Categories, and MonthlyBudgets
- `app/ingestion/scanner.py` [NEW] - Folder scanner for newly dropped files
- `app/ingestion/parsers/base.py` [NEW] - Base parser interface
- `app/ingestion/parsers/israeli_cards.py` [NEW] - Parsers for Max, Isracard, Cal, Bank Hapoalim, Bank Leumi Excel/CSV files
- `app/core/dedup.py` [NEW] - Hash generation & transaction deduplication engine
- `app/core/categories.py` [NEW] - Categorization engine & custom user rule matcher
- `app/core/installments.py` [NEW] - Installments schedule generator
- `app/export/excel_generator.py` [NEW] - Openpyxl-based multi-sheet Excel generator
- `app/api/routes.py` [NEW] - REST endpoints for UI dashboard & triggering scans
- `frontend/index.html` [NEW] - Dashboard shell
- `frontend/src/App.jsx` [NEW] - Web UI components (Dashboard, Transactions, Scanning, Categories, Settings)
- `tests/test_parsers.py` [NEW] - Unit tests for Israeli bank/credit card formats
- `tests/test_dedup.py` [NEW] - Unit tests for duplicate handling
- `tests/test_excel.py` [NEW] - Tests for Master Excel generation

---

## Step-by-Step Micro-Tasks

1. **Environment Setup & Database Layer**:
   - Initialize `pyproject.toml` with `uv`.
   - Define SQLModel classes in `app/db/models.py` (Transaction, CardMapping, CategoryRule, BudgetProjection).
   - Implement `app/db/database.py` SQLite engine initialization.

2. **Ingestion & Parsers Engine**:
   - Build `app/ingestion/parsers/israeli_cards.py` to auto-detect header layouts of Max, Isracard, Cal, Hapoalim, Leumi Excel/CSV statements.
   - Implement parsing logic for dates (Hebrew/English date formats), vendor names, ILS/USD/EUR amounts, and installment strings (e.g., "02/05" or payment counts).

3. **Deduplication, Normalization & Categorization**:
   - Implement hash creation in `app/core/dedup.py` using `sha256(date + amount + vendor + card_id + installment)`.
   - Implement rule-based categorization in `app/core/categories.py`.

4. **Excel Generator**:
   - Build `app/export/excel_generator.py` to compile database records into `Master_Budget.xlsx`.
   - Format worksheets with clear color accents, totals, and monthly breakdowns.

5. **FastAPI Local Backend & Folder Scanner**:
   - Build `app/ingestion/scanner.py` to scan `C:\Budget\Inputs` (or `./data/inputs`).
   - Implement API endpoints in `app/api/routes.py` for scan trigger, list transactions, update category rules, map card owners, and download/export Excel.

6. **Modern Web UI Dashboard**:
   - Build Vite/React or clean SPA frontend in `frontend/` featuring:
     - **Ingestion Status**: Shows scanned files and imported count.
     - **Transactions Table**: Search, filter by card/user/month/category, edit category.
     - **Monthly Overview**: Summary of income/expenses, multi-user credit card breakdown.
     - **Budget & Projections**: Forecast baseline based on fixed commitments + active installment schedule.
     - **Settings & Mappings**: Card owner assignment and category rule editor.

7. **Verification & Tests**:
   - Add unit tests for statement parsers, hash deduplication, installment projections, and Excel exporting.

---

## Verification Criteria
1. **Parser Test**: `pytest tests/test_parsers.py` passes for mock Max, Isracard, Cal, and Bank Excel statements.
2. **Deduplication Test**: Re-importing the exact same Excel file multiple times results in 0 duplicate records inserted into SQLite.
3. **Excel Export Test**: Running `python -m app.export.excel_generator` outputs `Master_Budget.xlsx` with intact headers, formulas, and formatted transaction rows.
4. **UI Verification**: Accessing `http://localhost:8000` loads the modern dashboard, displays transaction summaries per card user, and allows filtering by month/category.
5. **Privacy Audit**: 0 outbound network calls made; all data remains in local database & Excel files.

---

## Context Pruning
The Builder agent is permitted to read only these 3 core files during initial setup:
1. `app/db/models.py`
2. `app/ingestion/parsers/israeli_cards.py`
3. `app/export/excel_generator.py`
