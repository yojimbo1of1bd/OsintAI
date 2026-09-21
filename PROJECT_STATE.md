# Lodestar — Project State

*Paste this whole file at the start of every new Claude session. You generally don't need to paste `DESIGN_AND_SCOPE.md` or `BUILD_PLAN.md` too — reference them by name ("see BUILD_PLAN.md Phase N") and Claude can ask for a specific section if it actually needs one. Keeping this file short is what keeps each new session cheap.*

## One-liner
Windows-local, passive-OSINT case assistant for Trace-Labs-style missing-persons CTF work. Python + FastAPI + SQLite + local Ollama.

## Hard scope (full version in DESIGN_AND_SCOPE.md §2)
- Passive collection only. No contact, no auth/CAPTCHA bypass, no dark-web automation, no scraping ToS-restricted platforms.
- Every finding needs a source URL.
Phase 1 through 16 — COMPLETE ✓

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
app/routes/context.py — routes for case context intake (Phase 12)
app/routes/map.py     — routes for visual intelligence map (Phase 13)
app/routes/chat.py    — routes for interactive AI assistant (Phase 14)
app/routes/pipeline.py — routes for background auto-OSINT orchestration (Phase 15)
app/pipeline.py       — core auto-OSINT pipeline logic (Phase 15)
templates/index.html  — dark-themed landing page
templates/cases.html  — case list and creation UI
templates/case_detail.html — specific case and findings UI (updated w/ Pipeline modal)
templates/context_intake.html — form for seeding case context (Phase 12)
templates/case_map.html — visual intelligence map dashboard (Phase 13)
templates/case_chat.html — interactive LLM chat interface (Phase 14)
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
requirements.txt      — pinned deps (fastapi, uvicorn, sqlalchemy, jinja2, python-multipart, exifread, Pillow, maigret, httpx, cryptography, pytest)
.gitignore            — excludes .venv/, data/*.db, data/images/*, __pycache__/, lodestar.key
```

## Last session summary
Completed Phase 16 (Integration Polish & Tests). Added test suite (`pytest`), verified CRUD operations, edge cases, and pipeline behavior, and updated README with documentation and screenshots.

## Current Phase
**Current Phase:** Phase 16 complete. All phases in BUILD_PLAN.md are finished.
**Status:** The test suite is passing, the workflow UI has been updated to reflect the new pipeline/LLM assistant features, and the README has been updated. The full Lodestar framework is now operational.

## Known bugs / open questions
- Favicon 404 (cosmetic — no favicon.ico yet)
