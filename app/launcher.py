import sys
import time
import socket
import webbrowser
import threading
import uvicorn
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from app.config import BASE_DIR, INPUTS_DIR, OUTPUTS_DIR, DB_PATH, APP_VERSION
from app.db.database import init_db
from app.ingestion.scanner import scan_and_ingest_inputs
from app.main import app

def find_available_port(start_port: int = 8000) -> int:
    """Finds an open port starting from start_port."""
    for port in range(start_port, start_port + 20):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('127.0.0.1', port)) != 0:
                return port
    return start_port

def launch_browser(url: str, delay_seconds: float = 2.0):
    """Waits until local web server responds, then opens browser."""
    import urllib.request
    for _ in range(30):
        time.sleep(0.5)
        try:
            with urllib.request.urlopen(url, timeout=1) as resp:
                if resp.status == 200:
                    break
        except Exception:
            pass
    webbrowser.open(url)

def main():
    print("=" * 60)
    print(f" Home Budget & Expense Manager v{APP_VERSION} - Desktop Launcher")
    print("=" * 60)
    
    # 1. Initialize SQLite Database & apply migrations
    print(f" [PATH] Base Directory:          {BASE_DIR}")
    print(f" [PATH] Monthly Reports Drop (Inputs): {INPUTS_DIR}")
    
    from app.export.vendor_list import get_active_mapping_path
    from app.config import MASTER_EXCEL_PATH
    active_mapping = get_active_mapping_path()
    print(f" [PATH] Active Vendor Rules File:      {active_mapping}")
    print(f" [PATH] SQLite Database Path:          {DB_PATH}")
    print(f" [PATH] Master Excel Output File:      {MASTER_EXCEL_PATH}")
    print("=" * 60)
    
    print("[1/3] Initializing SQLite database schema...")
    init_db()
    
    # 2. Perform background folder scanning & ingestion
    print(f"[2/3] Scanning monthly statement reports in: {INPUTS_DIR} ...")
    results = scan_and_ingest_inputs()
    print(f"      Successfully scanned {len(results)} file(s).")
    
    # 3. Launch Web Server & open local browser
    print("[3/3] Starting local Web UI at http://localhost:8000 ...")
    print(" [INFO] Opening your default web browser automatically...")
    print(" [HINT] Press Ctrl+C in this window to stop the application.\n")

    port = find_available_port(8000)
    url = f"http://127.0.0.1:{port}"

    threading.Thread(target=launch_browser, args=(url, 2.5), daemon=True).start()

    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")

if __name__ == "__main__":
    main()
