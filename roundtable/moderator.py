import json

from roundtable.expert_selector import extract_json_from_text
from roundtable.session import (
    RoundtableSession,
    add_turn,
    format_turns_for_prompt,
    save_session,
)

TYPE_LABELS = {
    "add_context": "补充背景信息",
    "change_assumption": "改变前提假设",
    "new_question": "提出新问题",
    "request_perspective": "要求特定视角",
    "challenge_result": "质疑已有结论",
    "summarize_now": "要求生成总结",
    "generate_prd": "要求生成 PRD",
    "end_session": "结束讨论",
}

_SHORTCUT_TYPES = {
    "SUMMARY": "summarize_now",
    "PRD": "generate_prd",
    "END": "end_session",
}

_FALLBACK_CLASSIFICATION = {
    "type": "add_context",
    "reason": "无法解析 LLM 返回，默认作为补充背景处理",
    "recommended_action": "更新上下文后继续讨论",
    "need_new_experts": False,
    "suggested_expert_keywords": [],
    "next_round_goal": "基于新信息继续分析",
}


def _llm_response_to_text(response) -> str:
    if response is None:
        return ""
    if isinstance(response, str):
        return response
    for attr in ("content", "text"):
        if hasattr(response, attr):
            value = getattr(response, attr)
            if value is not None:
                return str(value)
    return str(response)


def _shortcut_result(interruption_type: str) -> dict:
    return {
        "type": interruption_type,
        "reason": "用户输入了快捷指令",
        "recommended_action": "立即执行对应操作",
        "need_new_experts": False,
        "suggested_expert_keywords": [],
        "next_round_goal": "",
    }


def _normalize_classification(data: dict) -> dict:
    result = dict(_FALLBACK_CLASSIFICATION)
    if not isinstance(data, dict):
        return result

    interruption_type = data.get("type")
    if interruption_type in TYPE_LABELS:
        result["type"] = interruption_type

    result["reason"] = str(data.get("reason", result["reason"]))
    result["recommended_action"] = str(
        data.get("recommended_action", result["recommended_action"])
    )

    need_new = data.get("need_new_experts", False)
    if isinstance(need_new, str):
        need_new = need_new.strip().lower() in ("true", "1", "yes", "是")
    result["need_new_experts"] = bool(need_new)

    keywords = data.get("suggested_expert_keywords", [])
    if isinstance(keywords, list):
        result["suggested_expert_keywords"] = [str(k) for k in keywords]
    else:
        result["suggested_expert_keywords"] = []

    result["next_round_goal"] = str(data.get("next_round_goal", result["next_round_goal"]))
    return result


def classify_user_interruption(llm, user_input: str, session: RoundtableSession) -> dict:
    """
    判断用户在讨论中途输入的内容属于哪种类型。
    返回 dict，结构见下方。
    """
    command = user_input.strip().upper()
    if command in _SHORTCUT_TYPES:
        return _shortcut_result(_SHORTCUT_TYPES[command])

    session_context = format_turns_for_prompt(session, max_chars=4000)
    if not session_context.strip():
        session_context = "（暂无发言记录）"

    prompt = f"""你是 AI 圆桌会议主持人。

用户在讨论过程中输入了新内容，请判断它的类型并决定下一步动作。

可选类型（只能选一个）：
- add_context：补充背景信息
- change_assumption：改变了某个前提假设
- new_question：提出了新问题
- request_perspective：要求从某个特定视角分析
- challenge_result：质疑已有结论
- summarize_now：要求生成总结
- generate_prd：要求生成 PRD
- end_session：结束讨论

当前会话上下文（最近发言摘要）：
{session_context}

用户新输入：
{user_input}

请直接输出合法 JSON，不要输出任何 Markdown 标记：
{{
  "type": "类型",
  "reason": "判断原因",
  "recommended_action": "建议的下一步动作描述",
  "need_new_experts": true或false,
  "suggested_expert_keywords": ["关键词1", "关键词2"],
  "next_round_goal": "如果需要继续讨论，下一轮的目标"
}}"""

    try:
        response = llm.call([{"role": "user", "content": prompt}])
        raw_text = _llm_response_to_text(response)
        json_str = extract_json_from_text(raw_text)
        if json_str:
            parsed = json.loads(json_str)
            return _normalize_classification(parsed)
    except Exception:
        pass

    return dict(_FALLBACK_CLASSIFICATION)


def print_interruption_result(result: dict) -> None:
    """
    把 classify_user_interruption 的结果打印成用户友好的中文提示。
    """
    interruption_type = result.get("type", "add_context")
    type_label = TYPE_LABELS.get(interruption_type, interruption_type)
    need_new = "是" if result.get("need_new_experts") else "否"
    next_goal = result.get("next_round_goal", "") or "（无）"

    print()
    print("-" * 40)
    print("🎙️ 主持人判断")
    print("-" * 40)
    print(f"类型：{type_label}")
    print(f"原因：{result.get('reason', '')}")
    print(f"下一步：{result.get('recommended_action', '')}")
    print(f"是否需要新专家：{need_new}")
    print(f"下一轮目标：{next_goal}")
    print("-" * 40)
    print()


def generate_round_summary(llm, session: RoundtableSession, print_output: bool = True) -> str:
    """
    在每轮专家发言结束后，让主持人生成一段阶段性小结。
    小结写入 session.turns（role="主持人小结"），并保存 session。
    返回小结文本。
    """
    turns = format_turns_for_prompt(session)
    if not turns.strip():
        turns = "（暂无讨论记录）"

    prompt = f"""你是 AI 圆桌会议主持人。

请基于以下专家讨论记录，生成一段简洁的阶段性小结（中文，不超过 400 字）。

小结需要包含：
1. 本轮讨论的主要共识
2. 主要分歧或待确认点
3. 下一步建议方向

【专家讨论记录】
{turns}

请直接输出小结文字，不需要标题。"""

    try:
        response = llm.call([{"role": "user", "content": prompt}])
        summary = _llm_response_to_text(response).strip()
    except Exception as exc:
        summary = f"阶段性小结生成失败：{exc}"

    add_turn(session, "主持人小结", summary)
    save_session(session)

    if print_output:
        print()
        print("-" * 40)
        print("📋 主持人阶段性小结")
        print("-" * 40)
        print()
        print(summary)
        print()

    return summary
