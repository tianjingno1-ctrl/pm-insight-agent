import json
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.llm_meeting import (
    DEFAULT_TOPIC,
    fallback_demo_script,
    parse_llm_json,
    resolve_llm_meeting_events,
    script_to_meeting_events,
)

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


def test_parse_llm_json_plain() -> None:
    raw = json.dumps(
        {
            "title": "测试",
            "topic": "AI 测试",
            "messages": [
                {
                    "speakerId": "twilight",
                    "speakerName": "Twilight Sparkle",
                    "text": "第一句。",
                }
            ],
            "summary": {
                "keyPoints": ["a", "b", "c"],
                "decision": "决定",
                "risks": ["r1", "r2"],
            },
        }
    )
    script = parse_llm_json(raw)
    assert script.topic == "AI 测试"
    assert script.messages[0].text == "第一句。"


def test_parse_llm_json_fenced() -> None:
    inner = json.dumps(
        {
            "title": "围栏",
            "topic": "议题",
            "messages": [
                {"speakerId": "rainbow", "speakerName": "Rainbow", "text": "执行要快。"},
                {"speakerId": "rarity", "speakerName": "Rarity", "text": "体验要好。"},
                {"speakerId": "fluttershy", "speakerName": "Fluttershy", "text": "关注风险。"},
                {"speakerId": "twilight", "speakerName": "Twilight", "text": "收束。"},
            ],
            "summary": {"keyPoints": ["1"], "decision": "d", "risks": ["x"]},
        }
    )
    raw = f"```json\n{inner}\n```"
    script = parse_llm_json(raw)
    assert script.title == "围栏"
    assert len(script.messages) >= 4


def test_script_to_meeting_events_shape() -> None:
    topic = "AI会不会取代产品经理"
    script = fallback_demo_script(topic)
    events = script_to_meeting_events(script, topic)
    types = [e["type"] for e in events]

    assert types[0] == "meeting_started"
    assert types[-1] == "meeting_done"
    assert "summary" in types

    speeches = [e for e in events if e["type"] == "speech"]
    assert len(speeches) >= 6
    assert any("就位" in (e.get("text") or "") for e in speeches)
    assert any("议题" in (e.get("text") or "") for e in speeches)
    assert any(topic in (e.get("text") or "") for e in speeches)

    summary_events = [e for e in events if e["type"] == "summary"]
    assert summary_events[0]["summary"]["direction"]


@pytest.mark.asyncio
async def test_resolve_llm_without_api_key_uses_fallback() -> None:
    with patch("app.services.llm_meeting.OPENAI_API_KEY", ""):
        events = await resolve_llm_meeting_events("远程办公是否会降低团队创造力")
        assert events[-1]["type"] == "meeting_done"
        joined = "远程办公是否会降低团队创造力"
        assert any(joined in (e.get("text") or "") for e in events if e["type"] == "speech")


@pytest.mark.asyncio
async def test_resolve_llm_blank_topic_defaults() -> None:
    with patch("app.services.llm_meeting.OPENAI_API_KEY", ""):
        events = await resolve_llm_meeting_events("  ")
        assert events[-1]["type"] == "meeting_done"
        assert any(DEFAULT_TOPIC in (e.get("text") or "") for e in events if e["type"] == "speech")


def test_llm_scenario_sse_without_api_key() -> None:
    with patch("app.services.llm_meeting.OPENAI_API_KEY", ""):
        response = client.get(
            "/api/meetings/mock-stream",
            params={
                "scenario": "llm",
                "topic": "AI 会不会取代产品经理",
                "pace": 4.0,
            },
        )
    assert response.status_code == 200
    events = parse_sse_events(response.text)
    assert events[0]["type"] == "meeting_started"
    assert events[-1]["type"] == "meeting_done"
    assert any("AI 会不会取代产品经理" in (e.get("text") or "") for e in events)


def test_existing_scenarios_unchanged() -> None:
    for scenario in ("default", "concise", "verbose", "weak"):
        response = client.get(
            "/api/meetings/mock-stream",
            params={"scenario": scenario, "pace": 4.0},
        )
        assert response.status_code == 200
        events = parse_sse_events(response.text)
        assert events[0]["type"] == "meeting_started"
        assert events[-1]["type"] == "meeting_done"
