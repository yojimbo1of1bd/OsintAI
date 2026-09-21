# Lodestar — Project State

*Paste this whole file at the start of every new Claude session. You generally don't need to paste `DESIGN_AND_SCOPE.md` or `BUILD_PLAN.md` too — reference them by name ("see BUILD_PLAN.md Phase N") and Claude can ask for a specific section if it actually needs one. Keeping this file short is what keeps each new session cheap.*

## One-liner
Windows-local, passive-OSINT case assistant for Trace-Labs-style missing-persons CTF work. Python + FastAPI + SQLite + local Ollama.

## Hard scope (full version in DESIGN_AND_SCOPE.md §2)
- Passive collection only. No contact, no auth/CAPTCHA bypass, no dark-web automation, no scraping ToS-restricted platforms.
- Every finding needs a source URL.
- Custom scripts run only from `scripts/`, only with explicit confirm + logging.

## Current phase
Phase 0 — COMPLETE ✓

## Files that exist
```
app/__init__.py       — package marker
app/main.py           — FastAPI app, GET / (landing), GET /api/health
app/database.py       — SQLAlchemy engine, session, Base, init_db()
app/models.py         — empty, ready for Phase 1 tables
templates/index.html  — dark-themed landing page
static/style.css      — design system (CSS custom properties, dark mode)
data/.gitkeep         — placeholder (DB files gitignored)
scripts/.gitkeep      — placeholder for custom scripts (Phase 8)
docs/.gitkeep         — placeholder for documentation
requirements.txt      — pinned deps (fastapi, uvicorn, sqlalchemy, jinja2, python-multipart)
.gitignore            — excludes .venv/, data/*.db, __pycache__/
```

## Last session summary
Built Phase 0 skeleton. FastAPI app runs at 127.0.0.1:8420. Landing page serves correctly. Health endpoint returns JSON. SQLite DB auto-creates in data/. Fixed Starlette TemplateResponse API change (keyword args required in Starlette 1.6+).

## Next step
Phase 1 per BUILD_PLAN.md: Case Manager Core — create/list/pause/stop/delete cases backed by SQLite.

## Known bugs / open questions
- Favicon 404 (cosmetic — no favicon.ico yet, will add in polish phase)
