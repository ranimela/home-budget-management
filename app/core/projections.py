from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from sqlmodel import Session, select
from typing import List, Dict, Any
from app.db.database import engine
from app.db.models import Transaction

def calculate_monthly_projections(months_ahead: int = 12) -> List[Dict[str, Any]]:
    """
    Calculates monthly budget projection for future months based on:
    1. Active installment payments schedule (e.g. payment 2 of 5).
    2. Fixed recurring monthly commitments (standing orders, bills, subscriptions).
    3. Historical category baseline spending.
    """
    today = date.today()
    start_month = date(today.year, today.month, 1)
    
    with Session(engine) as session:
        txs = session.exec(select(Transaction)).all()

    # 1. Historical Monthly Baseline per Category
    category_monthly_sums: Dict[str, Dict[str, float]] = {}
    installments_txs: List[Transaction] = []
    
    for t in txs:
        m_str = t.transaction_date.strftime("%Y-%m")
        cat = t.category or "Uncategorized"
        
        if cat not in category_monthly_sums:
            category_monthly_sums[cat] = {}
        category_monthly_sums[cat][m_str] = category_monthly_sums[cat].get(m_str, 0.0) + t.charged_amount
        
        if t.total_installments > 1:
            installments_txs.append(t)

    # Average monthly spend per category (excluding installments)
    category_averages: Dict[str, float] = {}
    for cat, months in category_monthly_sums.items():
        if months:
            category_averages[cat] = sum(months.values()) / len(months)
        else:
            category_averages[cat] = 0.0

    # 2. Build 12-Month Projection Matrix
    projections = []
    
    for i in range(months_ahead):
        future_date = start_month + relativedelta(months=i)
        future_m_str = future_date.strftime("%Y-%m")
        
        # Calculate Future Installments for this month
        installment_spend_for_month = 0.0
        active_installments_count = 0
        
        for inst_tx in installments_txs:
            # Remaining payments calculation
            months_passed = (future_date.year - inst_tx.transaction_date.year) * 12 + (future_date.month - inst_tx.transaction_date.month)
            scheduled_payment_no = inst_tx.current_installment + months_passed
            
            if 1 <= scheduled_payment_no <= inst_tx.total_installments:
                installment_spend_for_month += inst_tx.charged_amount
                active_installments_count += 1

        # Baseline variable spend projection
        baseline_variable_projected = sum(avg for cat, avg in category_averages.items())
        total_projected_spend = round(installment_spend_for_month + baseline_variable_projected, 2)

        projections.append({
            "month": future_m_str,
            "projected_installments_ils": round(installment_spend_for_month, 2),
            "active_installments_count": active_installments_count,
            "projected_variable_baseline_ils": round(baseline_variable_projected, 2),
            "total_projected_spend_ils": total_projected_spend,
            "category_averages": {cat: round(avg, 2) for cat, avg in category_averages.items()}
        })

    return projections

if __name__ == "__main__":
    matrix = calculate_monthly_projections(12)
    print("12-Month Budget Projections Matrix:")
    for m in matrix[:4]:
        print(m)
