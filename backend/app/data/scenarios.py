"""Mock meeting scripts (Python dicts). Manually aligned with frontend mock TS; drift risk."""

from __future__ import annotations

SUPPORTED_SCENARIOS = frozenset({"default", "concise", "verbose", "weak"})


class UnknownScenarioError(ValueError):
    def __init__(self, scenario: str) -> None:
        super().__init__(f"Unknown scenario: {scenario!r}")
        self.scenario = scenario


def _started(scenario_key: str) -> dict:
    return {
        "id": f"mock-start-{scenario_key}",
        "type": "meeting_started",
        "protocolVersion": "1.0",
        "delay_before_ms": 0,
    }


def _done(scenario_key: str) -> dict:
    return {
        "id": f"mock-done-{scenario_key}",
        "type": "meeting_done",
        "delay_before_ms": 0,
    }


def _wrap(scenario_key: str, body: list[dict]) -> list[dict]:
    return [_started(scenario_key), *body, _done(scenario_key)]


_DEFAULT_BODY: list[dict] = [
    {
        "id": "mock-default-1",
        "type": "speech",
        "speakerId": "host",
        "emotion": "thinking",
        "action": "open",
        "text": "今天只讨论一件事：两周内这个 MVP 到底该砍到多小。",
        "delay_before_ms": 0,
        "duration_ms": 2600,
    },
    {
        "id": "mock-default-2",
        "type": "speech",
        "speakerId": "product",
        "emotion": "excited",
        "action": "suggest",
        "text": "我先反对做完整报表。老板要的不是图表，而是现金流什么时候会断。",
        "delay_before_ms": 0,
        "duration_ms": 3200,
    },
    {
        "id": "mock-default-3",
        "type": "speech",
        "speakerId": "tech",
        "targetId": "product",
        "emotion": "worried",
        "action": "challenge",
        "text": "方向可以，但我反对第一版接银行接口。两周内风险太高，只能先做 CSV 上传。",
        "delay_before_ms": 0,
        "duration_ms": 3400,
    },
    {
        "id": "mock-default-4",
        "type": "speech",
        "speakerId": "growth",
        "targetId": "product",
        "emotion": "angry",
        "action": "reject",
        "text": "你们又急着做产品了。先拿假原型找 5 个老板验证，没人催款就别写代码。",
        "delay_before_ms": 0,
        "duration_ms": 3400,
    },
    {
        "id": "mock-default-5",
        "type": "speech",
        "speakerId": "host",
        "emotion": "happy",
        "action": "summarize",
        "text": "好，分歧已经清楚了：不是做不做 AI，而是先验证老板会不会因此行动。",
        "delay_before_ms": 0,
        "duration_ms": 3000,
    },
    {
        "id": "mock-summary-default",
        "type": "summary",
        "delay_before_ms": 0,
        "duration_ms": 0,
        "summary": {
            "direction": "先做现金流预警，不做完整财务报表。",
            "disagreement": "是否接银行接口。技术侧建议第一版只支持 CSV 上传。",
            "nextStep": "用 3 到 5 个真实老板测试预警短信是否促成催款行动。",
        },
    },
]

_CONCISE_BODY: list[dict] = [
    {
        "id": "mock-concise-1",
        "type": "speech",
        "speakerId": "host",
        "emotion": "thinking",
        "action": "open",
        "text": "两周 MVP 范围，今天定稿。",
        "delay_before_ms": 0,
    },
    {
        "id": "mock-concise-2",
        "type": "speech",
        "speakerId": "product",
        "emotion": "excited",
        "action": "suggest",
        "text": "只做现金流预警，不做报表。",
        "delay_before_ms": 0,
    },
    {
        "id": "mock-summary-concise",
        "type": "summary",
        "delay_before_ms": 0,
        "summary": {
            "direction": "现金流预警优先。",
            "disagreement": "是否接银行。",
            "nextStep": "5 家老板验证催款动作。",
        },
    },
]

_VERBOSE_BODY: list[dict] = [
    {
        "id": "mock-verbose-1",
        "type": "speech",
        "speakerId": "host",
        "emotion": "thinking",
        "action": "open",
        "text": "各位，我们今天花整整一轮时间，只讨论一件事：在两周这个非常紧的窗口里，这个面向中小企业老板的 AI 财务助手，MVP 到底应该砍到什么程度。",
        "delay_before_ms": 0,
    },
    {
        "id": "mock-verbose-2",
        "type": "speech",
        "speakerId": "product",
        "emotion": "excited",
        "action": "suggest",
        "text": "我强烈建议不要一上来就做完整报表和可视化大屏。老板真正焦虑的是现金流什么时候会见底。",
        "delay_before_ms": 0,
    },
    {
        "id": "mock-summary-verbose",
        "type": "summary",
        "delay_before_ms": 0,
        "summary": {
            "direction": "两周 MVP 聚焦现金流预警与见底倒计时，不做完整财务报表体系。",
            "disagreement": "银行接口是否纳入第一版：产品倾向尽快验证价值，技术强调两周内只能 CSV。",
            "nextStep": "用 3～5 位真实中小企业老板做原型测试，观察预警是否触发实际催款行为。",
        },
    },
]

_WEAK_BODY: list[dict] = [
    {
        "id": "mock-weak-1",
        "type": "speech",
        "speakerId": "host",
        "text": "那个……随便聊聊？",
        "delay_before_ms": 0,
    },
    {
        "id": "mock-weak-2",
        "type": "speech",
        "speakerId": "product",
        "emotion": "uncertain",
        "text": "图表？",
        "delay_before_ms": 0,
    },
    {
        "id": "mock-weak-3",
        "type": "speech",
        "speakerId": "tech",
        "targetId": "unknown-expert",
        "emotion": "worried",
        "action": "challenge",
        "text": "偏题了。",
        "delay_before_ms": 0,
    },
    {
        "id": "mock-summary-weak",
        "type": "summary",
        "delay_before_ms": 0,
        "summary": {
            "direction": "（勉强）先讨论现金流预警，但会议前期跑题较多。",
            "disagreement": "产品想加社区/图表，增长与技术的焦点不一致。",
            "nextStep": "需要重新对齐目标用户与两周 MVP 边界后再排期。",
        },
    },
]

_SCENARIOS: dict[str, list[dict]] = {
    "default": _wrap("default", _DEFAULT_BODY),
    "concise": _wrap("concise", _CONCISE_BODY),
    "verbose": _wrap("verbose", _VERBOSE_BODY),
    "weak": _wrap("weak", _WEAK_BODY),
}


def get_scenario_events(scenario: str) -> list[dict]:
    if scenario not in SUPPORTED_SCENARIOS:
        raise UnknownScenarioError(scenario)
    return [dict(event) for event in _SCENARIOS[scenario]]
