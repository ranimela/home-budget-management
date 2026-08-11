# Implementation Specification Plan: 12-Month Forward Cash Flow & Commitment Forecasting

**Architectural Role**: Lead Principal Systems Architect (Planner)  
**Status**: APPROVED via `/grill-me` & Hardened by Chaos Monkey  
**Target Specification File**: `/.plans/cash_flow_projections.md`

---

## Architectural Overview

This feature introduces a **12-Month Forward Cash Flow & Recurring Commitment Forecasting Engine** into the Home Budget Management application. 

### Core State Machine & Projection Logic:
1. **Active Multi-Month Installment Pipeline**:
   - For every active transaction where `total_installments > 1` and `current_installment < total_installments`, project the remaining $(N = \text{total\_installments} - \text{current\_installment})$ payments into future consecutive billing months (`charge_date + 1 month`, `+2 months`, ...).
2. **Fixed Recurring Baseline**:
   - Compute a rolling 3-month average of recurring fixed categories (Insurance, Education, Utilities, Communications, Standing Orders).
3. **Combined Monthly Commitment Matrix**:
   - For each of the next 12 billing months (`M+1` to `M+12`), calculate:
     $$\text{Total Projected Commitment}_M = \text{Locked Installments}_M + \text{Recurring Fixed Baseline}_M$$
4. **Web UI Presentation**:
   - Render a dedicated **12-Month Cash Flow & Commitment Projection Matrix** on `http://localhost:8000` with interactive monthly drilldowns.

---

## Immutable Data Contracts

### 1. Ingestion / Projection Calculation Contract DTO
```json
{
  "projection_month": "2026-09-01",
  "display_month": "09/26",
  "locked_installments_ils": 3450.00,
  "active_installments_count": 8,
  "fixed_recurring_baseline_ils": 4200.00,
  "total_projected_commitment_ils": 7650.00,
  "installment_items": [
    {
      "vendor": "חן פיטנס",
      "card_last_4": "4591",
      "user_name": "Rani",
      "installment_payment": "4/10",
      "monthly_amount_ils": 70.00
    }
  ]
}
```

### 2. API Endpoint Contract
- **Endpoint**: `GET /api/projections/detail`
- **Response**:
```json
{
  "status": "success",
  "rolling_baseline_months": 3,
  "fixed_recurring_baseline_monthly_ils": 4200.00,
  "forecast": [
    /* List of 12 Projection Month DTOs */
  ]
}
```

---

## 🐒 Failure Modes & Mitigation (Chaos Monkey Threat Modeling)

1. **Failure Mode 1: Calendar Year Rollover (`Dec 2026 -> Jan 2027`)**
   - *Threat*: Naïve date incrementing `month + 1` crashes when rolling from month 12 to month 1.
   - *Mitigation*: Use relative calendar delta math (`relativedelta(months=+i)` or standard Python `date` replacement logic) to guarantee accurate year incrementing across year-end boundaries.

2. **Failure Mode 2: Final Installment Boundary (`Current == Total`)**
   - *Threat*: Including transactions where `current_installment == total_installments` projects phantom 13th payments into future months.
   - *Mitigation*: Enforce strict inequality `current_installment < total_installments`. Only remaining unpaid installments $(N = \text{total\_installments} - \text{current\_installment})$ generate future month DTO projections.

3. **Failure Mode 3: Empty / Cold-Start Database**
   - *Threat*: Invoking `/api/projections/detail` on an unpopulated SQLite database yields division-by-zero or `NoneType` exception when computing 3-month rolling averages.
   - *Mitigation*: Fall back gracefully to `0.00` baseline spend and empty forecast lists without throwing HTTP 500 errors.

4. **Failure Mode 4: Floating Point Rounding & Sum Discrepancies**
   - *Threat*: Summing multiple float installments introduces IEEE 754 precision drift (e.g. `₪70.00000000000001`).
   - *Mitigation*: Apply explicit `round(amount, 2)` at every DTO aggregation boundary.

---

## Affected Files

- `app/core/projections.py` — Engine calculating 12-month installment commitments and rolling fixed baseline.
- `app/api/routes.py` — Expose `/api/projections/detail` endpoint.
- `frontend/index.html` — Add 12-Month Projections interactive table & visualization on the Web Dashboard.
- `tests/test_parsers.py` — Unit tests for 12-month forward projection engine math.

---

## Step-by-Step Micro-Tasks (for Builder Agent)

1. **Micro-Task 1 (Engine)**: Enhance `app/core/projections.py` to calculate exact multi-month installment roll-forward and 3-month rolling baseline for fixed categories with Chaos Monkey mitigations.
2. **Micro-Task 2 (API)**: Implement `GET /api/projections/detail` in `app/api/routes.py`.
3. **Micro-Task 3 (Frontend UI)**: Update `frontend/index.html` with a dedicated **12-Month Forward Commitment Matrix** section featuring collapsible month breakdowns.
4. **Micro-Task 4 (Verification)**: Add pytest test suite validation in `tests/test_parsers.py`.

---

## Verification Criteria

### Automated Tests
- `python -m pytest` executes 100% clean.
- Verify installment roll-forward math: a 10-installment item at payment 3/10 projects exactly 7 remaining monthly payments into `M+1` through `M+7`.
- Verify December to January year rollover math.

### Manual Verification
- Access `http://localhost:8000/api/projections/detail` and verify 12 consecutive future months.
- Verify web UI projection matrix displays locked installments, fixed recurring baseline, and combined total burn.

---

## Context Pruning (Permitted Files for Builder)

The Builder is strictly limited to reading ONLY these 3 files:
1. `app/core/projections.py`
2. `app/api/routes.py`
3. `frontend/index.html`
