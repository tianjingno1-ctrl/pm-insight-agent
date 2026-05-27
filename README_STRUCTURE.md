# Project Structure Rules

This repository is evolving from a Streamlit prototype into a pony-style AI roundtable product.

## Git anchors (experiment branch)

| Anchor | Commit | Meaning |
|--------|--------|---------|
| Phase 2.1 feature acceptance | `3360287` | tag `phase-2.1-pony-ui-accepted` |
| Phase 2.1 UI polish | `95fa3d6` | tag `phase-2.1-pony-ui-polish` |
| Docs handoff (Batch D) | `525cc93` | Phase 2.1 documented; **do not move** acceptance tags |

## Directory Ownership

| Directory | Purpose | Change Rule |
|---|---|---|
| `app.py` | Legacy Streamlit prototype UI | **Phase 2.2:** bugfix only; no API/SSE |
| `roundtable/` | Existing Python roundtable logic | **Phase 2.2:** no changes; no SSE; reuse from Phase 2.3+ |
| `frontend/` | Pony-style roundtable UI | Main UI area; mock + future SSE client |
| `backend/` | FastAPI mock SSE service | **Created in Phase 2.2 Batch B+** (not Batch A docs-only) |
| `docs/` | Product and protocol specs | Updated freely |
| `api/` (top-level) | — | **Not used** as service directory in Phase 2.2 |

## Current Phase

**Phase 2.2** — FastAPI/SSE **mock** backend (architecture decided in Batch A docs; code in Batch B–F).

**Phase 2.1** — **Done** (frontend mock, MeetingPlayer, UI polish, local acceptance @ `3360287`).

### Phase 2.2 rules

1. **New `backend/`** as an isolated FastAPI app; **not** `api/` at repo root.
2. **Do not** add API/SSE to `app.py` or `roundtable/`.
3. **Do not** use Next.js API routes as the primary SSE backend for Phase 2.2.
4. `backend/` must **not** `import` `roundtable/` or `app.py` in Phase 2.2.
5. Root `requirements.txt` stays for legacy Streamlit/agent; backend uses **`backend/pyproject.toml`**.
6. Frontend keeps `mockEvents` as fallback/demo; playback stays in **`useMeetingPlayer`**.
7. SSE ingestion uses a **new** hook **`useMeetingEventStream`** (not a replacement player hook).
8. Event contract: `frontend/lib/types.ts` (code) + `docs/meeting-event-spec.md` (docs); backend Pydantic is local to `backend/`.

### Planned `backend/` layout (Batch B/C — not created in Batch A)

```text
backend/
  pyproject.toml
  README.md
  app/
    __init__.py
    main.py
    config.py
    routers/
      __init__.py
      health.py
      meetings.py
    models/
      meeting_event.py
    services/
      mock_stream.py
    data/
      scenarios.py
  tests/
    test_mock_stream.py
```

## Phase 2.1 rules (historical)

1. Do not refactor `app.py` (Streamlit **freeze** on `main`).
2. Do not refactor `roundtable/` until Phase 2.3 adapter work.
3. Event protocol: `docs/meeting-event-spec.md` (`protocolVersion` defaults to `"1.0"` when omitted).
