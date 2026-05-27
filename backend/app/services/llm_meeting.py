"""Demo LLM meeting script generation (Phase 2.3-Demo-LLM).

Generates a full meeting script via OpenAI-compatible API, or local fallback.
Output is converted to existing MeetingEvent dicts — no contract changes.
"""

from __future__ import annotations

import json
import logging
import re
import uuid
from typing import Any

import httpx
from pydantic import BaseModel, Field, ValidationError

from app.config import OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL

logger = logging.getLogger(__name__)

DEFAULT_TOPIC = "AI 如何改变团队协作"
LLM_SCENARIO_KEY = "llm"

SPEAKER_TO_AGENT: dict[str, str] = {
    "twilight": "host",
    "rainbow": "growth",
    "rarity": "product",
    "fluttershy": "tech",
    "host": "host",
    "product": "product",
    "tech": "tech",
    "growth": "growth",
}

PONY_ROSTER: list[tuple[str, str, str]] = [
    ("twilight", "Twilight Sparkle", "host"),
    ("rainbow", "Rainbow Dash", "growth"),
    ("rarity", "Rarity", "product"),
    ("fluttershy", "Fluttershy", "tech"),
]

SPEECH_EMOTIONS = ("thinking", "excited", "worried", "neutral", "happy")
SPEECH_ACTIONS = ("open", "suggest", "challenge", "support", "summarize")

_SYSTEM_PROMPT = """你是小马AI风格圆桌会议编剧。根据用户议题，编写一场四角色中文圆桌讨论脚本。
角色与职责：
- Twilight Sparkle（speakerId: twilight）：战略、结构、证据
- Rainbow Dash（speakerId: rainbow）：速度、执行、大胆判断
- Rarity（speakerId: rarity）：用户体验、品质、产品打磨
- Fluttershy（speakerId: fluttershy）：人群影响、风险、伦理

只输出一个 JSON 对象，不要 Markdown，不要解释，不要代码块。
JSON 结构：
{
  "title": "string",
  "topic": "string",
  "messages": [
    {"speakerId": "twilight|rainbow|rarity|fluttershy", "speakerName": "string", "text": "string"}
  ],
  "summary": {
    "keyPoints": ["string", "string", "string"],
    "decision": "string",
    "risks": ["string", "string"]
  }
}
约束：messages 6-10 条；每条 1-3 句话；明显围绕 topic；中文。"""


class LlmMessage(BaseModel):
    speakerId: str = "twilight"
    speakerName: str = ""
    text: str = ""


class LlmSummary(BaseModel):
    keyPoints: list[str] = Field(default_factory=list)
    decision: str = ""
    risks: list[str] = Field(default_factory=list)


class LlmMeetingScript(BaseModel):
    title: str = "小马 AI 圆桌"
    topic: str = DEFAULT_TOPIC
    messages: list[LlmMessage] = Field(default_factory=list)
    summary: LlmSummary = Field(default_factory=LlmSummary)


def normalize_topic(topic: str | None) -> str:
    cleaned = (topic or "").strip()
    return cleaned if cleaned else DEFAULT_TOPIC


def _strip_json_fences(raw: str) -> str:
    text = raw.strip()
    fence = re.match(r"^```(?:json)?\s*([\s\S]*?)\s*```$", text, re.IGNORECASE)
    if fence:
        return fence.group(1).strip()
    return text


def parse_llm_json(raw_text: str) -> LlmMeetingScript:
    """Parse LLM JSON; tolerate ```json fences and fill defaults for missing fields."""
    payload = json.loads(_strip_json_fences(raw_text))
    if not isinstance(payload, dict):
        raise ValueError("LLM output is not a JSON object")

    messages_raw = payload.get("messages") or []
    messages: list[LlmMessage] = []
    if isinstance(messages_raw, list):
        for item in messages_raw:
            if not isinstance(item, dict):
                continue
            messages.append(
                LlmMessage(
                    speakerId=str(item.get("speakerId") or "twilight"),
                    speakerName=str(item.get("speakerName") or ""),
                    text=str(item.get("text") or "").strip(),
                )
            )

    summary_raw = payload.get("summary") or {}
    summary = LlmSummary()
    if isinstance(summary_raw, dict):
        kp = summary_raw.get("keyPoints") or []
        if isinstance(kp, list):
            summary.keyPoints = [str(x) for x in kp if str(x).strip()][:5]
        summary.decision = str(summary_raw.get("decision") or "").strip()
        risks = summary_raw.get("risks") or []
        if isinstance(risks, list):
            summary.risks = [str(x) for x in risks if str(x).strip()][:5]

    return LlmMeetingScript(
        title=str(payload.get("title") or "小马 AI 圆桌").strip(),
        topic=str(payload.get("topic") or DEFAULT_TOPIC).strip(),
        messages=[m for m in messages if m.text],
        summary=summary,
    )


def fallback_demo_script(topic: str) -> LlmMeetingScript:
    """Stable local demo script centered on topic (no external API)."""
    t = normalize_topic(topic)
    return LlmMeetingScript(
        title=f"关于「{t}」的小马圆桌",
        topic=t,
        messages=[
            LlmMessage(
                speakerId="twilight",
                speakerName="Twilight Sparkle",
                text=f"我们先框定议题：{t}。我会从目标、约束和可验证假设三条线拆开。",
            ),
            LlmMessage(
                speakerId="rainbow",
                speakerName="Rainbow Dash",
                text=f"别分析太久。围绕「{t}」，两周内必须有一个能演示、能收集反馈的最小版本。",
            ),
            LlmMessage(
                speakerId="rarity",
                speakerName="Rarity",
                text="速度重要，但体验不能塌。第一版界面要让人愿意继续聊，而不是看完就走。",
            ),
            LlmMessage(
                speakerId="fluttershy",
                speakerName="Fluttershy",
                text=f"也请想想人和团队：{t} 若推进太快，会不会让一线同学失去掌控感？",
            ),
            LlmMessage(
                speakerId="rainbow",
                speakerName="Rainbow Dash",
                text="同意补一层风险检查。我们并行：一条线做 demo，一条线做 5 人用户访谈。",
            ),
            LlmMessage(
                speakerId="twilight",
                speakerName="Twilight Sparkle",
                text=f"收束：{t} 的 MVP 先验证「是否值得继续投入」，再谈全面铺开。",
            ),
        ],
        summary=LlmSummary(
            keyPoints=[
                f"议题「{t}」先定义可演示 MVP",
                "两周内并行 demo 与小样本访谈",
                "体验与速度需要同时约束",
            ],
            decision=f"先以最小可演示方案验证「{t}」的核心假设，再扩展范围。",
            risks=[
                "范围膨胀导致两周内无法交付",
                "忽视使用者感受造成采纳率低",
            ],
        ),
    )


def _estimate_duration_ms(text: str) -> int:
    return min(4500, max(2200, len(text) * 45))


def _map_speaker_id(raw: str) -> str:
    key = raw.strip().lower()
    return SPEAKER_TO_AGENT.get(key, "host")


def script_to_meeting_events(script: LlmMeetingScript, topic: str) -> list[dict[str, Any]]:
    """Convert script to MeetingEvent dicts (contract-safe types only)."""
    resolved_topic = normalize_topic(script.topic or topic)
    events: list[dict[str, Any]] = [
        {
            "id": f"llm-start-{uuid.uuid4().hex[:8]}",
            "type": "meeting_started",
            "protocolVersion": "1.0",
            "delay_before_ms": 0,
        }
    ]

    # agent_joined → host announcement speeches
    for idx, (_sid, display_name, _agent) in enumerate(PONY_ROSTER):
        events.append(
            {
                "id": f"llm-join-{idx}",
                "type": "speech",
                "speakerId": "host",
                "emotion": "happy",
                "action": "open",
                "text": f"{display_name} 加入了圆桌。",
                "delay_before_ms": 0,
                "duration_ms": 1600,
            }
        )

    # topic_introduced → host speech
    events.append(
        {
            "id": "llm-topic-intro",
            "type": "speech",
            "speakerId": "host",
            "emotion": "thinking",
            "action": "open",
            "text": f"今天的议题是：{resolved_topic}。{script.title}",
            "delay_before_ms": 0,
            "duration_ms": 2800,
        }
    )

    # messages → speech
    for idx, msg in enumerate(script.messages):
        agent_id = _map_speaker_id(msg.speakerId)
        events.append(
            {
                "id": f"llm-msg-{idx}",
                "type": "speech",
                "speakerId": agent_id,
                "emotion": SPEECH_EMOTIONS[idx % len(SPEECH_EMOTIONS)],
                "action": SPEECH_ACTIONS[idx % len(SPEECH_ACTIONS)],
                "text": msg.text,
                "delay_before_ms": 0,
                "duration_ms": _estimate_duration_ms(msg.text),
            }
        )

    summary = script.summary
    key_points = summary.keyPoints or [resolved_topic]
    risks = summary.risks or ["需要更多验证"]
    events.append(
        {
            "id": "llm-summary",
            "type": "summary",
            "summary": {
                "direction": summary.decision or key_points[0],
                "disagreement": "；".join(risks),
                "nextStep": "；".join(key_points[:3]),
            },
            "delay_before_ms": 0,
        }
    )

    events.append(
        {
            "id": f"llm-done-{uuid.uuid4().hex[:8]}",
            "type": "meeting_done",
            "delay_before_ms": 0,
        }
    )
    return events


async def generate_llm_meeting_script(topic: str) -> LlmMeetingScript:
    """Call OpenAI-compatible chat completions; raises on failure."""
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not set")

    user_prompt = f"议题 topic：{normalize_topic(topic)}\n请生成完整 JSON 脚本。"
    url = f"{OPENAI_BASE_URL}/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    body: dict[str, Any] = {
        "model": OPENAI_MODEL,
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.7,
        "response_format": {"type": "json_object"},
    }

    async with httpx.AsyncClient(timeout=90.0) as client:
        try:
            response = await client.post(url, headers=headers, json=body)
            response.raise_for_status()
        except httpx.HTTPStatusError:
            # Some compatible APIs reject response_format
            body.pop("response_format", None)
            response = await client.post(url, headers=headers, json=body)
            response.raise_for_status()

    data = response.json()
    choices = data.get("choices") or []
    if not choices:
        raise ValueError("LLM response has no choices")
    content = choices[0].get("message", {}).get("content")
    if not isinstance(content, str) or not content.strip():
        raise ValueError("LLM response content is empty")
    script = parse_llm_json(content)
    if len(script.messages) < 4:
        raise ValueError("LLM script has too few messages")
    return script


async def resolve_llm_meeting_events(topic: str | None) -> list[dict[str, Any]]:
    """Try LLM script; on missing key or any failure, use fallback. Always returns events."""
    resolved_topic = normalize_topic(topic)
    script: LlmMeetingScript | None = None

    if OPENAI_API_KEY:
        try:
            script = await generate_llm_meeting_script(resolved_topic)
            logger.info("LLM meeting script generated for topic=%r", resolved_topic)
        except (httpx.HTTPError, json.JSONDecodeError, ValidationError, ValueError) as exc:
            logger.warning("LLM generation failed, using fallback: %s", exc)
        except Exception as exc:  # noqa: BLE001
            logger.warning("LLM generation unexpected error, using fallback: %s", exc)

    if script is None:
        script = fallback_demo_script(resolved_topic)

    return script_to_meeting_events(script, resolved_topic)
