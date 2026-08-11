import os
import sys
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

def build():
    print("=" * 60)
    print(" Compiling Standalone HomeBudgetManager.exe ...")
    print("=" * 60)

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--onedir",
        "--name=HomeBudgetManager",
        f"--add-data={BASE_DIR / 'frontend'};frontend",
        "--hidden-import=uvicorn.logging",
        "--hidden-import=uvicorn.loops",
        "--hidden-import=uvicorn.loops.auto",
        "--hidden-import=uvicorn.protocols",
        "--hidden-import=uvicorn.protocols.http",
        "--hidden-import=uvicorn.protocols.http.auto",
        "--hidden-import=uvicorn.lifespan",
        "--hidden-import=uvicorn.lifespan.on",
        "--hidden-import=sqlmodel",
        "--hidden-import=openpyxl",
        str(BASE_DIR / "app" / "launcher.py")
    ]

    print(f"Running command: {' '.join(cmd)}")
    res = subprocess.run(cmd, cwd=str(BASE_DIR))
    if res.returncode == 0:
        exe_path = BASE_DIR / "dist" / "HomeBudgetManager" / "HomeBudgetManager.exe"
        print("\n" + "=" * 60)
        print(" BUILD SUCCESSFUL!")
        print(f" Executable location: {exe_path}")
        print("=" * 60)
    else:
        print("\n BUILD FAILED with exit code:", res.returncode)
        sys.exit(res.returncode)

if __name__ == "__main__":
    build()
