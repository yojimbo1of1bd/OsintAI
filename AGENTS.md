# AGENTS.md — Project Rules for AI Coding Agents
# Read automatically by Antigravity (v1.20.3+) at session start.
# Applies to every task in this repo unless a nested AGENTS.md overrides
# it for a specific subfolder.

## Project Overview
- Name: Lodestar
- Type: Windows-local web app (FastAPI backend + browser UI)
- Purpose: passive-OSINT case assistant for Trace-Labs-style missing-persons CTF work
- Stage: early build — working through BUILD_PLAN.md phase by phase, one phase per session
- Full design rationale lives in DESIGN_AND_SCOPE.md in this repo. If something here seems to conflict with a detail not shown in this file, ask rather than guessing.

## Tech Stack
- Language: Python 3.11+
- Backend: FastAPI + Uvicorn
- Database: SQLite, encrypted at rest (SQLCipher, or Fernet on sensitive columns as a fallback)
- Frontend: plain HTML/JS, no build step, no framework
- Local LLM: Ollama (model-agnostic — qwen2.5, llama3.1, whatever's configured), called via the local REST API only
- No cloud AI APIs. No telemetry. No analytics.

## Safety Guardrails — read before writing any code
This project has hard scope limits that exist for legal and safety reasons, not style preference. Don't work around them even if a task seems to call for it, and don't add a feature that crosses one without flagging the boundary itself first.

Never, under any circumstance:
- write code that logs in as, impersonates, messages, friends, follows, or otherwise contacts a subject, their family, or their friends on any platform
- write code that bypasses authentication, CAPTCHAs, paywalls, or rate limits
- write a scraper for a platform whose ToS prohibits automated collection (Facebook, LinkedIn, Instagram) — build a manual-import form instead
- enable or wire up Tor/I2P scanning or Cloudflare-bypass options in a username-correlation library, even if the library itself supports them
- send case data to any cloud API (OpenAI, Anthropic, Google, etc.) — all AI calls go to localhost Ollama only
- generate pretext text, fake profile content, or persuasive messages aimed at a real person

Always stop and confirm with the human before:
- starting a new Phase from BUILD_PLAN.md (finish the current one's "Done when" checklist first)
- changing the database schema
- adding a new third-party dependency
- running anything from the `scripts/` folder
- deleting a file, a finding, or a case

## Code Quality
- One module per feature area (`case_manager.py`, `findings.py`, `correlator.py`, etc.) — don't collapse everything into one file
- Every route that touches the database wraps its work in try/except with a real error message, not a bare `pass`
- No `print()` for anything that matters — use `logging`
- Every DB-touching function takes an explicit `case_id` — nothing should be able to operate across cases by accident

## Testing
- Each phase in BUILD_PLAN.md lists a manual "Bug check" — run it before marking the phase done
- Add a pytest for anything that isn't obviously correct by inspection (parsing, scoring, exports)

## Git Conventions
- Commit at the end of each completed phase: `phase N: <what got built>`
- Don't force-push
- `data/` (the actual case database) is gitignored — never commit real case data

## Communication
- Work one Phase at a time, in the order BUILD_PLAN.md lists them, unless told otherwise
- When a Phase's "Done when" is met, stop and say so — don't auto-continue into the next phase
- If a BUILD_PLAN.md step is unclear, or a library's real API doesn't match what the plan assumed, ask rather than improvising around it silently
- If you notice a way the plan as written would cross a Safety Guardrail above, flag it before writing the code, not after
