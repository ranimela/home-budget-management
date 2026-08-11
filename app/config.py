import sys
from pathlib import Path

def get_base_dir() -> Path:
    """Returns executable parent folder if frozen in PyInstaller, else project root directory."""
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent

def get_bundle_dir() -> Path:
    """Returns PyInstaller temp directory (_MEIPASS) if frozen, else project root directory."""
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent.parent

BASE_DIR = get_base_dir()
BUNDLE_DIR = get_bundle_dir()

DATA_DIR = BASE_DIR / "data"
INPUTS_DIR = DATA_DIR / "inputs"
OUTPUTS_DIR = DATA_DIR / "outputs"
DB_PATH = DATA_DIR / "budget.db"
MASTER_EXCEL_PATH = OUTPUTS_DIR / "Master_Budget.xlsx"
STATIC_DIR = BUNDLE_DIR / "frontend"

# Fallback path check for user's existing Dropbox path
DROPBOX_INPUTS_PATH = Path(r"C:\Users\rmelamed\Dropbox\Home Shared\Home Finance\Credit Cards")

# Ensure required directories exist
INPUTS_DIR.mkdir(parents=True, exist_ok=True)
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH.parent.mkdir(parents=True, exist_ok=True)
