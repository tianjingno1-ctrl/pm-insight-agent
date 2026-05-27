# frontend/lib/types.ts is the current source of truth for MeetingEvent.
# This backend model is a local output validator for Phase 2.2 mock SSE only.
# Keep it manually synchronized with docs/meeting-event-spec.md.

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict

MeetingEventType = Literal[
    "meeting_started",
    "speech",
    "reaction",
    "summary",
    "meeting_done",
    "error",
]


class MeetingSummaryPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    direction: str
    disagreement: str
    nextStep: str


class MeetingEvent(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    id: str
    type: MeetingEventType

    speakerId: str | None = None
    targetId: str | None = None
    emotion: str | None = None
    action: str | None = None
    text: str | None = None
    duration_ms: int | None = None
    delay_before_ms: int | None = None
    summary: MeetingSummaryPayload | None = None
    stage: str | None = None
    intensity: int | None = None
    turnIndex: int | None = None
    roundIndex: int | None = None
    protocolVersion: str | None = None
    uiHint: dict[str, Any] | None = None
    errorInfo: dict[str, Any] | None = None


def validate_event_dict(event: dict[str, Any]) -> dict[str, Any]:
    return MeetingEvent.model_validate(event).model_dump(exclude_none=True)
