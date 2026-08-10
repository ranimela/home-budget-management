from datetime import date, datetime, timezone
from typing import Optional
from sqlmodel import Field, SQLModel

class Transaction(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    hash_key: str = Field(index=True, unique=True)
    source_file: str
    institution: str  # MAX, ISRACARD, CAL, LEUMI, HAPOALIM, MIZRAHI, UNKNOWN
    card_last_4: str = Field(default="0000", index=True)
    user_name: str = Field(default="Unassigned", index=True)
    
    transaction_date: date = Field(index=True)
    charge_date: Optional[date] = None
    vendor: str = Field(index=True)
    
    original_amount: float
    original_currency: str = "ILS"  # ILS, USD, EUR, etc.
    charged_amount: float
    charged_currency: str = "ILS"
    
    category: str = Field(default="Uncategorized", index=True)
    subcategory: Optional[str] = Field(default=None, index=True)
    current_installment: int = 1

    total_installments: int = 1
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class CardMapping(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    card_last_4: str = Field(unique=True, index=True)
    institution: str
    owner_name: str
    display_name: str

class CategoryRule(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    pattern: str = Field(unique=True)  # Regex pattern to match vendor name
    category: str

class IngestionLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    filename: str
    status: str  # SUCCESS, WARNING, ERROR
    imported_count: int = 0
    duplicate_count: int = 0
    message: str = ""
    processed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

