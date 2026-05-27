from fastapi import APIRouter

from app.config import PHASE, SERVICE_NAME

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "service": SERVICE_NAME,
        "phase": PHASE,
        "sse": "mock_stream",
    }
