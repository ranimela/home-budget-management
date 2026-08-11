# Implementation Specification Plan: Interactive Category Drill-Down Modal & Subcategory Analysis

**Architectural Role**: Lead Principal Systems Architect (Planner)  
**Status**: APPROVED via `/grill-me` & Hardened by Chaos Monkey  
**Target Specification File**: `/.plans/category_drilldown.md`

---

## Architectural Overview

This feature introduces an **Interactive Category Drill-Down Modal & Deep-Dive Analytics Engine** into the Home Budget Management application.

### Core Interaction Flow:
1. **Interactive Trigger**:
   - Clicking any category element (bar in Past Two Months chart, mini-chart header, or category tag) triggers an expanding glassmorphism modal on `http://localhost:8000`.
2. **Category Deep-Dive Modal**:
   - **Header**: Category name, active month filter selector (`All Months`, `01/26`, `02/26`, ..., `08/26`), total category ILS spend, and transaction count.
   - **Subcategory & Vendor Breakdown**: Ranked breakdown of subcategories (if mapped) and top vendors within that category.
   - **Filtered Transaction Table**: Searchable, paginated table displaying all transactions in the selected category.
3. **Data Fetching & Performance**:
   - Add a `/api/category/detail` endpoint in FastAPI returning pre-aggregated category stats, top vendors, and transaction lists.

---

## Immutable Data Contracts

### 1. API Endpoint Contract (`GET /api/category/detail`)
- **Query Parameters**: `category` (required string), `month` (optional string e.g. `08/26` or `2026-08`)
- **Response Payload**:
```json
{
  "status": "success",
  "category": "אוכל",
  "selected_month": "08/26",
  "total_spent_ils": 4520.50,
  "transaction_count": 42,
  "subcategories": [
    { "subcategory": "סופרמרקט", "total_ils": 3200.00, "count": 28 },
    { "subcategory": "ירקות ופירות", "total_ils": 1320.50, "count": 14 }
  ],
  "top_vendors": [
    { "vendor": "שופרסל", "total_ils": 2100.00, "count": 15 },
    { "vendor": "חצי חינם", "total_ils": 1100.00, "count": 13 }
  ],
  "transactions": [
    {
      "id": 101,
      "transaction_date": "15/08/26",
      "charge_date": "01/09/26",
      "card_name": "Rani CAL",
      "card_last_4": "9380",
      "vendor": "שופרסל שלי",
      "charged_amount": 350.20,
      "installment": "1/1"
    }
  ]
}
```

---

## 🐒 Failure Modes & Mitigation (Chaos Monkey Threat Modeling)

1. **Failure Mode 1: Special Character & Hebrew URL Encoding**
   - *Threat*: Category strings containing spaces or Hebrew characters (e.g. `אוכל`, `הוצאות חו"ל - נפולי`) break HTTP query string parsing (`404` or `422 Unprocessable Entity`).
   - *Mitigation*: Apply `encodeURIComponent()` on client request URLs and `urllib.parse.unquote()` on FastAPI parameters.

2. **Failure Mode 2: Empty Subcategory Mapping**
   - *Threat*: Categories without explicit subcategories return `null` or cause JS `.map()` exceptions in Modal rendering.
   - *Mitigation*: Fall back to empty array `[]` or `"General"` subcategory label.

3. **Failure Mode 3: Modal Keyboard Accessibility (`Esc` key & Background Backdrop Click)**
   - *Threat*: Modal traps user focus or prevents closing when clicking outside or pressing `Escape`.
   - *Mitigation*: Add explicit `Escape` key listener and backdrop overlay click dismiss logic.

---

## Affected Files

- `app/api/routes.py` — Add `/api/category/detail` endpoint.
- `frontend/index.html` — Add Category Drill-Down Modal HTML structure, dark-mode CSS styles, and JavaScript click handlers.
- `tests/test_parsers.py` — Add unit test for `/api/category/detail` API contract.

---

## Step-by-Step Micro-Tasks (for Builder Agent)

1. **Micro-Task 1 (API)**: Implement `GET /api/category/detail` endpoint in `app/api/routes.py`.
2. **Micro-Task 2 (Modal HTML/CSS)**: Add glassmorphism Modal markup and styles in `frontend/index.html`.
3. **Micro-Task 3 (Interactive JS Handlers)**: Wire click events on Category graphs/mini-charts in `frontend/index.html` to fetch `/api/category/detail` and open the Modal.
4. **Micro-Task 4 (Verification)**: Add pytest unit test in `tests/test_parsers.py`.

---

## Verification Criteria

### Automated Tests
- `python -m pytest` executes 100% clean.
- Verify `/api/category/detail` contract returns correct `total_spent_ils`, `top_vendors`, and `transactions` list.

### Manual Verification
- Click any Category graph on `http://localhost:8000` to verify the Modal opens smoothly.
- Verify month selector inside Modal filters data correctly.
- Verify vendor breakdown and transaction search work inside the Modal.

---

## Context Pruning (Permitted Files for Builder)

The Builder is strictly limited to reading ONLY these 2 files:
1. `app/api/routes.py`
2. `frontend/index.html`
