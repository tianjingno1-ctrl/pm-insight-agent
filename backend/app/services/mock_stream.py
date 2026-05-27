# THIS IS A MOCK STREAM SERVICE.
# Do not add real LLM orchestration here.
# Future real orchestration must live in a separate service module.

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from typing import Any

from pydantic import ValidationError

from app.data.scenarios import LLM_SCENARIO, get_scenario_events
from app.models.meeting_event import validate_event_dict
from app.services.llm_meeting import resolve_llm_meeting_events


def format_sse_data(payload: dict[str, Any]) -> str:
    compact = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    return f"data: {compact}\n\n"


def calculate_delay_seconds(event: dict[str, Any], pace: float) -> float:
    if pace <= 0:
        return 0.0
    delay_ms = event.get("delay_before_ms") or 0
    effective_delay_ms = delay_ms / pace
    return max(0.0, effective_delay_ms / 1000.0)


def _error_frame(code: str, message: str, recoverable: bool = False) -> str:
    payload = validate_event_dict(
        {
            "id": "mock-stream-error",
            "type": "error",
            "errorInfo": {
                "code": code,
                "message": message,
                "recoverable": recoverable,
            },
        }
    )
    return format_sse_data(payload)


async def generate_mock_sse_frames(
    scenario: str,
    pace: float,
    topic: str | None = None,
) -> AsyncIterator[str]:
    try:
        if scenario == LLM_SCENARIO:
            events = await resolve_llm_meeting_events(topic)
        else:
            events = get_scenario_events(scenario)
        for event in events:
            await asyncio.sleep(calculate_delay_seconds(event, pace))
            validated = validate_event_dict(event)
            yield format_sse_data(validated)
    except ValidationError as exc:
        yield _error_frame("validation_error", str(exc), recoverable=False)
    except Exception as exc:  # noqa: BLE001 — mock stream must not crash the response
        yield _error_frame("mock_stream_error", str(exc), recoverable=False)
