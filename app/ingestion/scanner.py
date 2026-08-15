from pathlib import Path
from sqlmodel import Session, select
from app.config import INPUTS_DIR
from app.db.database import engine, init_db
from app.db.models import Transaction, IngestionLog, CardMapping
from app.ingestion.parsers.israeli_cards import StatementParser
from app.core.categories import categorize_transaction

def scan_and_ingest_inputs() -> list[dict]:
    """Scans the INPUTS_DIR recursively for Excel/CSV statement files and ingests them into SQLite."""
    init_db()
    results = []
    
    # Recursive search in INPUTS_DIR - deduplicate files by filename keeping latest mtime
    all_files = [f for f in INPUTS_DIR.rglob('*') if f.suffix.lower() in ['.xlsx', '.xls', '.csv'] and 'Vendor_Category' not in f.name and 'Master_Budget' not in f.name]
    
    file_map = {}
    for f in all_files:
        # If file exists in both root and subfolder, keep the one with newest mtime (or root file if mtime equal)
        if f.name not in file_map or f.stat().st_mtime > file_map[f.name].stat().st_mtime or (f.parent == INPUTS_DIR and f.stat().st_mtime == file_map[f.name].stat().st_mtime):
            file_map[f.name] = f
            
    input_files = sorted(file_map.values(), key=lambda x: x.name)

    
    with Session(engine) as session:
        card_mappings = {m.card_last_4: m.owner_name for m in session.exec(select(CardMapping)).all()}
        
        for file_path in input_files:
            try:
                institution, card_last_4, raw_txs = StatementParser.parse_file(file_path)
                
                imported_count = 0
                duplicate_count = 0
                
                for tx_data in raw_txs:
                    card_4 = tx_data.get("card_last_4", "0000")
                    user_name = card_mappings.get(card_4)
                    if not user_name or user_name == "Unassigned":
                        folder_name = file_path.parent.name.lower()
                        if "rani" in folder_name or card_4 in ['9380', '4591', '1365', '1527', '1657', '1011', '2004']:
                            user_name = "Rani"
                        elif "yael" in folder_name or card_4 in ['1123', '4656', '1794', '4906', '3893', '4006', '3623', '8813', '5632']:
                            user_name = "Yael"
                        else:
                            user_name = "Unassigned"

                    # USER INSTRUCTION: Ignore categories from raw credit card files.
                    # Default all new transactions to Uncategorized, overridden strictly by Vendor_Category_Mapping.xlsx
                    category = "Uncategorized"
                    subcategory = None

                    # Check for existing record by hash_key
                    existing = session.exec(select(Transaction).where(Transaction.hash_key == tx_data["hash_key"])).first()
                    if existing:
                        duplicate_count += 1
                        continue

                    
                    tx = Transaction(
                        hash_key=tx_data["hash_key"],
                        source_file=file_path.name,
                        institution=tx_data["institution"],
                        card_last_4=tx_data["card_last_4"],
                        user_name=user_name,
                        transaction_date=tx_data["transaction_date"],
                        charge_date=tx_data.get("charge_date"),
                        vendor=tx_data["vendor"],
                        original_amount=tx_data["original_amount"],
                        original_currency=tx_data["original_currency"],
                        charged_amount=tx_data["charged_amount"],
                        charged_currency=tx_data["charged_currency"],
                        category=category,
                        subcategory=subcategory,
                        current_installment=tx_data["current_installment"],
                        total_installments=tx_data["total_installments"]
                    )

                    session.add(tx)
                    imported_count += 1



                
                session.commit()
                
                log = IngestionLog(
                    filename=file_path.name,
                    status="SUCCESS",
                    imported_count=imported_count,
                    duplicate_count=duplicate_count,
                    message=f"Ingested {imported_count} new, skipped {duplicate_count} duplicates."
                )
                session.add(log)
                session.commit()
                
                results.append({
                    "filename": file_path.name,
                    "status": "SUCCESS",
                    "imported": imported_count,
                    "duplicates": duplicate_count,
                    "institution": institution,
                    "card_last_4": card_last_4
                })
            except Exception as e:
                log = IngestionLog(
                    filename=file_path.name,
                    status="ERROR",
                    imported_count=0,
                    duplicate_count=0,
                    message=str(e)
                )
                session.add(log)
                session.commit()
                results.append({
                    "filename": file_path.name,
                    "status": "ERROR",
                    "error": str(e)
                })
                
    from app.export.vendor_list import apply_vendor_category_file
    apply_vendor_category_file()

    return results

if __name__ == "__main__":
    scan_results = scan_and_ingest_inputs()
    print("Scan Summary:", scan_results)
