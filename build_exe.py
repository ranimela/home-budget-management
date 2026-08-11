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

        # Deploy to shared Dropbox folder
        deploy_dir = Path(r"C:\Users\rmelamed\Dropbox\Home Shared\Home Finance\HomeBudgetApp")
        if deploy_dir.parent.exists():
            print(f"\n Deploying to shared Dropbox viewing location: {deploy_dir} ...")
            deploy_dir.mkdir(parents=True, exist_ok=True)
            import shutil
            for item in (BASE_DIR / "dist" / "HomeBudgetManager").iterdir():
                dest = deploy_dir / item.name
                if item.is_dir():
                    shutil.copytree(item, dest, dirs_exist_ok=True)
                else:
                    try:
                        shutil.copy2(item, dest)
                    except PermissionError:
                        print(f" Warning: Could not overwrite {dest.name} (file in use). Close app to overwrite.")

            # Copy ongoing working Vendor_Category_Mapping.xlsx
            working_vendor_file = BASE_DIR / "data" / "inputs" / "Vendor_Category_Mapping.xlsx"
            if working_vendor_file.exists():
                shutil.copy2(working_vendor_file, deploy_dir / "Vendor_Category_Mapping.xlsx")
                print(f" Preserved ongoing working Vendor_Category_Mapping.xlsx to Dropbox!")
            print("=" * 60)
            print(f" DEPLOYMENT TO DROPBOX COMPLETE!")
            print(f" Executable Path: {deploy_dir / 'HomeBudgetManager.exe'}")
            print("=" * 60)
    else:
        print("\n BUILD FAILED with exit code:", res.returncode)
        sys.exit(res.returncode)

if __name__ == "__main__":
    build()
