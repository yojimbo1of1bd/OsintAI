# Lodestar — Project State

*Paste this whole file at the start of every new Claude session. You generally don't need to paste `DESIGN_AND_SCOPE.md` or `BUILD_PLAN.md` too — reference them by name ("see BUILD_PLAN.md Phase N") and Claude can ask for a specific section if it actually needs one. Keeping this file short is what keeps each new session cheap.*

## One-liner
Windows-local, passive-OSINT case assistant for Trace-Labs-style missing-persons CTF work. Python + FastAPI + SQLite + local Ollama.

## Hard scope (full version in DESIGN_AND_SCOPE.md §2)
- Passive collection only. No contact, no auth/CAPTCHA bypass, no dark-web automation, no scraping ToS-restricted platforms.
- Every finding needs a source URL.
- Custom scripts run only from `scripts/`, only with explicit confirm + logging.

## Current phase
Phase 1, 2, 3, 4, & 5 — COMPLETE ✓

## Files that exist
```
app/__init__.py       — package marker
app/main.py           — FastAPI app, routers for cases & findings included
app/database.py       — SQLAlchemy engine, session, Base, init_db()
app/models.py         — Case & Finding models
app/correlator.py     — Maigret username correlation logic
app/routes/cases.py   — routes for case management
app/routes/findings.py — routes for finding management
app/routes/images.py  — routes for image uploads and EXIF extraction
app/routes/relationships.py — routes for relationship mapper
templates/index.html  — dark-themed landing page
templates/cases.html  — case list and creation UI
templates/case_detail.html — specific case and findings UI
static/style.css      — design system (CSS custom properties, dark mode)
data/.gitkeep         — placeholder (DB files gitignored)
data/images/          — directory for local image storage
scripts/.gitkeep      — placeholder for custom scripts (Phase 8)
docs/.gitkeep         — placeholder for documentation
requirements.txt      — pinned deps (fastapi, uvicorn, sqlalchemy, jinja2, python-multipart, exifread, Pillow, maigret)
.gitignore            — excludes .venv/, data/*.db, data/images/*, __pycache__/
```

## Last session summary
Verified and completed Phase 5 (Relationship Mapper). Implemented the `Relationship` SQLAlchemy model. Created the `app/routes/relationships.py` router to handle creation and deletion of relationships. Updated `case_detail.html` with an input form (enforcing source URLs), a tabular list view, and an interactive graph visualization using `vis-network`.

## Next step
Phase 6 per BUILD_PLAN.md: Data Export — JSON/CSV export of case findings/relationships.

## Known bugs / open questions
- Favicon 404 (cosmetic — no favicon.ico yet, will add in polish phase)
