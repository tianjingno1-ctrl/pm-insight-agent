# Project Structure Rules

This repository is evolving from a Streamlit prototype into a pony-style AI roundtable product.

## Directory Ownership

| Directory | Purpose | Change Rule |
|---|---|---|
| `app.py` | Legacy Streamlit prototype UI | Only bugfixes before backend migration |
| `roundtable/` | Existing Python roundtable logic | Keep stable; reuse later in backend |
| `frontend/` | New pony-style roundtable UI | Main development area in `experiment/pony-roundtable-ui` |
| `backend/` | Future FastAPI backend | Not created in Phase 1 frontend mock |
| `docs/` | Product and protocol specs | Can be updated freely |

## Current Phase

Phase: Pony Roundtable — **2.1a / 2.1b** (frontend) + contract docs

Rules:
1. Do not refactor `app.py` (Streamlit **freeze**: bugfix only on `main`).
2. Do not refactor `roundtable/` until Phase 2.3 adapter work.
3. Build UI inside `frontend/`; playback stays in `useMeetingPlayer` (or SSE variant).
4. Use mock meeting events first; optional fields in `MeetingEvent` are not required in mock yet.
5. Event protocol source of truth: `docs/meeting-event-spec.md` (`protocolVersion` defaults to `"1.0"`).
6. Do not create `backend/` until **Phase 2.2** (FastAPI/SSE mock).
