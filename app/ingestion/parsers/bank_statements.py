import re
import pandas as pd
from datetime import datetime, date
from pathlib import Path
from typing import List, Tuple, Dict, Any
from app.core.dedup import generate_transaction_hash

class BankStatementParser:
    """Parser for Israeli Bank Checking Account statements (Hapoalim, Leumi, Mizrahi, Discount)."""

    @staticmethod
    def parse_bank_file(file_path: Path) -> Tuple[str, str, List[Dict[str, Any]]]:
        """
        Parses bank checking account statements.
        Returns: (bank_name, account_number, list_of_transactions)
        """
        ext = file_path.suffix.lower()
        if ext in ['.xlsx', '.xls']:
            try:
                excel_file = pd.ExcelFile(file_path)
                df = excel_file.parse(excel_file.sheet_names[0])
            except Exception:
                df = pd.read_csv(file_path, encoding='utf-8-sig', errors='replace')
        elif ext == '.csv':
            try:
                df = pd.read_csv(file_path, encoding='utf-8-sig')
            except Exception:
                df = pd.read_csv(file_path, encoding='iso-8859-8', errors='replace')
        else:
            raise ValueError(f"Unsupported file format: {ext}")

        text_dump = df.iloc[:15].to_string().lower() + " " + file_path.name.lower()
        
        bank_name = "BANK_UNKNOWN"
        if "hapoalim" in text_dump or "הפועלים" in text_dump:
            bank_name = "HAPOALIM"
        elif "leumi" in text_dump or "לאומי" in text_dump:
            bank_name = "LEUMI"
        elif "mizrahi" in text_dump or "מזרחי" in text_dump:
            bank_name = "MIZRAHI"
        elif "discount" in text_dump or "דיסקונט" in text_dump:
            bank_name = "DISCOUNT"

        acct_match = re.search(r'(?:חשבון|account|ח\"פ)\D*?(\d{3,9})', text_dump)
        account_no = acct_match.group(1) if acct_match else "0000"

        transactions = []
        header_idx = None
        for idx in range(min(25, len(df))):
            row_vals = [str(val).replace('\n', ' ').strip().lower() for val in df.iloc[idx].values if pd.notna(val)]
            row_str = " ".join(row_vals)
            if any(term in row_str for term in ['תאריך', 'תיאור', 'זכות', 'חובה', 'סכום', 'יתרה']):
                header_idx = idx
                break

        if header_idx is None:
            return bank_name, account_no, transactions

        raw_headers = [str(c).replace('\n', ' ').strip() for c in df.iloc[header_idx].values]
        df_data = df.iloc[header_idx + 1:].copy().reset_index(drop=True)
        df_data.columns = raw_headers

        col_date = BankStatementParser._find_col(df_data.columns, ['תאריך', 'date'])
        col_vendor = BankStatementParser._find_col(df_data.columns, ['תיאור', 'שם עסק', 'פרטים', 'description'])
        col_debit = BankStatementParser._find_col(df_data.columns, ['חובה', 'סכום חובה', 'debit'])
        col_credit = BankStatementParser._find_col(df_data.columns, ['זכות', 'סכום זכות', 'credit'])
        col_amount = BankStatementParser._find_col(df_data.columns, ['סכום', 'amount'])

        for _, row in df_data.iterrows():
            try:
                if not col_vendor or pd.isna(row[col_vendor]):
                    continue
                raw_vendor = str(row[col_vendor]).strip()
                if not raw_vendor or raw_vendor.lower() in ['nan', 'none', '', 'סה"כ']:
                    continue

                if not col_date or pd.isna(row[col_date]):
                    continue
                parsed_date = BankStatementParser._parse_date(str(row[col_date]))

                # Calculate debit amount
                debit_amt = 0.0
                if col_debit and pd.notna(row[col_debit]):
                    debit_amt = BankStatementParser._parse_number(row[col_debit])
                elif col_amount and pd.notna(row[col_amount]):
                    debit_amt = BankStatementParser._parse_number(row[col_amount])

                if debit_amt == 0.0:
                    continue

                hash_key = generate_transaction_hash(
                    transaction_date=parsed_date,
                    charged_amount=debit_amt,
                    vendor=raw_vendor,
                    card_last_4=account_no,
                    current_installment=1,
                    total_installments=1
                )

                transactions.append({
                    "hash_key": hash_key,
                    "source_file": file_path.name,
                    "institution": bank_name,
                    "card_last_4": account_no,
                    "transaction_date": parsed_date,
                    "vendor": raw_vendor,
                    "original_amount": debit_amt,
                    "original_currency": "ILS",
                    "charged_amount": debit_amt,
                    "charged_currency": "ILS",
                    "current_installment": 1,
                    "total_installments": 1
                })
            except Exception:
                continue

        return bank_name, account_no, transactions

    @staticmethod
    def _find_col(columns: List[str], candidates: List[str]) -> Optional[str]:
        for candidate in candidates:
            for col in columns:
                if candidate.lower() in str(col).lower():
                    return col
        return None

    @staticmethod
    def _parse_number(val: Any) -> float:
        if isinstance(val, (int, float)):
            return float(val)
        val_str = str(val).replace('₪', '').replace('$', '').replace(',', '').strip()
        val_str = re.sub(r'[^\d.-]', '', val_str)
        try:
            return abs(float(val_str))
        except ValueError:
            return 0.0

    @staticmethod
    def _parse_date(val_str: str) -> date:
        if isinstance(val_str, (datetime, pd.Timestamp)):
            return val_str.date()
        val_str = str(val_str).split(' ')[0].strip()
        for fmt in ['%d/%m/%Y', '%d/%m/%y', '%Y-%m-%d', '%d-%m-%Y', '%d.%m.%Y', '%d.%m.%y']:
            try:
                return datetime.strptime(val_str, fmt).date()
            except ValueError:
                pass
        return datetime.today().date()
