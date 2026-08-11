import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
INPUTS_DIR = Path(r"C:\Users\rmelamed\Dropbox\Home Shared\Home Finance\Credit Cards")
OUTPUTS_DIR = DATA_DIR / "outputs"
DB_PATH = Path(r"C:\dev\db_storage\budget.db")
MASTER_EXCEL_PATH = OUTPUTS_DIR / "Master_Budget.xlsx"

# Ensure directories exist
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

