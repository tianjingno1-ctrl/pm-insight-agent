# PM Insight Backend (Phase 2.2)

FastAPI **mock** backend skeleton for the pony-style roundtable UI.

## Scope (Batch B)

- `GET /health` only
- No SSE, no LLM, no database, no auth
- Does **not** import `roundtable/` or `app.py` (Streamlit legacy)
- Does **not** modify root `requirements.txt` (use this package’s `pyproject.toml`)

**Batch C** will add:

```http
GET /api/meetings/mock-stream
```

## Ports

| Service   | Port |
|-----------|------|
| Backend   | 8000 |
| Frontend  | 3000 |

CORS allows `http://localhost:3000` and `http://127.0.0.1:3000` only.

## Requirements

- Python **3.11+** (see `requires-python` in `pyproject.toml`). On Windows, if `python` points to 3.8, use `py -3.12` below.

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

Example response:

```json
{
  "status": "ok",
  "service": "pm-insight-backend",
  "phase": "2.2",
  "sse": "not_implemented"
}
```

## Tests

```powershell
py -3.12 -m pytest
```
