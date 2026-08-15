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
APP_VERSION = "1.0.0"

def get_inputs_dir() -> Path:
    """Prioritizes shared Dropbox Credit Cards folder, with dynamic fallback to local data/inputs."""
    primary_dropbox = Path(r"C:\Users\rmelamed\Dropbox\Home Shared\Home Finance\Credit Cards")
    if primary_dropbox.exists():
        return primary_dropbox
    
    user_dropbox = Path.home() / "Dropbox" / "Home Shared" / "Home Finance" / "Credit Cards"
    if user_dropbox.exists():
        return user_dropbox

    local_inputs = BASE_DIR / "data" / "inputs"
    local_inputs.mkdir(parents=True, exist_ok=True)
    return local_inputs

DATA_DIR = BASE_DIR / "data"
INPUTS_DIR = get_inputs_dir()
OUTPUTS_DIR = DATA_DIR / "outputs"

def get_db_path() -> Path:
    """Returns BASE_DIR/data/budget.db when running as frozen .exe in Dropbox, or dev DB in project dev mode."""
    if getattr(sys, 'frozen', False):
        local_db = DATA_DIR / "budget.db"
        local_db.parent.mkdir(parents=True, exist_ok=True)
        return local_db
    
    dev_db = Path(r"C:\dev\db_storage\budget.db")
    if dev_db.exists():
        return dev_db
        
    local_db = DATA_DIR / "budget.db"
    local_db.parent.mkdir(parents=True, exist_ok=True)
    return local_db

DB_PATH = get_db_path()
MASTER_EXCEL_PATH = OUTPUTS_DIR / "Master_Budget.xlsx"
STATIC_DIR = BUNDLE_DIR / "frontend"

# Ensure required directories exist
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH.parent.mkdir(parents=True, exist_ok=True)
