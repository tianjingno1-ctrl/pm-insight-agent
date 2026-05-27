import json
import re

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.main import app
from app.models.meeting_event import validate_event_dict
from app.services.mock_stream import format_sse_data

client = TestClient(app)


def parse_sse_events(body: str) -> list[dict]:
    events: list[dict] = []
    for block in body.split("\n\n"):
        block = block.strip()
        if not block:
            continue
        assert block.startswith("data: ")
        events.append(json.loads(block[5:].strip()))
    return events


def test_format_sse_data_shape() -> None:
    frame = format_sse_data({"id": "x", "type": "speech", "text": "hi"})
    assert frame.startswith("data: ")
    assert frame.endswith("\n\n")
    assert " " not in frame.split("data: ", 1)[1].split("\n\n", 1)[0]


def test_mock_stream_default() -> None:
    response = client.get(
        "/api/meetings/mock-stream",
        params={"scenario": "default", "pace": 4.0},
    )
    assert response.status_code == 200
    assert "text/event-stream" in response.headers.get("content-type", "")
    body = response.text
    assert "meeting_started" in body
    assert "summary" in body
    assert "meeting_done" in body
    assert "event: speech" not in body

    events = parse_sse_events(body)
    assert events[0]["type"] == "meeting_started"
    assert events[-1]["type"] == "meeting_done"
    assert any(e["type"] == "speech" for e in events)


@pytest.mark.parametrize("scenario", ["concise", "verbose", "weak"])
def test_mock_stream_scenarios(scenario: str) -> None:
    response = client.get(
        "/api/meetings/mock-stream",
        params={"scenario": scenario, "pace": 4.0},
    )
    assert response.status_code == 200
    events = parse_sse_events(response.text)
    assert events[0]["type"] == "meeting_started"
    assert events[-1]["type"] == "meeting_done"


def test_unknown_scenario_400() -> None:
    response = client.get(
        "/api/meetings/mock-stream",
        params={"scenario": "unknown", "pace": 1.0},
    )
    assert response.status_code == 400


@pytest.mark.parametrize("pace", [0.1, 5.0])
def test_pace_out_of_range_422(pace: float) -> None:
    response = client.get(
        "/api/meetings/mock-stream",
        params={"scenario": "default", "pace": pace},
    )
    assert response.status_code == 422


def test_protocol_version_only_on_meeting_started() -> None:
    events = parse_sse_events(
        client.get(
            "/api/meetings/mock-stream",
            params={"scenario": "default", "pace": 4.0},
        ).text
    )
    with_version = [e for e in events if "protocolVersion" in e]
    assert len(with_version) == 1
    assert with_version[0]["type"] == "meeting_started"


def test_no_timestamp_or_metadata_fields() -> None:
    events = parse_sse_events(
        client.get(
            "/api/meetings/mock-stream",
            params={"scenario": "weak", "pace": 4.0},
        ).text
    )
    for event in events:
        assert "timestamp" not in event
        assert "metadata" not in event


def test_meeting_done_appears_once() -> None:
    events = parse_sse_events(
        client.get(
            "/api/meetings/mock-stream",
            params={"scenario": "default", "pace": 4.0},
        ).text
    )
    done_count = sum(1 for e in events if e["type"] == "meeting_done")
    assert done_count == 1


def test_pydantic_extra_forbid() -> None:
    with pytest.raises(ValidationError):
        validate_event_dict(
            {"id": "x", "type": "speech", "timestamp": "bad"},
        )
