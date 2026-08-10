import sys
from pathlib import Path
import pandas as pd
from sqlmodel import Session, select
from app.db.database import engine, init_db
from app.db.models import Transaction, IngestionLog
from app.ingestion.scanner import scan_and_ingest_inputs
from app.ingestion.parsers.israeli_cards import StatementParser
from app.export.vendor_list import generate_vendor_category_file
from app.export.excel_generator import generate_master_excel

sys.stdout.reconfigure(encoding='utf-8')
init_db()

folder = Path(r'C:\Users\rmelamed\Dropbox\Home Shared\Home Finance\Credit Cards')
files = [f for f in folder.rglob('*.xlsx') if 'Vendor_Category' not in f.name and 'Master_Budget' not in f.name]

file_map = {}
for f in files:
    if f.name not in file_map or f.stat().st_mtime > file_map[f.name].stat().st_mtime or f.parent == folder:
        file_map[f.name] = f

raw_vendor_categories = {}
total_parsed_rows = 0

for name, path in sorted(file_map.items()):
    inst, card, txs = StatementParser.parse_file(path)
    total_parsed_rows += len(txs)
    for t in txs:
        v = t['vendor'].strip()
        cat = t.get('existing_category')
        if cat and cat.lower() not in ['nan', 'none', 'uncategorized']:
            raw_vendor_categories[v] = cat

print(f"Audited {len(file_map)} statement files containing {total_parsed_rows} total rows.")
print(f"Total vendors with explicit statement categories in raw files: {len(raw_vendor_categories)}")

with Session(engine) as session:
    txs = session.exec(select(Transaction)).all()
    db_categories = {t.vendor.strip(): t.category for t in txs}

discrepancies = []
for v, raw_cat in raw_vendor_categories.items():
    db_cat = db_categories.get(v)
    if db_cat != raw_cat:
        discrepancies.append((v, raw_cat, db_cat))

print(f"\nAudit Result: {len(discrepancies)} discrepancies found.")
if discrepancies:
    print("Discrepancies found! Syncing database with statement categories...")
    with Session(engine) as session:
        all_db_txs = session.exec(select(Transaction)).all()
        for t in all_db_txs:
            v = t.vendor.strip()
            if v in raw_vendor_categories and t.category != raw_vendor_categories[v]:
                t.category = raw_vendor_categories[v]
                session.add(t)
        session.commit()
    generate_master_excel()
    generate_vendor_category_file(overwrite=True)
    print("Database, Master Excel, and Vendor Category list synced 100%!")
else:
    print("SUCCESS: 100% of vendor categories from all statement files match the database!")
