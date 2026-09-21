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

### Phase 12 — Context Seeding & Case Intake Form
**Goal:** let the user front-load everything they already know about a subject into a structured intake, so downstream tools have something to work with immediately instead of starting from zero.
**Steps:**
1. Add a `CaseContext` model (new table `case_contexts`) with fields: `subject_name`, `known_aliases` (comma-separated), `age_range`, `last_known_location`, `last_seen_date`, `known_associates` (text), `social_handles` (text/JSON), `life_events` (text), `physical_description`, `additional_notes`. All encrypted at rest like other sensitive columns.
2. Create `app/routes/context.py` with routes: `GET /cases/{id}/context` (view/edit form), `POST /cases/{id}/context` (save/update).
3. Build `templates/context_intake.html` — a multi-section form (Identity, Location, Social Presence, Associates, Life Events) that saves to the new table.
4. Add a prominent "Seed Case Context" button on the case detail page header that links to the intake form.
5. When context is saved, auto-generate initial Findings from structured fields (e.g., each social handle → a "Basic Subject Info" finding with `verified=false`).

**Bug check:** fill out the intake form for a test case; restart the app; confirm all fields survive; confirm auto-generated findings appear in the case view.
**Done when:** a new case can be front-loaded with 10+ data points in under 2 minutes through the intake form, and those points are visible as unverified findings.
**Continue prompt:**
> Continuing Lodestar from PROJECT_STATE.md. Phase 12 (Context Seeding) is done. Starting Phase 13 (Visual Intelligence Map) per BUILD_PLAN.md.

---

### Phase 13 — Visual Intelligence Map
**Goal:** turn pooled case data into an interactive visual map — family trees, social-handle networks, last-seen locations on a real map, and a timeline of life events — so the investigator can see the whole picture at a glance.
**Steps:**
1. Build `templates/case_map.html` — a full-page visual dashboard for a single case, accessible via "View Case Map" button on the case detail page.
2. **Relationship graph (enhanced):** upgrade the existing vis-network graph to a full-page view with:
   - Node types: Subject (center, highlighted), Family, Friend, Associate, Unknown
   - Edge labels from the `relationships` table
   - Color-coded by relationship type
   - Click a node → sidebar shows all findings mentioning that person
3. **Location timeline:** if any findings or images have GPS/location data, plot them on a [Leaflet.js](https://leafletjs.com/) map (via CDN, no API key needed for OpenStreetMap tiles). Each pin shows the finding value, date, and source link.
4. **Event timeline:** render a vertical timeline (pure HTML/CSS, or vis-timeline via CDN) of key events pulled from `case_contexts.life_events` and chronological findings, sorted by date.
5. **Social handle grid:** a card grid showing each known handle, which platform it maps to (from correlator results), and whether it's verified.
6. Wire the map page into the main nav for each case.

**Bug check:** create a case with 3 relationships, 2 images with GPS, and 5 findings across different dates — the map page renders all three visualizations without errors.
**Done when:** the case map page shows a working relationship graph, a location map with pins, and a timeline — all populated from real case data.
**Continue prompt:**
> Continuing Lodestar from PROJECT_STATE.md. Phase 13 (Visual Intelligence Map) is done. Starting Phase 14 (Interactive LLM Assistant) per BUILD_PLAN.md.

---

### Phase 14 — Interactive LLM Assistant (qwen3:8b)
**Goal:** replace the one-shot triage report with a persistent, step-by-step chat assistant that can read the case data, guide the investigator through OSINT methodology, suggest next actions, and draft flag submissions — all via local Ollama (`qwen3:8b`).
**Steps:**
1. Create `app/routes/assistant.py` with:
   - `GET /cases/{id}/assistant` — renders the chat UI
   - `POST /cases/{id}/assistant/message` — accepts user message, builds prompt from case context + conversation history + case data, calls Ollama, returns the response
2. Build `templates/assistant.html` — a chat-style interface:
   - Message bubbles (user / assistant), auto-scroll
   - System prompt includes: all case findings, relationships, context data, and the Trace Labs category checklist
   - "Suggest Next Step" quick-action button that asks the LLM what to investigate next
   - "Draft Flag" button that asks the LLM to format a specific finding as a CTF flag submission
   - "Summarize Gaps" button that asks what categories are thin
3. Conversation history stored in-memory per session (not in DB — these are working notes, not evidence). Optionally save/export a conversation as a text file.
4. Model selector defaults to `qwen3:8b` but allows override (same pattern as existing triage).
5. Streaming support: use Ollama's streaming API (`"stream": true`) and Server-Sent Events (SSE) so the response types in real-time instead of waiting for the full generation.
6. Add a nav link to the assistant from the case detail page.

**Bug check:** open the assistant on a case with 10+ findings; ask it "what should I look into next?"; confirm the response references actual case data and doesn't hallucinate findings that don't exist; confirm streaming works (text appears incrementally).
**Done when:** the assistant can hold a multi-turn conversation, reference real case data in every response, and the three quick-action buttons all produce useful output.
**Continue prompt:**
> Continuing Lodestar from PROJECT_STATE.md. Phase 14 (Interactive LLM Assistant) is done. Starting Phase 15 (Auto-OSINT Pipeline) per BUILD_PLAN.md.

---

### Phase 15 — Auto-OSINT Pipeline
**Goal:** a single "Run Investigation" button that takes the seeded context and automatically orchestrates the existing tools — username correlator, image metadata, public-domain searches — feeding results back iteratively without manual intervention. The investigator reviews results afterward, not during.
**Steps:**
1. Create `app/pipeline.py` — the orchestration engine:
   - Takes a `case_id`, reads `CaseContext` for that case
   - **Step 1 — Username sweep:** for each handle in `social_handles`, run the Maigret correlator (reuse `app/correlator.py`). Results auto-saved as unverified findings.
   - **Step 2 — Public records enrichment:** for the subject name + any known aliases, construct manual-search URLs for public-domain sources (court records via PACER links, voter registration lookup pages, obituary indexes, Wayback Machine snapshots). Save these as findings with category "Advanced Subject Info" and `verified=false`.
   - **Step 3 — Image batch processing:** if any images already exist for the case, re-extract EXIF if not already done, generate all reverse-image-search URLs, and save them as findings.
   - **Step 4 — LLM synthesis:** call Ollama with the full updated case data and ask it to: summarize what the pipeline found, flag contradictions, suggest manual follow-ups.
   - Each step logs progress to a pipeline run log file (same `data/logs/` pattern as the script runner).
2. Create `app/routes/pipeline.py`:
   - `POST /cases/{id}/pipeline/run` — kicks off the pipeline as a background task
   - `GET /cases/{id}/pipeline/status` — returns current step / progress / log
3. Add a "▶ Run Investigation" button on the case detail page (only shown if context has been seeded and case is active). Requires confirm click per AGENTS.md rules.
4. Pipeline must respect case status — if the case is paused mid-pipeline, remaining steps are skipped.
5. **Safety rail:** the pipeline ONLY generates search URLs and runs the correlator. It never visits URLs, never scrapes, never contacts anyone. This is explicit in the code comments and the UI copy.

**Bug check:** seed a test case with 2 handles and a name; run the pipeline; confirm correlator results, generated search URLs, and LLM summary all appear as findings; pause the case mid-pipeline and confirm remaining steps are skipped.
**Done when:** the pipeline runs end-to-end on a seeded case, produces 20+ unverified findings from automated tools, and the LLM synthesis accurately summarizes what was found.
**Continue prompt:**
> Continuing Lodestar from PROJECT_STATE.md. Phase 15 (Auto-OSINT Pipeline) is done. Starting Phase 16 (Integration Polish & Tests) per BUILD_PLAN.md.

---

### Phase 16 — Integration Polish & Tests
**Goal:** make the new features (Phases 12–15) feel like a cohesive workflow, not bolted-on additions. Fix bugs surfaced during testing, add pytest coverage, update all documentation.
**Steps:**
1. **Workflow integration:** on the case detail page, add a clear visual workflow indicator: "1. Seed Context → 2. Run Investigation → 3. Review Map → 4. Chat with Assistant → 5. Export Flags."
2. **Bug fixes:** address any issues found during Phases 12–15 bug checks.
3. **Tests:** add pytest tests for:
   - Context model CRUD
   - Pipeline step ordering and case-pause interruption
   - Assistant prompt construction (verify it includes real data, doesn't exceed token limits)
   - Map data serialization (relationships → vis-network JSON, locations → Leaflet markers)
4. **README update:** add sections for the new features with screenshots (reuse the Playwright screenshot script).
5. **Dependency pinning:** freeze new dependencies.
6. **PROJECT_STATE.md:** update file manifest and completion status.

**Bug check:** fresh clone → `run_lodestar.bat` → create case → seed context → run pipeline → view map → chat with assistant → export → all work without errors.
**Done when:** the full workflow runs cold-start to export on a clean Windows machine, all new tests pass, and the README documents every feature.

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
