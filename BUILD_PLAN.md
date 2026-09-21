# Lodestar — Build Plan
### Phased, session-sized steps for building with Claude's free plan

## How to use this file

- One phase per sitting, roughly matching a day.
- At the end of a session, update `PROJECT_STATE.md` — what got built, what broke, what's next. Two or three lines is enough.
- At the start of the next session, paste `PROJECT_STATE.md` plus the Continue Prompt for your current phase (shown below each phase). You don't need to paste this whole file or `DESIGN_AND_SCOPE.md` again — say "see BUILD_PLAN.md Phase N" and Claude can ask for detail if it actually needs it.
- Don't move to the next phase until "Done when" is fully checked. Small verified steps compound. Unverified ones just accumulate bugs.

---

### Phase 0 — Environment & Skeleton
**Goal:** a project that runs and does nothing yet.
**Steps:**
1. Install Python 3.11+, install Ollama, pull one small model: `ollama pull qwen2.5:7b`.
2. `git init lodestar`; create `app/`, `data/`, `scripts/`, `docs/`.
3. venv + `pip install fastapi uvicorn sqlalchemy`.
4. One route that returns "Lodestar is running" at `127.0.0.1:8420`.

**Bug check:** `uvicorn app.main:app --reload` starts clean; the browser shows the message.
**Done when:** the above, committed to git.
**Continue prompt:**
> Continuing Lodestar from PROJECT_STATE.md. Phase 0 is done. Starting Phase 1 (Case Manager Core) per BUILD_PLAN.md.

---

### Phase 1 — Case Manager Core
**Goal:** create / list / pause / stop / delete a case, backed by SQLite.
**Steps:** `cases` table via SQLAlchemy; 4 routes; a minimal HTML page to exercise them (no styling needed yet).
**Bug check:** create two cases, pause one, restart the app, confirm status persisted.
**Done when:** all four operations work from the browser, not just curl.

---

### Phase 2 — Finding Logger
**Goal:** the core manual data-entry workflow.
**Steps:** `findings` table; a form for `{category, value, source_url, notes}`; a per-case list view; delete-single-finding.
**Bug check:** log 5 findings, delete 1, restart, confirm the other 4 survive.
**Done when:** logging a finding takes under 10 seconds through the UI.

---

### Phase 3 — Username Correlator
**Goal:** wrap Maigret (primary) and/or Sherlock, land results as unverified Findings.
**Steps:**
- `pip install maigret` (or the Windows EXE release if you want to skip the Python dependency chain).
- Call it as a library, not a subprocess, where possible — it's designed to be embedded.
- **Explicitly disable:** Tor/I2P scanning, `--ai` (defaults to OpenAI cloud), and any Cloudflare-bypass option. Default clear-web scan only.
- Results land as `verified = false` Findings — never auto-marked true, you check each one.

**Bug check:** run against a throwaway handle you own; confirm pausing the case actually stops a long scan mid-run, not just the display.

---

### Phase 4 — Image Importer
**Goal:** drag-and-drop images, pull EXIF/GPS/timestamp.
**Steps:** upload route; `exifread` / Pillow metadata extraction; manual source-URL field; generate (don't auto-run) reverse-image-search links.
**Bug check:** an image with GPS EXIF renders coordinates correctly; an image with none doesn't crash the importer.

---

### Phase 5 — Relationship Mapper
**Goal:** log `X is [relation] of Y, source: url` and see it as a simple graph.
**Steps:** `relationships` table; entry form with a **required** (not optional) source_url; a simple list view first, a real graph render (vis-network via CDN, or Maigret's `--neo4j` export if you want a proper graph DB) once the list view works.
**Bug check:** a 5-person mini-tree renders; every edge has a source.

---

### Phase 6 — LLM Triage Assistant
**Goal:** a local Ollama call that summarizes a case and flags thin categories.
**Steps:** REST call to `localhost:11434/api/generate`; prompt template scoped to *that case's* findings only; output shown for review, never auto-saved as a finding.
**Bug check:** run it on a 3-finding case and a 30-finding case — both complete, and the summary only references findings that actually exist (no invented details).

---

### Phase 7 — Exporter
**Goal:** the flag-submission format.
**Steps:** route that dumps `{category, value, source_url, explanation}` per finding to CSV and plain text.
**Bug check:** export rejects (or flags) any finding missing a source URL.

---

### Phase 8 — Custom Script Runner
**Goal:** your own scripts, run with explicit confirmation and full logging.
**Steps:** scripts only launch from a fixed `scripts/` folder; UI lists what's there; running requires a confirm click; stdout/stderr piped to a per-run log; case-status check before allowing a run.
**Bug check:** a trivial test script won't run without the confirm click; its output shows up in the log file.

---

### Phase 9 — Encryption & Leak-Proofing
**Goal:** the raw `.db` file is useless if copied elsewhere.
**Steps:** SQLCipher (or Fernet on sensitive columns if SQLCipher's Windows build is a hassle); confirm the server binds to `127.0.0.1` only, never `0.0.0.0`; encrypted backup/export command; secure delete for a single finding or a whole case.
**Bug check:** copy the raw db file to another machine — unreadable without your key.

---

### Phase 10 — Windows Packaging
**Goal:** something that isn't "open a terminal every time."
**Steps:** a `.bat` launcher that activates the venv and opens the browser tab; PyInstaller for a single-file exe once everything else is stable (optional).
**Bug check:** double-click the `.bat` on a clean checkout — it starts with no manual venv activation.

---

### Phase 11 — Polish & Documentation
**Goal:** a README your future self (or a teammate) can actually follow.
**Steps:** fold `DESIGN_AND_SCOPE.md` into a proper `README.md`; add a Quickstart section; screenshot the UI; pin every dependency version.
**Done when:** someone with a clean Windows machine can go from zero to a running case using only the README.

---

## Appendix: reusable phase template

If you add your own phases later, keep the same shape:

```
### Phase N — <name>
Goal:
Steps:
Bug check:
Done when:
Continue prompt:
```
