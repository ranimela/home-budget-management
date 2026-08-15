import shutil
from pathlib import Path

def deploy():
    src_dist = Path(r"c:\Users\rmelamed\Projects\home-budget-management\dist\HomeBudgetManager")
    src_proj = Path(r"c:\Users\rmelamed\Projects\home-budget-management")
    dest_dir = Path(r"C:\Users\rmelamed\Dropbox\Home Shared\Home Finance\HomeBudgetApp")

    print("=" * 60)
    print(f" Deploying HomeBudgetApp to Shared Dropbox...")
    print(f" Target Directory: {dest_dir}")
    print("=" * 60)

    # 1. Ensure target directories exist
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_data = dest_dir / "data"
    dest_inputs = dest_data / "inputs"
    dest_outputs = dest_data / "outputs"
    dest_inputs.mkdir(parents=True, exist_ok=True)
    dest_outputs.mkdir(parents=True, exist_ok=True)

    # 2. Copy Executable & Dependencies (_internal)
    print(" Copying executable binaries and _internal dependencies...")
    for item in src_dist.iterdir():
        dest_item = dest_dir / item.name
        if item.is_dir():
            shutil.copytree(item, dest_item, dirs_exist_ok=True)
        else:
            try:
                shutil.copy2(item, dest_item)
            except PermissionError:
                pass

    # 3. Copy Ongoing Working Vendor_Category_Mapping.xlsx
    working_vendor_file = src_proj / "data" / "inputs" / "Vendor_Category_Mapping.xlsx"
    if working_vendor_file.exists():
        print(f" Preserving ongoing working vendor mapping file: {working_vendor_file.name}")
        shutil.copy2(working_vendor_file, dest_inputs / "Vendor_Category_Mapping.xlsx")

    # 4. Copy existing budget.db database and outputs
    src_db = src_proj / "data" / "budget.db"
    if src_db.exists():
        print(" Copying existing budget.db SQLite database...")
        shutil.copy2(src_db, dest_data / "budget.db")

    src_master = src_proj / "data" / "outputs" / "Master_Budget.xlsx"
    if src_master.exists():
        print(" Copying existing Master_Budget.xlsx...")
        shutil.copy2(src_master, dest_outputs / "Master_Budget.xlsx")

    # 5. Copy raw input statements
    src_inputs = src_proj / "data" / "inputs"
    if src_inputs.exists():
        for f in src_inputs.iterdir():
            if f.is_file():
                shutil.copy2(f, dest_inputs / f.name)

    print("\n" + "=" * 60)
    print(" DEPLOYMENT TO DROPBOX COMPLETE!")
    print(f" Shared Folder: {dest_dir}")
    print(f" Executable Path: {dest_dir / 'HomeBudgetManager.exe'}")
    print("=" * 60)

if __name__ == "__main__":
    deploy()
