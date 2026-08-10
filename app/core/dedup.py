import hashlib
from datetime import date
from typing import Optional

def generate_transaction_hash(
    transaction_date: date,
    charged_amount: float,
    vendor: str,
    card_last_4: str,
    current_installment: int = 1,
    total_installments: int = 1,
    voucher: Optional[str] = None
) -> str:
    """
    Generates a deterministic SHA-256 fingerprint for a transaction to prevent duplicates.
    Includes optional voucher number to distinguish multiple identical transactions on the same date.
    """
    clean_vendor = "".join(vendor.strip().lower().split())
    date_str = transaction_date.strftime("%Y-%m-%d")
    amount_str = f"{charged_amount:.2f}"
    voucher_str = str(voucher).strip() if voucher else ""
    
    raw_payload = f"{date_str}|{amount_str}|{clean_vendor}|{card_last_4}|{current_installment}/{total_installments}|{voucher_str}"
    return hashlib.sha256(raw_payload.encode("utf-8")).hexdigest()
