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
from contextlib import asynccontextmanager

from app.database import init_db
from app.routes.cases import router as cases_router
from app.routes.findings import router as findings_router
from app.routes.images import router as images_router
from app.routes.relationships import router as relationships_router
from app.routes.triage import router as triage_router
from app.routes.exporter import router as exporter_router
from app.routes.scripts import router as scripts_router
from app.routes.context import router as context_router
from app.routes.map import router as map_router
from app.routes.chat import router as chat_router
from app.routes.pipeline import router as pipeline_router

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

import sys
import logging

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: check for dangerous binding
    if "0.0.0.0" in sys.argv:
        logger.error("CRITICAL SECURITY RISK: Lodestar is attempting to bind to 0.0.0.0.")
        logger.error("This exposes sensitive case data to the local network or internet.")
        logger.error("Please run with host '127.0.0.1' only.")
        sys.exit(1)
        
    # Startup: create tables
    init_db()
    yield
    # Shutdown logic can go here

app = FastAPI(
    title="Lodestar",
    description="Passive-OSINT case assistant for missing-persons CTF work.",
    version="0.1.0",
    lifespan=lifespan,
)

# Resolve paths relative to the project root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Mount static files (CSS, JS, images)
app.mount(
    "/static",
    StaticFiles(directory=os.path.join(BASE_DIR, "static")),
    name="static",
)

images_dir = os.path.join(BASE_DIR, "data", "images")
os.makedirs(images_dir, exist_ok=True)
app.mount(
    "/images",
    StaticFiles(directory=images_dir),
    name="images",
)

# Jinja2 templates
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# Include route modules
app.include_router(cases_router)
app.include_router(findings_router)
app.include_router(images_router)
app.include_router(relationships_router)
app.include_router(triage_router)
app.include_router(exporter_router)
app.include_router(scripts_router)
app.include_router(context_router)
app.include_router(map_router)
app.include_router(chat_router)
app.include_router(pipeline_router)




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
