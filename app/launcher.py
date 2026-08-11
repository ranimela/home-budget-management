import sys
import time
import socket
import webbrowser
import threading
import uvicorn
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import BASE_DIR, INPUTS_DIR, OUTPUTS_DIR, DB_PATH
from app.main import app

def find_available_port(start_port: int = 8000) -> int:
    """Finds an open port starting from start_port."""
    for port in range(start_port, start_port + 20):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('127.0.0.1', port)) != 0:
                return port
    return start_port

def launch_browser(url: str, delay_seconds: float = 1.2):
    """Waits for server to start, then opens browser."""
    time.sleep(delay_seconds)
    webbrowser.open(url)

def main():
    print("=" * 60)
    print(" 💰 Home Budget & Expense Manager — Desktop Launcher")
    print("=" * 60)
    print(f" 📁 Base Directory: {BASE_DIR}")
    print(f" 📥 Credit Card Drop Location: {INPUTS_DIR}")
    print(f" 📊 Master Excel Location: {OUTPUTS_DIR}")
    print(f" 🗄️ Database Path: {DB_PATH}")
    print("=" * 60)

    port = find_available_port(8000)
    url = f"http://127.0.0.1:{port}"

    print(f" 🚀 Starting Local Server on {url} ...")
    print(" 🌐 Opening your default web browser automatically...")
    print(" 💡 Press Ctrl+C in this window to stop the application.\n")

    threading.Thread(target=launch_browser, args=(url,), daemon=True).start()

    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")

if __name__ == "__main__":
    main()
