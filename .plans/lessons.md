# Lessons Log
Add one line per problem that cost time (what happened, what rule or convention would have prevented it).
Promote repeated lessons into `conventions.md` here and into the master template.

- (2026-08-13) Automatic `.exe` builds during intermediate tasks risked overwriting the stable Dropbox executable -> Never run `build_exe.py` or `deploy_to_dropbox.py` unless the user explicitly asks to export the `.exe`.
- (2026-08-13) Frontend month filter compared `01/MM/YY` (`charge_date`) against `MM/YY` filter checkboxes, resulting in zero totals -> Always normalize `01/MM/YY` dates to `MM/YY` before matching against month filters.
- (2026-09-11) Local `data/inputs/Vendor_Category_Mapping.xlsx` shadowed the user's updated Dropbox mapping file -> Always prioritize `DROPBOX_MAPPING_PATH` (`INPUTS_DIR / "Vendor_Category_Mapping.xlsx"`) first and treat `Vendor_Category_Mapping.xlsx` as strictly read-only.
- (2026-09-11) Both `run_server_home_finance.bat` and `app/launcher.py` opened a browser tab on startup -> Let `app/launcher.py` handle opening the single browser tab after Uvicorn responds.
- (2026-09-12) Multi-month installment plans appeared multiple times in 12-month projections because each monthly statement file contains a step row (`1/12`, `2/12`, etc.) -> Deduplicate active installments by `(vendor, card_last_4, charged_amount, total_installments)` keeping only the latest statement record.
