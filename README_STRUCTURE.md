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

Phase: Pony Roundtable Frontend Mock

Rules:
1. Do not refactor `app.py`.
2. Do not refactor `roundtable/`.
3. Build the first visual prototype inside `frontend/`.
4. Use mock meeting events first.
5. Future backend must emit the same `MeetingEvent` structure defined in docs.
