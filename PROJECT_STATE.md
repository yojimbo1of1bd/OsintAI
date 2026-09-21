# Lodestar — Project State

*Paste this whole file at the start of every new Claude session. You generally don't need to paste `DESIGN_AND_SCOPE.md` or `BUILD_PLAN.md` too — reference them by name ("see BUILD_PLAN.md Phase N") and Claude can ask for a specific section if it actually needs one. Keeping this file short is what keeps each new session cheap.*

## One-liner
Windows-local, passive-OSINT case assistant for Trace-Labs-style missing-persons CTF work. Python + FastAPI + SQLite + local Ollama.

## Hard scope (full version in DESIGN_AND_SCOPE.md §2)
- Passive collection only. No contact, no auth/CAPTCHA bypass, no dark-web automation, no scraping ToS-restricted platforms.
- Every finding needs a source URL.
- Custom scripts run only from `scripts/`, only with explicit confirm + logging.

## Current phase
Phase 1 through 11 — COMPLETE ✓

## Files that exist
```
app/__init__.py       — package marker
app/main.py           — FastAPI app, routers for cases & findings included
app/database.py       — SQLAlchemy engine, session, Base, init_db()
app/models.py         — Case & Finding models
app/encryption.py     — Fernet symmetric encryption layer
app/correlator.py     — Maigret username correlation logic
app/routes/cases.py   — routes for case management
app/routes/findings.py — routes for finding management
app/routes/images.py  — routes for image uploads and EXIF extraction
app/routes/relationships.py — routes for relationship mapper
app/routes/triage.py  — routes for LLM triage assistant
app/routes/exporter.py — routes for exporting case data (CSV, TXT)
app/routes/scripts.py — routes for running custom scripts
templates/index.html  — dark-themed landing page
templates/cases.html  — case list and creation UI
templates/case_detail.html — specific case and findings UI
static/style.css      — design system (CSS custom properties, dark mode)
data/.gitkeep         — placeholder (DB files gitignored)
data/images/          — directory for local image storage
scripts/.gitkeep      — placeholder for custom scripts (Phase 8)
scripts/encrypted_backup.py — creates an encrypted database backup
scripts/decrypt_backup.py — restores an encrypted database backup
scripts/encrypt_existing_db.py — migrates plaintext data to ciphertext
run_lodestar.bat      — Windows launcher script (Phase 10)
README.md             — documentation and quickstart (Phase 11)
docs/.gitkeep         — placeholder for documentation
docs/screenshot_home.png — UI screenshot for README
docs/screenshot_cases.png — UI screenshot for README
requirements.txt      — pinned deps (fastapi, uvicorn, sqlalchemy, jinja2, python-multipart, exifread, Pillow, maigret, httpx, cryptography)
.gitignore            — excludes .venv/, data/*.db, data/images/*, __pycache__/, lodestar.key
```

## Last session summary
Verified and completed Phase 11 (Polish & Documentation). Folded `DESIGN_AND_SCOPE.md` into a comprehensive `README.md` with a Quickstart guide. Pinned all dependencies in `requirements.txt` via pip freeze. Used Playwright headless testing to capture UI screenshots for the documentation. Lodestar is now fully documented and ready for a zero-config cold start on Windows.

## Next step
Project is complete! Any further phases will require updating the BUILD_PLAN.md.

## Known bugs / open questions
- Favicon 404 (cosmetic — no favicon.ico yet, will add in polish phase)
