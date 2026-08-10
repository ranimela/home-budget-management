from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from app.db.database import init_db
from app.api.routes import router as api_router
from app.config import INPUTS_DIR, OUTPUTS_DIR

app = FastAPI(
    title="Home Budget & Expense Manager",
    description="100% local, privacy-first credit card and budget manager",
    version="1.0.0"
)

# Initialize Database on startup
@app.on_event("startup")
def on_startup():
    init_db()

# Include API routes
app.include_router(api_router)

# Serve static web frontend if exists
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

@app.get("/")
def read_root():
    index_path = FRONTEND_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"message": "Home Budget Backend API active. Place files in ./data/inputs and trigger /api/scan"}
