from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlmodel import Session, select
from typing import List, Optional, Dict, Any
from pathlib import Path
from collections import defaultdict
from datetime import datetime
import shutil

from app.config import INPUTS_DIR, MASTER_EXCEL_PATH
from app.db.database import get_session
from app.db.models import Transaction, CardMapping, CategoryRule, IngestionLog
from app.ingestion.scanner import scan_and_ingest_inputs
from app.export.excel_generator import generate_master_excel, CARD_DISPLAY_NAMES

router = APIRouter(prefix="/api")

@router.post("/scan")
def trigger_scan():
    """Triggers scan on input directory."""
    results = scan_and_ingest_inputs()
    excel_path = generate_master_excel()
    return {
        "status": "success",
        "ingestion_results": results,
        "excel_path": excel_path
    }

@router.post("/upload")
def upload_statement(file: UploadFile = File(...)):
    """Allows web UI file upload directly into input folder."""
    INPUTS_DIR.mkdir(parents=True, exist_ok=True)
    target_path = INPUTS_DIR / file.filename
    with open(target_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    results = scan_and_ingest_inputs()
    generate_master_excel()
    return {"status": "uploaded", "filename": file.filename, "ingestion_results": results}

@router.get("/transactions")
def list_transactions(
    month: Optional[str] = None,
    user: Optional[str] = None,
    category: Optional[str] = None,
    session: Session = Depends(get_session)
):
    query = select(Transaction)
    if user:
        query = query.where(Transaction.user_name == user)
    if category:
        query = query.where(Transaction.category == category)
    
    txs = session.exec(query.order_by(Transaction.transaction_date.desc())).all()
    card_mappings = {m.card_last_4: m.display_name for m in session.exec(select(CardMapping)).all()}

    results = []
    for t in txs:
        if month and t.transaction_date.strftime("%Y-%m") != month:
            continue
        card_label = CARD_DISPLAY_NAMES.get(t.card_last_4, card_mappings.get(t.card_last_4, f"Card {t.card_last_4}"))
        results.append({
            "id": t.id,
            "hash_key": t.hash_key,
            "source_file": t.source_file,
            "institution": t.institution,
            "card_last_4": t.card_last_4,
            "card_name": card_label,
            "user_name": t.user_name or "Unassigned",
            "transaction_date": t.transaction_date.strftime("%d/%m/%y"),
            "charge_date": t.charge_date.strftime("01/%m/%y") if t.charge_date else t.transaction_date.strftime("01/%m/%y"),
            "vendor": t.vendor,
            "charged_amount": t.charged_amount,
            "charged_currency": t.charged_currency,
            "category": t.category or "Uncategorized",
            "subcategory": t.subcategory or "",
            "current_installment": t.current_installment,
            "total_installments": t.total_installments
        })

    return results

@router.get("/summary")
def get_summary_metrics(session: Session = Depends(get_session)):
    txs = session.exec(select(Transaction)).all()
    card_mappings = {m.card_last_4: m for m in session.exec(select(CardMapping)).all()}
    
    total_spent = sum(t.charged_amount for t in txs)
    total_tx_count = len(txs)
    
    user_totals = {}
    category_totals = {}
    month_totals = {}
    card_breakdown = {}
    
    for t in txs:
        m = (t.charge_date or t.transaction_date).strftime("01/%m/%y")
        u = t.user_name or "Unassigned"
        c_num = t.card_last_4
        c_label = CARD_DISPLAY_NAMES.get(c_num, card_mappings[c_num].display_name if c_num in card_mappings else f"Card {c_num}")
        
        user_totals[u] = user_totals.get(u, 0.0) + t.charged_amount
        category_totals[t.category or "Uncategorized"] = category_totals.get(t.category or "Uncategorized", 0.0) + t.charged_amount
        month_totals[m] = month_totals.get(m, 0.0) + t.charged_amount
        
        if c_num not in card_breakdown:
            card_breakdown[c_num] = {
                "card_last_4": c_num,
                "card_name": c_label,
                "user_name": u,
                "institution": t.institution,
                "total_spent_ils": 0.0,
                "transaction_count": 0
            }
        card_breakdown[c_num]["total_spent_ils"] += t.charged_amount
        card_breakdown[c_num]["transaction_count"] += 1

    for c_info in card_breakdown.values():
        c_info["total_spent_ils"] = round(c_info["total_spent_ils"], 2)

    logs = session.exec(select(IngestionLog).order_by(IngestionLog.processed_at.desc()).limit(10)).all()
    
    return {
        "total_spent_ils": round(total_spent, 2),
        "total_transactions": total_tx_count,
        "user_totals": user_totals,
        "category_totals": category_totals,
        "monthly_totals": month_totals,
        "cards_mapped_count": len(card_breakdown),
        "card_breakdown": list(card_breakdown.values()),
        "recent_logs": logs
    }

@router.get("/analytics")
def get_analytics_data(session: Session = Depends(get_session)):
    """Returns dataset for user requested charts:
    1. Overall Monthly Spending Trend (Line Chart)
    2. Category Breakdown comparing Past Two Months (Grouped Bar Chart)
    3. Monthly trend graph for EVERY single category (Interactive Category Selector)
    """
    txs = session.exec(select(Transaction)).all()
    
    monthly_trend = defaultdict(float)
    category_totals = defaultdict(float)
    category_by_month = defaultdict(lambda: defaultdict(float))

    for t in txs:
        m_label = (t.charge_date or t.transaction_date).strftime("%m/%y")
        cat = t.category or "Uncategorized"
        amt = t.charged_amount

        monthly_trend[m_label] += amt
        category_totals[cat] += amt
        category_by_month[cat][m_label] += amt

    sorted_months = sorted(monthly_trend.keys(), key=lambda x: datetime.strptime(x, "%m/%y") if "/" in x else x)

    # 1. Monthly Spending Trend Line Data
    monthly_trend_data = {
        "labels": sorted_months,
        "totals": [round(monthly_trend[m], 2) for m in sorted_months]
    }

    # 2. Category Breakdown for Past Two Months
    sorted_cats = [c[0] for c in sorted(category_totals.items(), key=lambda x: x[1], reverse=True)]
    past_two_months = sorted_months[-2:] if len(sorted_months) >= 2 else sorted_months
    m1_label = past_two_months[0] if len(past_two_months) >= 1 else ""
    m2_label = past_two_months[1] if len(past_two_months) >= 2 else ""

    category_past_two_months = {
        "labels": sorted_cats,
        "month_1_label": m1_label,
        "month_2_label": m2_label,
        "month_1_totals": [round(category_by_month[cat][m1_label], 2) for cat in sorted_cats],
        "month_2_totals": [round(category_by_month[cat][m2_label], 2) for cat in sorted_cats]
    }

    # 3. Monthly graph for EVERY single category
    all_categories_monthly = {}
    for cat in sorted_cats:
        all_categories_monthly[cat] = [round(category_by_month[cat][m], 2) for m in sorted_months]

    category_all_monthly_data = {
        "months": sorted_months,
        "categories": sorted_cats,
        "data_by_category": all_categories_monthly
    }

    return {
        "status": "success",
        "monthly_trend": monthly_trend_data,
        "category_past_two_months": category_past_two_months,
        "category_all_monthly": category_all_monthly_data
    }

@router.get("/cards")
def list_cards(session: Session = Depends(get_session)):
    cards = session.exec(select(CardMapping)).all()
    res = []
    for c in cards:
        c_label = CARD_DISPLAY_NAMES.get(c.card_last_4, c.display_name)
        res.append({
            "id": c.id,
            "card_last_4": c.card_last_4,
            "raw_last_4": c.card_last_4,
            "institution": c.institution,
            "owner_name": c.owner_name,
            "display_name": c_label
        })
    return res

@router.post("/cards")
def create_or_update_card(card: CardMapping, session: Session = Depends(get_session)):
    existing = session.exec(select(CardMapping).where(CardMapping.card_last_4 == card.card_last_4)).first()
    if existing:
        existing.owner_name = card.owner_name
        existing.display_name = card.display_name
        existing.institution = card.institution
        session.add(existing)
    else:
        session.add(card)
    session.commit()
    
    txs = session.exec(select(Transaction).where(Transaction.card_last_4 == card.card_last_4)).all()
    for t in txs:
        t.user_name = card.owner_name
        session.add(t)
    session.commit()
    generate_master_excel()
    return {"status": "saved", "card": card}

from app.export.vendor_list import generate_vendor_category_file, apply_vendor_category_file
from app.core.projections import calculate_monthly_projections

@router.get("/projections")
def get_projections():
    """Returns 12-month forward budget projections."""
    matrix = calculate_monthly_projections(12)
    return {"status": "success", "projections": matrix}

@router.get("/projections/detail")
def get_projections_detail():
    """Returns itemized 12-month forward cash flow and recurring commitment forecast DTO."""
    forecast = calculate_monthly_projections(12)
    fixed_baseline = forecast[0]["fixed_recurring_baseline_ils"] if forecast else 0.0
    return {
        "status": "success",
        "rolling_baseline_months": 3,
        "fixed_recurring_baseline_monthly_ils": fixed_baseline,
        "forecast": forecast
    }

from urllib.parse import unquote

@router.get("/category/detail")
def get_category_detail(category: str, month: Optional[str] = None, session: Session = Depends(get_session)):
    """Returns detailed subcategory breakdown, top vendors, and transactions for a specific category."""
    cat_decoded = unquote(category)
    query = select(Transaction).where(Transaction.category == cat_decoded)
    txs = session.exec(query.order_by(Transaction.transaction_date.desc())).all()
    card_mappings = {m.card_last_4: m.display_name for m in session.exec(select(CardMapping)).all()}

    filtered_txs = []
    subcat_totals = defaultdict(float)
    subcat_counts = defaultdict(int)
    vendor_totals = defaultdict(float)
    vendor_counts = defaultdict(int)
    total_spent = 0.0

    for t in txs:
        m_label = (t.charge_date or t.transaction_date).strftime("%m/%y")
        if month and month != "all" and m_label != month:
            continue

        amt = t.charged_amount
        total_spent += amt
        sub = t.subcategory or "General"
        v = t.vendor

        subcat_totals[sub] += amt
        subcat_counts[sub] += 1
        vendor_totals[v] += amt
        vendor_counts[v] += 1

        card_label = CARD_DISPLAY_NAMES.get(t.card_last_4, card_mappings.get(t.card_last_4, f"Card {t.card_last_4}"))
        filtered_txs.append({
            "id": t.id,
            "transaction_date": t.transaction_date.strftime("%d/%m/%y"),
            "charge_date": (t.charge_date or t.transaction_date).strftime("01/%m/%y"),
            "card_name": card_label,
            "card_last_4": t.card_last_4,
            "user_name": t.user_name or "Unassigned",
            "vendor": t.vendor,
            "subcategory": sub,
            "charged_amount": round(amt, 2),
            "installment": f"{t.current_installment}/{t.total_installments}" if t.total_installments > 1 else "1/1"
        })

    sorted_subcats = sorted(subcat_totals.items(), key=lambda x: x[1], reverse=True)
    subcategories_list = [
        {"subcategory": s[0], "total_ils": round(s[1], 2), "count": subcat_counts[s[0]]}
        for s in sorted_subcats
    ]

    sorted_vendors = sorted(vendor_totals.items(), key=lambda x: x[1], reverse=True)[:10]
    top_vendors_list = [
        {"vendor": v[0], "total_ils": round(v[1], 2), "count": vendor_counts[v[0]]}
        for v in sorted_vendors
    ]

    return {
        "status": "success",
        "category": cat_decoded,
        "selected_month": month or "all",
        "total_spent_ils": round(total_spent, 2),
        "transaction_count": len(filtered_txs),
        "subcategories": subcategories_list,
        "top_vendors": top_vendors_list,
        "transactions": filtered_txs
    }

@router.get("/export")
def export_excel():
    path = generate_master_excel()
    return {"status": "exported", "path": path}

@router.get("/vendors/export")
def export_vendor_list():
    path = generate_vendor_category_file()
    return {"status": "exported", "path": path}

@router.get("/subcategories/audit")
def get_subcategory_audit():
    """Audits Vendor_Category_Mapping.xlsx to notify user of vendors missing subcategories."""
    from app.export.vendor_list import get_active_mapping_path
    import pandas as pd

    mapping_path = get_active_mapping_path()
    if not mapping_path.exists():
        return {"status": "error", "message": "Mapping file not found."}

    df = pd.read_excel(mapping_path)
    if "Vendor Name" not in df.columns:
        return {"status": "error", "message": "Invalid schema."}

    missing_df = df[df["Subcategory"].isna() | (df["Subcategory"].astype(str).str.strip() == "") | (df["Subcategory"] == "General")]
    
    missing_list = []
    for idx, row in missing_df.iterrows():
        missing_list.append({
            "vendor_name": str(row.get("Vendor Name", "")),
            "category": str(row.get("Category", "Uncategorized")),
            "total_spent_ils": round(float(row.get("Total Spent (ILS)", 0.0)), 2),
            "transaction_count": int(row.get("Transaction Count", 0))
        })

    missing_list.sort(key=lambda x: x["total_spent_ils"], reverse=True)

    return {
        "status": "success",
        "mapping_file_path": str(mapping_path),
        "total_vendors": len(df),
        "missing_subcategory_count": len(missing_df),
        "missing_vendors": missing_list
    }
