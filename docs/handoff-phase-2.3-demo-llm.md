# Phase 2.3 Demo LLM Handoff

## Commit

```text
57c75ac feat(demo): add LLM-generated meeting script over SSE
```

## Status

Phase 2.3-Demo-LLM implemented and pushed.

Checks passed:

- Backend pytest: 22 passed
- Frontend build: passed
- Frontend lint: passed
- Fallback SSE: verified
- Working tree: clean

## Demo Architecture

```text
Topic
→ Backend LLM/fallback meeting script
→ MeetingEvent list
→ SSE mock-stream endpoint
→ Frontend buffered playback
```

Current demo mode:

- Not multi-agent orchestration
- Not token-level streaming
- Not live incremental playback
- Generates full meeting script first, then plays via SSE

## Backend Start

### Real LLM

```powershell
cd backend
$env:OPENAI_API_KEY="your key"
$env:OPENAI_BASE_URL="https://api.openai.com/v1"
$env:OPENAI_MODEL="gpt-4o-mini"
py -3.12 -m uvicorn app.main:app --reload --port 8000
```

### Fallback

```powershell
cd backend
Remove-Item Env:OPENAI_API_KEY -ErrorAction SilentlyContinue
py -3.12 -m uvicorn app.main:app --reload --port 8000
```

## Frontend Start

```powershell
cd frontend
$env:NEXT_PUBLIC_MEETING_SOURCE="sse"
$env:NEXT_PUBLIC_MEETING_SCENARIO="llm"
$env:NEXT_PUBLIC_MEETING_TOPIC="AI会不会取代产品经理"
$env:NEXT_PUBLIC_MEETING_PACE="4.0"
npm run dev
```

Open:

```text
http://localhost:3000
```

## Quick Verification

```powershell
curl.exe http://127.0.0.1:8000/health
```

```powershell
curl.exe -N "http://127.0.0.1:8000/api/meetings/mock-stream?scenario=llm&topic=AI%E4%BC%9A%E4%B8%8D%E4%BC%9A%E5%8F%96%E4%BB%A3%E4%BA%A7%E5%93%81%E7%BB%8F%E7%90%86&pace=4.0"
```

Expected:

```text
meeting_started
speech
summary
meeting_done
```

## Frontend Expected Result

- Page loads without crash
- SSE connects to backend
- Meeting buffers until done
- Roundtable playback starts
- Content includes: AI会不会取代产品经理

## Fallback Behavior

If `OPENAI_API_KEY` is missing or LLM request fails:

- Backend uses local fallback script
- Still returns SSE events
- Still emits `meeting_done`
- Frontend demo still works

## Demo Topics

- AI 会不会取代产品经理
- 创业公司应该先追求增长还是利润
- 远程办公是否会降低团队创造力
- AI 圆桌会议能不能提升团队决策质量

## Demo Talk Track

```text
这是一个真实大模型驱动的 AI 圆桌会议原型。系统根据议题生成多角色讨论，再转换成标准会议事件，通过 SSE 推给前端播放。当前为了演示稳定，采用先生成完整会议、再事件流播放的方式。
```

## Known Limitations

- Demo uses one LLM generation call, not true multi-agent orchestration
- Demo is not token streaming
- Frontend role slots still reuse Phase 2.1 expert layout
- Backend maps generated script into existing playable event shape
- Changing NEXT_PUBLIC_* env requires restarting frontend dev server
