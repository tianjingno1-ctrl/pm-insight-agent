# PM Insight Backend (Phase 2.2)

FastAPI **mock** backend for the pony-style roundtable UI.

**Stable SSE anchor**: commit `741c181` · tag **`phase-2.2-mock-sse-backend`**

## Scope

- `GET /health` — service status (`sse: "mock_stream"`)
- `GET /api/meetings/mock-stream` — mock SSE `MeetingEvent` stream
- **Demo LLM** (`scenario=llm`): OpenAI-compatible script generation with local fallback
- No database, no auth
- Not full multi-agent orchestration
- Does **not** import `roundtable/` or `app.py`
- Does **not** modify root `requirements.txt`

Mock data: `app/data/scenarios.py` (Python dicts), manually aligned with `frontend/lib/mockEvents.ts` and `mockScenarios.ts` — **drift risk**.

## Ports (dual-service local dev)

| Service  | Port | Command |
|----------|------|---------|
| Backend  | 8000 | `py -3.12 -m uvicorn app.main:app --reload --port 8000` |
| Frontend | 3000 | `cd ../frontend && npm run dev` |

CORS allows `http://localhost:3000` and `http://127.0.0.1:3000` only.

## Requirements

- Python **3.11+** (`requires-python` in `pyproject.toml`).
- On Windows, if `python` is 3.8, use **`py -3.12`** for all commands below.

## Setup

```powershell
cd backend
py -3.12 -m pip install -e ".[dev]"
```

## Run

```powershell
py -3.12 -m uvicorn app.main:app --reload --port 8000
```

### Demo LLM env (optional)

```powershell
$env:OPENAI_API_KEY="your-key"
$env:OPENAI_BASE_URL="https://api.openai.com/v1"
$env:OPENAI_MODEL="gpt-4o-mini"
py -3.12 -m uvicorn app.main:app --reload --port 8000
```

If `OPENAI_API_KEY` is unset or the LLM call fails, `scenario=llm` uses a **local fallback** script (still emits `meeting_done`).

```powershell
curl.exe -N "http://127.0.0.1:8000/api/meetings/mock-stream?scenario=llm&topic=AI%E4%BC%9A%E4%B8%8D%E4%BC%9A%E5%8F%96%E4%BB%A3%E4%BA%A7%E5%93%81%E7%BB%8F%E7%90%86&pace=4.0"
```

Scenarios: `default` | `concise` | `verbose` | `weak` | **`llm`** (with `topic` query).

## Verification checklist (Batch C / D)

### 1. Health

```powershell
curl.exe http://127.0.0.1:8000/health
```

Expected:

```json
{"status":"ok","service":"pm-insight-backend","phase":"2.2","sse":"mock_stream"}
```

If you see `"sse":"not_implemented"`, an **old** uvicorn process is still bound to port 8000 — stop it and restart (see Troubleshooting).

### 2. Mock SSE stream

```powershell
curl.exe -N "http://127.0.0.1:8000/api/meetings/mock-stream?scenario=default&pace=1.0"
```

Body should include (as JSON in `data:` lines):

- `"type":"meeting_started"` with `"protocolVersion":"1.0"` (**MeetingEvent contract version**, not project Phase 2.1)
- `"type":"speech"`
- `"type":"summary"` (object: `direction`, `disagreement`, `nextStep`)
- `"type":"meeting_done"`

Must **not** include: `event: speech`, top-level `"timestamp"`, top-level `"metadata"`.

### 3. Error branches

```powershell
curl.exe -i "http://127.0.0.1:8000/api/meetings/mock-stream?scenario=unknown"
curl.exe -i "http://127.0.0.1:8000/api/meetings/mock-stream?pace=0.1"
curl.exe -i "http://127.0.0.1:8000/api/meetings/mock-stream?pace=5"
```

| Query | HTTP |
|-------|------|
| `scenario=unknown` | **400** |
| `pace=0.1` or `pace=5` | **422** |

### 4. Scenarios

```powershell
curl.exe -N "http://127.0.0.1:8000/api/meetings/mock-stream?scenario=concise&pace=4.0"
curl.exe -N "http://127.0.0.1:8000/api/meetings/mock-stream?scenario=verbose&pace=4.0"
curl.exe -N "http://127.0.0.1:8000/api/meetings/mock-stream?scenario=weak&pace=4.0"
```

### 5. Tests

```powershell
py -3.12 -m pytest -v
```

Expected: **15 passed** (includes health, isolation, mock-stream).

## Mock SSE API reference

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

## Troubleshooting

### Port 8000 already in use (Windows)

Symptom: uvicorn fails with `[Errno 10048]`; curl hits old app (`sse: not_implemented`, mock-stream **404**).

```powershell
$pid = (Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue).OwningProcess
if ($pid) { Stop-Process -Id $pid -Force }
```

Then restart uvicorn from `backend/` with `py -3.12`.

### PowerShell `curl` alias

Use **`curl.exe`**, not `curl` (may invoke `Invoke-WebRequest`).

## Layout

```text
backend/app/
  models/meeting_event.py   # Pydantic output validator (extra=forbid)
  data/scenarios.py         # mock scripts
  services/mock_stream.py   # THIS IS A MOCK — no LLM here
  routers/meetings.py       # mock-stream endpoint
```

## Next (Phase 2.2)

- **Batch E**: frontend `useMeetingEventStream` (buffer until `meeting_done`, then `useMeetingPlayer`)
- **Batch F1**: `NEXT_PUBLIC_MEETING_SOURCE=mock|sse`

Frontend still uses `mockEvents` by default until Batch E/F1.
