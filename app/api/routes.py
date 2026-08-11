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
    """Returns dataset strictly for the 3 user-selected charts (Monthly Trend, Category Bar, Category MoM)."""
    txs = session.exec(select(Transaction)).all()
    
    monthly_trend = defaultdict(float)
    category_totals = defaultdict(float)
    category_mom = defaultdict(lambda: defaultdict(float))

    for t in txs:
        m_label = (t.charge_date or t.transaction_date).strftime("%m/%y")
        cat = t.category or "Uncategorized"
        amt = t.charged_amount

        # 1. Monthly Spending Trend
        monthly_trend[m_label] += amt
        
        # 2. Total Spend per Category
        category_totals[cat] += amt
        
        # 3. Category Spending Month-over-Month
        category_mom[m_label][cat] += amt

    sorted_months = sorted(monthly_trend.keys(), key=lambda x: datetime.strptime(x, "%m/%y") if "/" in x else x)

    # 1. Monthly Spending Trend Line Data
    monthly_trend_data = {
        "labels": sorted_months,
        "totals": [round(monthly_trend[m], 2) for m in sorted_months]
    }

    # 2. Total Spend per Category Bar Data (Sorted descending)
    sorted_cats = sorted(category_totals.items(), key=lambda x: x[1], reverse=True)
    category_data = {
        "labels": [c[0] for c in sorted_cats],
        "totals": [round(c[1], 2) for c in sorted_cats]
    }

    # 3. Category Spending Month-over-Month Grouped Bar Data
    top_6_categories = [c[0] for c in sorted_cats[:6]]
    category_mom_datasets = []
    colors = ['#38bdf8', '#10b981', '#a855f7', '#f59e0b', '#f43f5e', '#64748b']
    for idx, cat_name in enumerate(top_6_categories):
        category_mom_datasets.append({
            "label": cat_name,
            "data": [round(category_mom[m][cat_name], 2) for m in sorted_months],
            "backgroundColor": colors[idx % len(colors)]
        })

    category_mom_data = {
        "labels": sorted_months,
        "datasets": category_mom_datasets
    }

    return {
        "status": "success",
        "monthly_trend": monthly_trend_data,
        "category_distribution": category_data,
        "category_mom": category_mom_data
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

@router.get("/export")
def export_excel():
    path = generate_master_excel()
    return {"status": "exported", "path": path}

@router.get("/vendors/export")
def export_vendor_list():
    path = generate_vendor_category_file()
    return {"status": "exported", "path": path}

@router.post("/vendors/apply")
def apply_vendor_categories():
    count = apply_vendor_category_file()
    generate_master_excel()
    return {"status": "applied", "updated_transactions": count}
