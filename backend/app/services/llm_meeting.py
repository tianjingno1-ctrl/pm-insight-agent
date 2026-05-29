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
    # 新版：直接用语义 id
    "host": "host",
    "product": "product",
    "tech": "tech",
    "growth": "growth",
    # 兼容旧版小马 id
    "twilight": "host",
    "rainbow": "growth",
    "rarity": "product",
    "fluttershy": "tech",
}

# 与 frontend/lib/mockEvents.ts 角色名一致
EXPERT_ROSTER: list[tuple[str, str, str]] = [
    ("host", "主持人", "host"),
    ("product", "产品专家", "product"),
    ("tech", "技术专家", "tech"),
    ("growth", "增长专家", "growth"),
]

# 兼容测试/旧引用
PONY_ROSTER = EXPERT_ROSTER

SPEECH_EMOTIONS = ("thinking", "excited", "worried", "neutral", "happy")
SPEECH_ACTIONS = ("open", "suggest", "challenge", "support", "summarize")

_SYSTEM_PROMPT = """你是产品经理圆桌会议编剧。根据用户议题，编写一场四角色中文圆桌讨论脚本。

固定角色（speakerId 必须使用下列值，speakerName 必须使用下列中文名）：
- host / 主持人：控场、结构、证据、收束
- product / 产品专家：MVP 边界、用户价值、体验
- tech / 技术专家：工程可行性、架构取舍、交付风险
- growth / 增长专家：需求验证、增长假设、市场节奏

只输出一个 JSON 对象，不要 Markdown，不要解释，不要代码块。
JSON 结构：
{
  "title": "string",
  "topic": "string",
  "messages": [
    {"speakerId": "host|product|tech|growth", "speakerName": "主持人|产品专家|技术专家|增长专家", "text": "string"}
  ],
  "summary": {
    "keyPoints": ["string", "string", "string"],
    "decision": "string",
    "risks": ["string", "string"]
  }
}
约束：
- messages 6-10 条；每条 1-3 句话；内容必须明显围绕 topic，不同 topic 讨论内容必须不同；
- 禁止照搬示例话术；禁止出现 Twilight、Rainbow 等英文角色名；
- speakerName 必须与 speakerId 对应（host→主持人，product→产品专家，tech→技术专家，growth→增长专家）。"""


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
        title=f"关于「{t}」的专家圆桌",
        topic=t,
        messages=[
            LlmMessage(
                speakerId="host",
                speakerName="主持人",
                text=f"我们先框定议题：{t}。我会从目标、约束和可验证假设三条线拆开。",
            ),
            LlmMessage(
                speakerId="growth",
                speakerName="增长专家",
                text=f"别分析太久。围绕「{t}」，先明确谁受益、怎么验证需求是否真实存在。",
            ),
            LlmMessage(
                speakerId="product",
                speakerName="产品专家",
                text=f"同意要快，但 MVP 边界要清楚。针对「{t}」，第一版只解决最痛的一个场景。",
            ),
            LlmMessage(
                speakerId="tech",
                speakerName="技术专家",
                text=f"从工程角度，{t} 若两周内要演示，建议先 mock 数据 + 手动流程，别一上来接复杂接口。",
            ),
            LlmMessage(
                speakerId="growth",
                speakerName="增长专家",
                text="可以先并行：一条线做可演示原型，一条线找 5 个目标用户访谈。",
            ),
            LlmMessage(
                speakerId="host",
                speakerName="主持人",
                text=f"收束：「{t}」先用最小方案验证核心假设，再决定是否加大投入。",
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

    # 各专家就位（由本人简短发言，与前端圆桌角色名一致）
    for idx, (_sid, display_name, agent_id) in enumerate(EXPERT_ROSTER):
        events.append(
            {
                "id": f"llm-join-{idx}",
                "type": "speech",
                "speakerId": agent_id,
                "emotion": "happy",
                "action": "open",
                "text": f"{display_name}已就位。",
                "delay_before_ms": 0,
                "duration_ms": 1400,
            }
        )

    # 议题介绍 → 主持人
    events.append(
        {
            "id": "llm-topic-intro",
            "type": "speech",
            "speakerId": "host",
            "emotion": "thinking",
            "action": "open",
            "text": f"今天讨论：{resolved_topic}",
            "delay_before_ms": 0,
            "duration_ms": 2400,
        }
    )

    # messages → speech（优先用 LLM 返回的 speakerName 校验，展示层靠 speakerId）
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
