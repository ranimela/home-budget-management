import re
from typing import Optional

def categorize_transaction(vendor: str, session=None) -> str:
    """Returns Uncategorized unless statement category or vendor mapping applies."""
    return "Uncategorized"

def categorize_vendor(vendor: str):
    return "Uncategorized", None
