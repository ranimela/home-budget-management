import re
import pandas as pd
from datetime import datetime, date
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional
from app.core.dedup import generate_transaction_hash

class IsraeliCardStatementParser:
    """Parser engine for Israeli credit card statements (Max, Isracard, Cal)."""

    @staticmethod
    def parse_file(file_path: Path) -> Tuple[str, str, List[Dict[str, Any]]]:
        return IsraeliCardStatementParser.parse_statement_file(file_path)

    @staticmethod
    def parse_statement_file(file_path: Path) -> Tuple[str, str, List[Dict[str, Any]]]:
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

        text_dump = df.iloc[:15].to_string() + " " + file_path.name
        
        # Institution identification
        institution = "CREDIT_CARD"
        text_dump_lower = text_dump.lower()
        if "max" in text_dump_lower or "לאומיקארד" in text_dump_lower or "leumicard" in text_dump_lower or "מועדון הנחות" in text_dump_lower:
            institution = "MAX"
        elif "isracard" in text_dump_lower or "ישראכרט" in text_dump_lower:
            institution = "ISRACARD"
        elif "cal" in text_dump_lower or "כאל" in text_dump_lower or "visa" in text_dump_lower:
            institution = "CAL"

        # Extract global card number (excluding year 202X)
        card_matches = re.findall(r'\b(?!202\d)(\d{4})\b', text_dump)
        global_card_last_4 = card_matches[0] if card_matches else "0000"
        if global_card_last_4 == "0000":
            fn_matches = re.findall(r'\b(?!202\d)(\d{4})\b', file_path.name)
            if fn_matches:
                global_card_last_4 = fn_matches[0]

        # Extract global billing month from statement header or file name
        global_charge_date = None
        hdr_b_match = re.search(r'(?:לחיוב ב-|חיוב ב-|תאריך חיוב[:\s]*)([\d./-]+)', text_dump)
        if hdr_b_match:
            raw_b = hdr_b_match.group(1).strip()
            dt_parsed = IsraeliCardStatementParser._parse_date(raw_b)
            global_charge_date = date(dt_parsed.year, dt_parsed.month, 1)

        if not global_charge_date:
            fn_m = re.search(r'(\d{2})_(\d{4})', file_path.name)
            if fn_m:
                m_val = int(fn_m.group(1))
                y_val = int(fn_m.group(2))
                global_charge_date = date(y_val, m_val, 1)

        # Locate table header row
        header_idx = None
        for idx in range(min(25, len(df))):
            row_str = " ".join([str(val).replace('\n', ' ').strip().lower() for val in df.iloc[idx].values if pd.notna(val)])
            if ('תאריך' in row_str or 'date' in row_str) and ('שם' in row_str or 'עסק' in row_str or 'תיאור' in row_str or 'סכום' in row_str):
                header_idx = idx
                break

        transactions = []
        if header_idx is None:
            return institution, global_card_last_4, transactions

        raw_headers = [str(c).replace('\n', ' ').strip() for c in df.iloc[header_idx].values]
        df_data = df.iloc[header_idx + 1:].copy().reset_index(drop=True)
        df_data.columns = raw_headers

        # Column Identification
        col_date = IsraeliCardStatementParser._find_exact_col(df_data.columns, ['תאריך עסקה', 'תאריך רכישה', 'תאריך'])
        col_charge_date = IsraeliCardStatementParser._find_exact_col(df_data.columns, ['תאריך חיוב', 'מועד חיוב'])
        col_vendor = IsraeliCardStatementParser._find_exact_col(df_data.columns, ['שם בית העסק', 'שם בית עסק', 'שם עסק', 'תיאור'], exclude=['תאריך', 'date'])
        col_card = IsraeliCardStatementParser._find_exact_col(df_data.columns, ['4 ספרות אחרונות של כרטיס האשראי', '4 ספרות אחרונות', '4 ספרות'])
        col_charged_amt = IsraeliCardStatementParser._find_exact_col(df_data.columns, ['סכום חיוב', 'סכום בחיוב', 'חיוב', 'סכום'])
        col_charged_curr = IsraeliCardStatementParser._find_exact_col(df_data.columns, ['מטבע חיוב', 'מטבע לחיוב'])
        col_orig_amt = IsraeliCardStatementParser._find_exact_col(df_data.columns, ['סכום עסקה מקורי', 'סכום עסקה', 'סכום במקור', 'מקור'])
        col_orig_curr = IsraeliCardStatementParser._find_exact_col(df_data.columns, ['מטבע עסקה', 'מטבע מקור', 'מטבע'])
        col_category = IsraeliCardStatementParser._find_exact_col(df_data.columns, ['ענף', 'קטגוריה'])
        col_voucher = IsraeliCardStatementParser._find_exact_col(df_data.columns, ["מס' שובר", "מספר שובר", "שובר", "הערות"])

        for row_idx, row in df_data.iterrows():
            try:
                # Parse vendor
                if not col_vendor or pd.isna(row[col_vendor]):
                    continue
                raw_vendor = str(row[col_vendor]).strip()
                if not raw_vendor or raw_vendor.lower() in ['nan', 'none', '', 'סה"כ', 'סה''כ עסקה']:
                    continue

                # Parse transaction date
                if not col_date or pd.isna(row[col_date]):
                    continue
                raw_date_str = str(row[col_date]).strip()
                if not raw_date_str or not re.search(r'\d', raw_date_str):
                    continue
                parsed_date = IsraeliCardStatementParser._parse_date(raw_date_str)

                # Parse 4-digit card number per row
                card_last_4 = "0000"
                if col_card and pd.notna(row[col_card]):
                    card_val = re.sub(r'\D', '', str(row[col_card]).strip())
                    if len(card_val) >= 4:
                        card_last_4 = card_val[-4:]

                final_card_4 = card_last_4 if card_last_4 != "0000" else global_card_last_4

                # Detect currencies
                row_str_values = " ".join([str(val) for val in row.values if pd.notna(val)])
                
                orig_currency = "ILS"
                if col_orig_curr and pd.notna(row[col_orig_curr]):
                    orig_currency = IsraeliCardStatementParser._detect_currency(str(row[col_orig_curr]))
                else:
                    orig_currency = IsraeliCardStatementParser._detect_currency(row_str_values)

                charged_currency = "ILS"
                if col_charged_curr and pd.notna(row[col_charged_curr]):
                    charged_currency = IsraeliCardStatementParser._detect_currency(str(row[col_charged_curr]))

                # USER INSTRUCTION: Ignore and omit foreign currency transactions (USD, EUR, GBP)
                if orig_currency != "ILS" or charged_currency != "ILS":
                    continue

                # Parse actual billing date -> ALWAYS 1ST OF RELEVANT MONTH (01/mm/yy)
                row_charge_date = global_charge_date
                if col_charge_date and pd.notna(row[col_charge_date]):
                    raw_c_str = str(row[col_charge_date]).strip()
                    if raw_c_str and re.search(r'\d', raw_c_str):
                        dt_c = IsraeliCardStatementParser._parse_date(raw_c_str)
                        row_charge_date = date(dt_c.year, dt_c.month, 1)

                if not row_charge_date:
                    row_charge_date = date(parsed_date.year, parsed_date.month, 1)

                # Parse amounts
                charged_amt = 0.0
                if col_charged_amt and pd.notna(row[col_charged_amt]):
                    charged_amt = IsraeliCardStatementParser._parse_number(row[col_charged_amt])

                orig_amt = charged_amt
                if col_orig_amt and pd.notna(row[col_orig_amt]):
                    orig_amt = IsraeliCardStatementParser._parse_number(row[col_orig_amt])

                if charged_amt == 0.0 and orig_amt == 0.0:
                    continue

                # Parse statement native category
                existing_category = None
                if col_category and pd.notna(row[col_category]):
                    cat_val = str(row[col_category]).strip()
                    if cat_val and cat_val.lower() not in ['nan', 'none', '-']:
                        existing_category = cat_val

                # Parse voucher / row distinguisher
                voucher_val = f"r{row_idx}"
                if col_voucher and pd.notna(row[col_voucher]):
                    v_str = str(row[col_voucher]).strip()
                    if v_str and v_str.lower() not in ['nan', 'none']:
                        voucher_val = v_str

                # Parse installments across all row cells
                curr_inst, total_inst = 1, 1
                inst_match = re.search(r'(?:תשלום\s*)?(\d+)\s*(?:מתוך|of|/)\s*(\d+)', row_str_values)
                if inst_match:
                    curr_inst = int(inst_match.group(1))
                    total_inst = int(inst_match.group(2))

                hash_key = generate_transaction_hash(
                    transaction_date=parsed_date,
                    charged_amount=charged_amt,
                    vendor=raw_vendor,
                    card_last_4=final_card_4,
                    current_installment=curr_inst,
                    total_installments=total_inst,
                    voucher=voucher_val
                )

                transactions.append({
                    "hash_key": hash_key,
                    "source_file": file_path.name,
                    "institution": institution,
                    "card_last_4": final_card_4,
                    "transaction_date": parsed_date,
                    "charge_date": row_charge_date,
                    "vendor": raw_vendor,
                    "original_amount": orig_amt,
                    "original_currency": "ILS",
                    "charged_amount": charged_amt,
                    "charged_currency": "ILS",
                    "existing_category": existing_category,
                    "current_installment": curr_inst,
                    "total_installments": total_inst
                })
            except Exception:
                continue

        return institution, global_card_last_4, transactions

    @staticmethod
    def _detect_currency(val_str: str) -> str:
        s = val_str.upper()
        if '$' in s or 'USD' in s or 'דולר' in s:
            return 'USD'
        if '€' in s or 'EUR' in s or 'יורו' in s:
            return 'EUR'
        if '£' in s or 'GBP' in s or 'ליש' in s:
            return 'GBP'
        return 'ILS'

    @staticmethod
    def _find_exact_col(columns: List[str], candidates: List[str], exclude: Optional[List[str]] = None) -> Optional[str]:
        exclude_terms = [e.lower() for e in (exclude or [])]
        for candidate in candidates:
            for col in columns:
                col_str = str(col).lower().strip()
                if any(ex in col_str for ex in exclude_terms):
                    continue
                if candidate.lower() == col_str:
                    return col
        for candidate in candidates:
            for col in columns:
                col_str = str(col).lower().strip()
                if any(ex in col_str for ex in exclude_terms):
                    continue
                if candidate.lower() in col_str:
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
        for fmt in ['%d-%m-%Y', '%d/%m/%Y', '%d-%m-%y', '%d/%m/%y', '%Y-%m-%d', '%d.%m.%Y', '%d.%m.%y', '%d.%m']:
            try:
                dt = datetime.strptime(val_str, fmt)
                if fmt == '%d.%m':
                    dt = dt.replace(year=datetime.today().year)
                return dt.date()
            except ValueError:
                pass
        return datetime.today().date()

StatementParser = IsraeliCardStatementParser
