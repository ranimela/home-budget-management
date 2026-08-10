import pytest
from datetime import date
from sqlmodel import SQLModel, create_engine, Session
from app.db.models import Transaction
from app.core.dedup import generate_transaction_hash
from app.export.excel_generator import generate_master_excel

def test_transaction_hash_deduplication():
    hash1 = generate_transaction_hash(date(2026, 7, 1), 150.0, "Super-Pharm", "1234", 1, 1)
    hash2 = generate_transaction_hash(date(2026, 7, 1), 150.0, "Super-Pharm", "1234", 1, 1)
    hash3 = generate_transaction_hash(date(2026, 7, 1), 150.0, "Super-Pharm", "1234", 2, 5)
    
    assert hash1 == hash2
    assert hash1 != hash3

def test_excel_generation(tmp_path):
    # Isolated test database in memory
    test_engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(test_engine)
    
    with Session(test_engine) as session:
        tx = Transaction(
            hash_key="test_hash_unique_123",
            source_file="test_unit.xlsx",
            institution="MAX",
            card_last_4="1234",
            user_name="TestUser",
            transaction_date=date(2026, 7, 10),
            vendor="Shufersal",
            original_amount=250.0,
            original_currency="ILS",
            charged_amount=250.0,
            charged_currency="ILS",
            category="Groceries",
            current_installment=1,
            total_installments=1
        )
        session.add(tx)
        session.commit()

    excel_path = generate_master_excel()
    assert "Master_Budget" in excel_path

