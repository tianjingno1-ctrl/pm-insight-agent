from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from app.config import API_PREFIX
from app.data.scenarios import SUPPORTED_SCENARIOS
from app.services.mock_stream import generate_mock_sse_frames

router = APIRouter(prefix=f"{API_PREFIX}/meetings", tags=["meetings"])

PACE_MIN = 0.25
PACE_MAX = 4.0


@router.get("/mock-stream")
async def mock_meeting_stream(
    scenario: str = Query(default="default"),
    pace: float = Query(default=1.0),
    topic: str | None = Query(default=None),
) -> StreamingResponse:
    if scenario not in SUPPORTED_SCENARIOS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown scenario {scenario!r}. Supported: {sorted(SUPPORTED_SCENARIOS)}",
        )
    if pace < PACE_MIN or pace > PACE_MAX:
        raise HTTPException(
            status_code=422,
            detail=f"pace must be between {PACE_MIN} and {PACE_MAX}, got {pace}",
        )

    return StreamingResponse(
        generate_mock_sse_frames(scenario, pace, topic=topic),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
