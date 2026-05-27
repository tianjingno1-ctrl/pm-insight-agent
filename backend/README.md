# PM Insight Backend (Phase 2.2)

FastAPI **mock** backend for the pony-style roundtable UI.

## Scope

- `GET /health` — service status
- `GET /api/meetings/mock-stream` — mock SSE `MeetingEvent` stream (Batch C)
- No real LLM, no database, no auth
- Does **not** import `roundtable/` or `app.py`
- Does **not** modify root `requirements.txt`

Mock data lives in `app/data/scenarios.py` (Python dicts). Manually aligned with `frontend/lib/mockEvents.ts` and `mockScenarios.ts` — **drift risk** if TS changes without sync.

## Ports

| Service   | Port |
|-----------|------|
| Backend   | 8000 |
| Frontend  | 3000 |

CORS: `http://localhost:3000`, `http://127.0.0.1:3000` only.

## Requirements

- Python **3.11+**. On Windows, if default `python` is 3.8, use `py -3.12` below.

## Setup

```powershell
cd backend
py -3.12 -m pip install -e ".[dev]"
```

## Run

```powershell
py -3.12 -m uvicorn app.main:app --reload --port 8000
```

## Health check

```powershell
curl.exe http://127.0.0.1:8000/health
```

## Mock SSE stream (Batch C)

```http
GET /api/meetings/mock-stream?scenario=default&pace=1.0
```

| Query | Values | Notes |
|-------|--------|-------|
| `scenario` | `default`, `concise`, `verbose`, `weak` | Unknown → HTTP **400** |
| `pace` | `0.25` … `4.0` | Higher = faster; out of range → HTTP **422** |

Response: `text/event-stream`. Each frame:

```text
data: {"id":"...","type":"speech",...}

```

- No custom SSE `event:` types — business type is JSON `type` only.
- Stream order: `meeting_started` → `speech`/`reaction`… → `summary` → `meeting_done` → close.
- `protocolVersion` only on `meeting_started` (currently `"1.0"`).

### curl examples

```powershell
curl.exe -N "http://127.0.0.1:8000/api/meetings/mock-stream?scenario=default&pace=1.0"
curl.exe -N "http://127.0.0.1:8000/api/meetings/mock-stream?scenario=concise&pace=2.0"
curl.exe -i "http://127.0.0.1:8000/api/meetings/mock-stream?scenario=unknown"
```

## Tests

```powershell
py -3.12 -m pytest
```

## Layout

```text
backend/app/
  models/meeting_event.py   # Pydantic output validator (extra=forbid)
  data/scenarios.py         # mock scripts
  services/mock_stream.py   # THIS IS A MOCK — no LLM here
  routers/meetings.py       # mock-stream endpoint
```
