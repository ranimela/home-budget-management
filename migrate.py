from sqlalchemy import text
from app.db.database import engine
from app.export.vendor_list import generate_vendor_category_file

def migrate():
    with engine.connect() as conn:
        try:
            conn.execute(text('ALTER TABLE "transaction" ADD COLUMN subcategory TEXT;'))
            conn.commit()
            print("Successfully added subcategory column to transaction table!")
        except Exception as e:
            print("Migration info:", e)

if __name__ == "__main__":
    migrate()
    path = generate_vendor_category_file()
    print("Vendor Category Excel file updated at:", path)
