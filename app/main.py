"""
Lodestar — Main application entry point.

A passive-OSINT case assistant for Trace Labs-style missing-persons CTF work.
Binds to 127.0.0.1:8420 only — never 0.0.0.0 — because case data must
stay local.
"""

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os

from app.database import init_db

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Lodestar",
    description="Passive-OSINT case assistant for missing-persons CTF work.",
    version="0.1.0",
)

# Resolve paths relative to the project root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Mount static files (CSS, JS, images)
app.mount(
    "/static",
    StaticFiles(directory=os.path.join(BASE_DIR, "static")),
    name="static",
)

# Jinja2 templates
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))


# ---------------------------------------------------------------------------
# Startup — create tables on first run
# ---------------------------------------------------------------------------

@app.on_event("startup")
def on_startup():
    init_db()


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def landing_page(request: Request):
    """Serve the main landing page."""
    return templates.TemplateResponse(request=request, name="index.html")


@app.get("/api/health", response_class=JSONResponse)
async def health_check():
    """Quick health-check endpoint for debugging and monitoring."""
    return {"status": "running", "message": "Lodestar is running"}


# ---------------------------------------------------------------------------
# Direct launch: python -m app.main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",  # Local only — never 0.0.0.0
        port=8420,
        reload=True,
    )
