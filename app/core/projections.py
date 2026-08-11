from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from sqlmodel import Session, select
from typing import List, Dict, Any
from app.db.database import engine
from app.db.models import Transaction

from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from sqlmodel import Session, select
from typing import List, Dict, Any
from collections import defaultdict

from app.db.database import engine
from app.db.models import Transaction, CardMapping
from app.export.excel_generator import CARD_DISPLAY_NAMES

FIXED_RECURRING_CATEGORIES = {
    "insurance", "education", "utilities", "subscriptions", "standing orders",
    "ביטוח", "חינוך", "הוראת קבע", "תקשורת", "חשבונות"
}

def calculate_monthly_projections(months_ahead: int = 12) -> List[Dict[str, Any]]:
    """
    Calculates 12-month forward budget projections incorporating:
    1. Active installment roll-forward schedule (current_installment < total_installments).
    2. Rolling 3-month average of fixed recurring categories.
    3. Combined total projected commitment per future month.
    """
    today = date.today()
    start_month = date(today.year, today.month, 1) + relativedelta(months=1)
    
    with Session(engine) as session:
        txs = session.exec(select(Transaction)).all()
        card_mappings = {m.card_last_4: m for m in session.exec(select(CardMapping)).all()}

    if not txs:
        # Cold-start zero fallback
        projections = []
        for i in range(months_ahead):
            future_date = start_month + relativedelta(months=i)
            projections.append({
                "projection_month": future_date.strftime("%Y-%m-01"),
                "display_month": future_date.strftime("%m/%y"),
                "locked_installments_ils": 0.0,
                "active_installments_count": 0,
                "fixed_recurring_baseline_ils": 0.0,
                "total_projected_commitment_ils": 0.0,
                "installment_items": []
            })
        return projections

    # 1. Compute Rolling 3-Month Fixed Recurring Baseline
    all_months = sorted(list({ (t.charge_date or t.transaction_date).strftime("%Y-%m") for t in txs }))
    recent_3_months = set(all_months[-3:]) if len(all_months) >= 3 else set(all_months)
    
    fixed_recurring_total = 0.0
    for t in txs:
        m_str = (t.charge_date or t.transaction_date).strftime("%Y-%m")
        cat_lower = (t.category or "").lower()
        vendor_lower = t.vendor.lower()
        if m_str in recent_3_months:
            if any(f in cat_lower or f in vendor_lower for f in FIXED_RECURRING_CATEGORIES):
                fixed_recurring_total += t.charged_amount

    fixed_baseline_monthly = round(fixed_recurring_total / max(len(recent_3_months), 1), 2)

    # 2. Extract Active Installment Transactions
    installments_txs = [t for t in txs if t.total_installments > 1 and t.current_installment < t.total_installments]

    # 3. Build 12-Month Projection Matrix
    projections = []
    
    for i in range(months_ahead):
        future_date = start_month + relativedelta(months=i)
        future_month_str = future_date.strftime("%m/%y")
        
        locked_installments_sum = 0.0
        installment_items = []
        
        for inst_tx in installments_txs:
            base_date = date((inst_tx.charge_date or inst_tx.transaction_date).year, (inst_tx.charge_date or inst_tx.transaction_date).month, 1)
            months_passed = (future_date.year - base_date.year) * 12 + (future_date.month - base_date.month)
            scheduled_payment_no = inst_tx.current_installment + months_passed
            
            if 1 <= scheduled_payment_no <= inst_tx.total_installments:
                amount = round(inst_tx.charged_amount, 2)
                locked_installments_sum += amount
                
                c_num = inst_tx.card_last_4
                c_label = CARD_DISPLAY_NAMES.get(c_num, card_mappings[c_num].display_name if c_num in card_mappings else f"Card {c_num}")
                
                installment_items.append({
                    "vendor": inst_tx.vendor,
                    "card_last_4": c_num,
                    "card_name": c_label,
                    "user_name": inst_tx.user_name or "Unassigned",
                    "installment_payment": f"{scheduled_payment_no}/{inst_tx.total_installments}",
                    "monthly_amount_ils": amount
                })

        locked_installments_sum = round(locked_installments_sum, 2)
        total_commitment = round(locked_installments_sum + fixed_baseline_monthly, 2)

        projections.append({
            "projection_month": future_date.strftime("%Y-%m-01"),
            "display_month": future_month_str,
            "locked_installments_ils": locked_installments_sum,
            "active_installments_count": len(installment_items),
            "fixed_recurring_baseline_ils": fixed_baseline_monthly,
            "total_projected_commitment_ils": total_commitment,
            "installment_items": installment_items
        })

    return projections

if __name__ == "__main__":
    matrix = calculate_monthly_projections(12)
    print("12-Month Cash Flow Projection Matrix:")
    for m in matrix[:3]:
        print(m)

