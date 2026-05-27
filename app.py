# -*- coding: utf-8 -*-
"""
PM Insight Roundtable · Streamlit 可视化界面
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import streamlit as st

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from core.llm import check_api_key, get_llm
from core.utils import read_project_context
from roundtable.agent_loader import ExpertAgent, load_expert_agents
from roundtable.agent_registry import AgentRegistry
from roundtable.discussion import (
    assign_speaker_key,
    expert_display_name,
    force_summary_markdown,
    format_round_summary,
    get_assigned_speaker_key,
    infer_speaker_key_from_expert,
    infer_speaker_key_from_text,
    run_expert_round,
    run_moderator_closing,
    run_moderator_opening,
    sanitize_discussion_text,
)
from roundtable.expert_selector import auto_select_experts
from roundtable.session import (
    add_turn,
    create_session,
    extract_text_from_image_bytes,
    save_session,
    update_context,
)
from roundtable.synthesis import update_memory_files

MEMORY_FILES = {
    "洞察历史": Path("memory/insights.md"),
    "历史决策": Path("memory/decisions.md"),
    "待办事项": Path("memory/todos.md"),
}

USER_ROLES = frozenset({"用户", "你", "用户补充"})

# 小结渲染调试（验证通过后设为 False）
DEBUG_SUMMARY = True

# 固定角色展示（avatar 必须为 emoji 字符串，勿用 name 首字母）
ROLE_DISPLAY: Dict[str, Tuple[str, str]] = {
    "user": ("👤", "你"),
    "moderator": ("🎩", "主持人"),
    "product": ("🧭", "产品专家"),
    "tech": ("🛠️", "技术专家"),
    "growth": ("📈", "增长专家"),
    "risk": ("🛡️", "风险专家"),
    "design": ("🎨", "体验设计专家"),
    "strategy": ("🧠", "战略专家"),
    "priority": ("⚡", "优先级专家"),
    "unknown": ("💬", "专家"),
}

_DISPLAY_NAME_TO_KEY = {
    label: key for key, (_, label) in ROLE_DISPLAY.items() if key not in ("user", "moderator")
}

_RISK_KEYWORDS = ("风险", "合规", "法律", "隐私", "数据安全", "监管", "法务", "风控")
_STRATEGY_KEYWORDS = ("商业模式", "定价", "战略", "竞争", "壁垒", "变现")

_REGISTRY_CATEGORY_FOR_KEY = {
    "product": ("product",),
    "tech": ("engineering",),
    "growth": ("marketing", "sales"),
    "risk": ("specialized",),
    "design": ("design",),
    "strategy": ("strategy", "finance"),
}


def _read_memory_file(path: Path) -> str:
    if not path.is_file():
        return "暂无记录"
    try:
        content = path.read_text(encoding="utf-8").strip()
    except OSError:
        return "暂无记录"
    return content if content else "暂无记录"


def _default_round_goal(result: dict, round_index: int = 1, is_followup: bool = False) -> str:
    plan = result.get("discussion_plan") or []
    if plan:
        idx = min(max(round_index - 1, 0), len(plan) - 1)
        return plan[idx]
    if is_followup:
        return "回应用户最新追问，聚焦新信息，避免重复已达成共识的内容"
    return "从各自专业角度分析用户需求与可行方案"


def _turn_role(turn) -> str:
    if isinstance(turn, dict):
        return turn.get("role", "")
    return turn.role


def _turn_content(turn) -> str:
    if isinstance(turn, dict):
        return turn.get("content", "")
    return turn.content


def _speaker_key_from_expert(expert) -> str:
    return get_assigned_speaker_key(expert)


def _speaker_key_from_role_text(role: str) -> Optional[str]:
    bare = role.split("（")[0].strip() if "（" in role else role.strip()
    if bare in _DISPLAY_NAME_TO_KEY:
        return _DISPLAY_NAME_TO_KEY[bare]
    return infer_speaker_key_from_text(f"{bare} {role}")


def _target_speaker_keys(user_input: str) -> List[str]:
    """首轮/追问默认 3 位；风险或战略关键词时最多 4 位。"""
    text = (user_input or "").lower()
    keys = ["product", "tech", "growth"]
    if any(kw in text for kw in _RISK_KEYWORDS):
        if "risk" not in keys:
            keys.append("risk")
    elif any(kw in text for kw in _STRATEGY_KEYWORDS):
        if "strategy" not in keys:
            keys.append("strategy")
    return keys[:4]


def _fallback_expert(speaker_key: str) -> ExpertAgent:
    label = ROLE_DISPLAY.get(speaker_key, ROLE_DISPLAY["unknown"])[1]
    lens_hint = {
        "product": "功能边界与 MVP 取舍",
        "tech": "实现路径与工程取舍",
        "growth": "需求验证与成功信号",
        "risk": "合规与数据可靠性",
        "design": "最小交互与可理解性",
        "strategy": "商业取舍与是否值得做",
    }.get(speaker_key, "专业判断")
    agent = ExpertAgent(
        id=f"fallback-{speaker_key}",
        name=label,
        category=speaker_key,
        path="",
        description=f"内置{label}",
        prompt=f"你是{label}，从{lens_hint}角度给出简短判断。",
    )
    assign_speaker_key(agent, speaker_key)
    return agent


def _pick_expert_for_key(
    speaker_key: str,
    pool: list,
    registry: AgentRegistry,
    used_ids: Set[str],
) -> ExpertAgent:
    for expert in pool:
        if expert.id in used_ids:
            continue
        if infer_speaker_key_from_expert(expert) == speaker_key:
            assign_speaker_key(expert, speaker_key)
            used_ids.add(expert.id)
            return expert

    for cat in _REGISTRY_CATEGORY_FOR_KEY.get(speaker_key, (speaker_key,)):
        for expert in registry.list_by_category(cat):
            if expert.id in used_ids:
                continue
            assign_speaker_key(expert, speaker_key)
            used_ids.add(expert.id)
            return expert

    for expert in registry.list_all():
        if expert.id in used_ids:
            continue
        if infer_speaker_key_from_expert(expert) == speaker_key:
            assign_speaker_key(expert, speaker_key)
            used_ids.add(expert.id)
            return expert

    agent = _fallback_expert(speaker_key)
    used_ids.add(agent.id)
    return agent


def _prepare_expert_panel(
    experts: list,
    registry: AgentRegistry,
    user_input: str,
) -> list:
    """
    按 speaker_key 去重并补齐默认组合 product + tech + growth（必要时 +risk/strategy）。
  一轮内每个职能键只出现一位专家。
    """
    target_keys = _target_speaker_keys(user_input)
    pool = list(experts or [])
    used_ids: Set[str] = set()
    panel: list = []

    for key in target_keys:
        panel.append(_pick_expert_for_key(key, pool, registry, used_ids))

    return panel


def _match_expert_for_turn(role: str, experts: Optional[list]):
    if not experts or not role:
        return None
    for expert in experts:
        name = getattr(expert, "name", "") or ""
        if name and (name in role or role.startswith(name)):
            return expert
    return None


def _display_for_speaker_key(speaker_key: str) -> Tuple[str, str]:
    return ROLE_DISPLAY.get(speaker_key, ROLE_DISPLAY["unknown"])


def _message_user(content: str, role: str = "你") -> dict:
    avatar, label = ROLE_DISPLAY["user"]
    return {
        "type": "user",
        "speaker_key": "user",
        "avatar": avatar,
        "display_name": label,
        "name": label,
        "role": role,
        "content": content,
    }


def _message_moderator(content: str, role: str = "主持人") -> dict:
    avatar, label = ROLE_DISPLAY["moderator"]
    return {
        "type": "assistant",
        "speaker_key": "moderator",
        "avatar": avatar,
        "display_name": label,
        "name": label,
        "role": role,
        "content": sanitize_discussion_text(content),
    }


def _message_summary(content: str, role: str = "主持人（总结）") -> dict:
    """小结一律强制为三行标准格式（兼容旧 session 脏数据）。"""
    avatar, _ = ROLE_DISPLAY["moderator"]
    normalized = force_summary_markdown(content)
    return {
        "type": "summary",
        "speaker_key": "moderator",
        "role": role,
        "name": "主持人（总结）",
        "display_name": "主持人（总结）",
        "avatar": avatar,
        "content": normalized,
    }


def _message_expert(role: str, content: str, experts: Optional[list] = None) -> dict:
    speaker_key = _speaker_key_from_role_text(role)
    expert = _match_expert_for_turn(role, experts)
    if speaker_key is None and expert is not None:
        speaker_key = _speaker_key_from_expert(expert)
    if speaker_key is None:
        speaker_key = "unknown"
    avatar, label = _display_for_speaker_key(speaker_key)
    if not label or len(label) == 1 or label in ("", "P"):
        label = ROLE_DISPLAY["unknown"][1]
    return {
        "type": "expert",
        "speaker_key": speaker_key,
        "avatar": avatar,
        "display_name": label,
        "name": label,
        "role": role,
        "content": sanitize_discussion_text(content),
    }


def _looks_like_summary_message(content: str, name: str = "", role: str = "") -> bool:
    """按内容/身份识别小结，不依赖 msg[type]。"""
    text = content or ""
    identity = f"{name} {role}"

    if "总结" in identity or "小结" in identity:
        return True
    if "主持人（总结）" in role or "主持人小结" in role:
        return True
    if "本轮小结" in text:
        return True

    field_markers = (
        "当前倾向",
        "当前趋势",
        "当前走势",
        "当前热点",
        "目前趋势",
        "最大分歧",
        "最大封闭",
        "最大闭合",
        "最大成交量",
        "最大加密",
        "下一步建议",
        "下一步：",
    )
    return any(m in text for m in field_markers)


def _is_summary_message(msg: dict) -> bool:
    content = msg.get("content", "") or ""
    name = str(msg.get("name") or msg.get("display_name") or "")
    role = str(msg.get("role") or "")
    return msg.get("type") == "summary" or _looks_like_summary_message(
        content, name, role
    )


def _dedupe_summary_messages(messages: list) -> list:
    """连续/重复小结只保留最后一条，并统一为标准三行格式。"""
    result: list = []
    for msg in messages:
        if _is_summary_message(msg):
            normalized = dict(msg)
            normalized["type"] = "summary"
            normalized["content"] = force_summary_markdown(
                msg.get("content", "") or ""
            )
            if result and _is_summary_message(result[-1]):
                result[-1] = normalized
            else:
                result.append(normalized)
        else:
            result.append(msg)
    return result


def _rebuild_messages_from_session(session, experts: Optional[list] = None) -> list:
    """从 session.turns 全量重建 messages，避免增量 append 重复小结。"""
    messages: list = []
    for turn in session.turns:
        role = _turn_role(turn)
        content = _turn_content(turn)
        msg = _turn_to_message(role, content, experts)
        if msg:
            messages.append(msg)
    return _dedupe_summary_messages(messages)


def _turn_to_message(role: str, content: str, experts: Optional[list] = None) -> Optional[dict]:
    if not (content or "").strip():
        return None
    if role in USER_ROLES:
        return _message_user(content, role=role)
    if role == "用户":
        return _message_user(content, role="你")
    # 主持人总结：重建 messages 时即标准化，勿落成普通 assistant
    if "总结" in (role or "") or "小结" in (role or "") or role in (
        "主持人小结",
        "主持人（总结）",
    ):
        summary_role = role if ("总结" in role or "小结" in role) else "主持人（总结）"
        return _message_summary(content, role=summary_role)
    if role == "主持人":
        if _looks_like_summary_message(content, role=role):
            return _message_summary(content, role="主持人（总结）")
        return _message_moderator(content, role=role)
    if _looks_like_summary_message(content, role=role):
        return _message_summary(content, role="主持人（总结）")
    return _message_expert(role, content, experts)


def _limit_experts(
    experts: list,
    user_input: str,
    is_followup: bool,
    registry: AgentRegistry,
) -> list:
    """
    按 speaker_key 去重并补齐默认专家组合；追问轮重新按本轮问题选 3-4 位。
    """
    # TODO: 追问明显涉及新领域时，在已有 panel 上最多动态新增 1 名专家
    return _prepare_expert_panel(experts, registry, user_input)


def _extract_display_messages(session, experts: Optional[list] = None) -> list:
    """从 session.turns 构建完整展示消息列表（含用户追问）。"""
    messages = []
    for turn in session.turns:
        role = _turn_role(turn)
        content = _turn_content(turn)
        msg = _turn_to_message(role, content, experts)
        if msg:
            messages.append(msg)
    return messages


def _append_new_turns_to_messages(
    session,
    messages_so_far: list,
    turns_before: int,
    experts: Optional[list] = None,
) -> None:
    """把 session.turns 中 turns_before 之后的新发言追加到 messages_so_far。"""
    for turn in session.turns[turns_before:]:
        role = _turn_role(turn)
        content = _turn_content(turn)
        msg = _turn_to_message(role, content, experts)
        if msg:
            messages_so_far.append(msg)


def _build_memory_report(session) -> str:
    """把 session 的结构化结论拼成写入 memory 的报告格式"""
    lines = []

    if session.decisions:
        lines.append("## 结论")
        for d in session.decisions:
            lines.append(f"- {d}")

    if session.todos:
        lines.append("\n## 待办")
        for t in session.todos:
            lines.append(f"- {t}")

    if session.open_questions:
        lines.append("\n## 未决问题")
        for q in session.open_questions:
            lines.append(f"- {q}")

    return "\n".join(lines) if lines else "（本次讨论无结构化结论）"


def _latest_summary_for_memory(messages: list, session) -> str:
    """优先取最近一条 summary 消息，否则用 session 结构化字段生成报告。"""
    for msg in reversed(messages):
        if _is_summary_message(msg):
            content = force_summary_markdown((msg.get("content") or "").strip())
            if content:
                return content
    return _build_memory_report(session)


def _persist_to_long_term_memory() -> None:
    """用户主动将当前 session 结论写入长期记忆文件。"""
    session = st.session_state.rt_session
    if session is None:
        st.warning("当前没有可保存的讨论会话。")
        return
    latest_summary = _latest_summary_for_memory(st.session_state.messages, session)
    update_memory_files(session, latest_summary)
    st.session_state.memory_saved = True


def _render_messages(container, messages: list, extra_status: str = "") -> None:
    """
    遗留：动态 empty + 重绘 chat_message 列表（易触发 Streamlit setIn 错位）。
    主流程请使用 _render_message_list + status_placeholder，勿在讨论中调用本函数。
    """
    container.empty()
    with container:
        for msg in messages:
            if msg["type"] == "user":
                with st.chat_message("user", avatar="👤"):
                    st.markdown(msg["content"])
            elif msg["type"] == "assistant":
                avatar = msg.get("avatar") or ROLE_DISPLAY["moderator"][0]
                with st.chat_message("assistant", avatar=avatar):
                    st.markdown(msg["content"])
            elif msg["type"] == "summary" or _looks_like_summary_message(
                msg.get("content", ""),
                str(msg.get("name") or msg.get("display_name") or ""),
                str(msg.get("role") or ""),
            ):
                with st.container(border=True):
                    st.markdown(force_summary_markdown(msg.get("content", "")))
            else:
                avatar = msg.get("avatar") or ROLE_DISPLAY["unknown"][0]
                label = msg.get("display_name") or "专家"
                with st.chat_message("assistant", avatar=avatar):
                    st.markdown(f"**{label}**\n\n{msg['content']}")
        if extra_status:
            st.info(extra_status)


def run_discussion_streaming(
    status_placeholder,
    user_input: str = "",
    followup: str = "",
    is_followup: bool = False,
) -> None:
    """
    执行一轮圆桌讨论。仅更新 status_placeholder 状态文案；
    消息追加到 st.session_state.messages，完整列表由 main rerun 后静态渲染。
    """
    check_api_key()
    llm = get_llm()
    registry = AgentRegistry(load_expert_agents())
    project_context = read_project_context()
    messages = st.session_state.messages

    if is_followup:
        session = st.session_state.rt_session
        experts = st.session_state.rt_experts
        result = st.session_state.rt_result
        round_index = st.session_state.round_index + 1
        st.session_state.round_index = round_index

        # 用户追问已在 main 中 append 到 messages，此处只写入 session
        update_context(session, followup)
        add_turn(session, "你", followup)
        save_session(session)

        status_placeholder.info(
            f"💬 第 {round_index} 轮追问讨论进行中，请稍候..."
        )

        experts = _limit_experts(
            experts,
            followup or session.original_input,
            is_followup=True,
            registry=registry,
        )
        st.session_state.rt_experts = experts
    else:
        round_index = 1
        session = create_session(
            title=(user_input or "圆桌讨论")[:40],
            original_input=user_input,
            selected_experts=[],
        )
        add_turn(session, "用户", user_input)
        save_session(session)

        messages.clear()
        messages.append(_message_user(sanitize_discussion_text(user_input)))

        status_placeholder.info("🔍 正在分析问题，选择最合适的专家...")

        result = auto_select_experts(llm, user_input, registry)
        experts = _limit_experts(
            result["experts"], user_input, is_followup=False, registry=registry
        )
        session.selected_experts = [expert.id for expert in experts]
        save_session(session)

        st.session_state.rt_session = session
        st.session_state.rt_experts = experts
        st.session_state.rt_result = result
        st.session_state.round_index = 1

    expert_names = "、".join(
        _display_for_speaker_key(_speaker_key_from_expert(e))[1] for e in experts
    )
    status_placeholder.info(
        f"🎙️ 第 {round_index} 轮：已邀请 {expert_names}，主持人正在开场..."
    )

    round_start_index = len(session.turns)
    if is_followup and followup.strip():
        round_topic = followup.strip()
    elif not is_followup and user_input:
        round_topic = user_input
    else:
        round_topic = session.original_input

    turns_before = len(session.turns)
    run_moderator_opening(
        llm,
        session,
        experts,
        project_context=project_context,
        discussion_plan=result.get("discussion_plan") or [],
        print_output=False,
        is_followup=is_followup,
        round_index=round_index,
        followup=followup,
    )
    _append_new_turns_to_messages(session, messages, turns_before, experts)

    round_goal = _default_round_goal(result, round_index, is_followup)

    for expert in experts:
        _avatar, label = _display_for_speaker_key(_speaker_key_from_expert(expert))
        status_placeholder.info(f"💬 {label} 正在发言...")

        turns_before = len(session.turns)
        run_expert_round(
            llm,
            session,
            [expert],
            project_context=project_context,
            round_goal=round_goal,
            print_output=False,
            followup=followup,
            is_followup=is_followup,
            round_index=round_index,
        )
        _append_new_turns_to_messages(session, messages, turns_before, experts)

    status_placeholder.info("📝 主持人正在整理本轮小结...")

    turns_before = len(session.turns)
    run_moderator_closing(
        llm,
        session,
        print_output=False,
        round_index=round_index,
        round_start_index=round_start_index,
        round_topic=round_topic,
    )
    _append_new_turns_to_messages(session, messages, turns_before, experts)

    save_session(session)
    st.session_state.rt_session = session
    st.session_state.messages = _rebuild_messages_from_session(session, experts)
    st.session_state.discussion_active = True
    st.session_state.memory_saved = False

    status_placeholder.empty()
    st.rerun()


def _enrich_question(question: str, uploaded_files: list) -> str:
    enriched_question = question
    if not uploaded_files:
        return enriched_question

    file_context_parts = []
    for f in uploaded_files:
        if f.type.startswith("image/"):
            try:
                ocr_text = extract_text_from_image_bytes(f.getvalue())
                if ocr_text:
                    file_context_parts.append(
                        f"[截图 {f.name} OCR 识别内容]:\n{ocr_text[:2000]}"
                    )
                else:
                    file_context_parts.append(
                        f"[用户上传了截图：{f.name}，未能识别出文字]"
                    )
            except Exception as exc:
                file_context_parts.append(
                    f"[用户上传了截图：{f.name}，OCR 失败：{exc}]"
                )
        elif f.type in ("text/plain", "text/markdown"):
            text = f.read().decode("utf-8", errors="ignore")
            file_context_parts.append(f"[附件 {f.name}]:\n{text[:2000]}")
        elif f.type == "application/pdf":
            file_context_parts.append(
                f"[用户上传了PDF文件：{f.name}，请结合问题分析]"
            )

    if file_context_parts:
        enriched_question = (question or "") + "\n\n---\n" + "\n\n".join(
            file_context_parts
        )
    return enriched_question


def render_memory_panel() -> None:
    st.markdown("### 📚 记忆面板")
    for label, path in MEMORY_FILES.items():
        with st.expander(label, expanded=False):
            st.markdown(_read_memory_file(path))


def render_sidebar() -> tuple:
    with st.sidebar:
        st.title("🎯 专家圆桌系统")
        question = st.text_area(
            "请输入你的问题",
            height=120,
            placeholder="描述你的产品想法、问题或决策…",
            key="user_question",
        )

        uploaded_files = st.file_uploader(
            "📎 上传截图或文件（可选）",
            type=["png", "jpg", "jpeg", "webp", "pdf", "txt", "md"],
            accept_multiple_files=True,
            key="uploaded_files",
        )

        if uploaded_files:
            for f in uploaded_files:
                if f.type.startswith("image/"):
                    st.image(f, caption=f.name, use_container_width=True)
                else:
                    st.markdown(f"📄 `{f.name}`")

        submitted = st.button("提交", type="primary", use_container_width=True)
        st.divider()
        render_memory_panel()
    return submitted, (question or "").strip(), uploaded_files or []


def _render_memory_save_controls() -> None:
    """长期记忆沉淀：仅用户点击时写入 memory/*.md。"""
    if st.session_state.memory_saved:
        st.success("已写入长期记忆")
        return
    if st.button(
        "💾 沉淀本次决策到长期记忆",
        key="save_to_memory_btn",
        use_container_width=False,
    ):
        try:
            _persist_to_long_term_memory()
            st.rerun()
        except Exception as exc:
            st.error(f"写入长期记忆失败：{exc}")


def _render_message_list(messages: list) -> None:
    messages = _dedupe_summary_messages(messages)
    summary_count = sum(1 for m in messages if _is_summary_message(m))
    if DEBUG_SUMMARY:
        st.caption(
            f"DEBUG_RENDER_COUNT: total messages = {len(messages)}, "
            f"summary_count = {summary_count}"
        )

    for i, msg in enumerate(messages):
        content = msg.get("content", "") or ""
        name = str(msg.get("name") or msg.get("display_name") or "")
        role = str(msg.get("role") or "")
        msg_type = msg.get("type") or ""

        is_summary = _is_summary_message(msg) or _looks_like_summary_message(
            content, name, role
        )

        # summary 必须最先渲染，且不得落入下方 assistant/expert 的 st.markdown(content)
        if is_summary:
            normalized_content = force_summary_markdown(msg.get("content") or "")
            if DEBUG_SUMMARY:
                st.caption(
                    f"DEBUG MSG {i}: type={msg_type} role={role} "
                    f"name={name} is_summary={is_summary} head={content[:40]!r}"
                )
                st.caption("调试：摘要已规范化")
                st.code(normalized_content, language="markdown")
            with st.container(border=True):
                if DEBUG_SUMMARY:
                    st.caption("调试：即将正式渲染 normalized_content")
                st.markdown(normalized_content)
            continue

        if DEBUG_SUMMARY:
            st.caption(
                f"DEBUG MSG {i}: type={msg_type} role={role} "
                f"name={name} is_summary={is_summary} head={content[:40]!r}"
            )

        if msg_type == "user":
            with st.chat_message("user", avatar=ROLE_DISPLAY["user"][0]):
                st.markdown(content)
        elif msg_type == "assistant":
            if _looks_like_summary_message(content, name, role):
                normalized_content = force_summary_markdown(content)
                with st.container(border=True):
                    st.markdown(normalized_content)
                continue
            avatar = msg.get("avatar") or ROLE_DISPLAY["moderator"][0]
            with st.chat_message("assistant", avatar=avatar):
                st.markdown(content)
        elif msg_type == "summary":
            normalized_content = force_summary_markdown(msg.get("content") or "")
            with st.container(border=True):
                st.markdown(normalized_content)
            continue
        else:
            if _looks_like_summary_message(content, name, role):
                normalized_content = force_summary_markdown(content)
                with st.container(border=True):
                    st.markdown(normalized_content)
                continue
            avatar = msg.get("avatar") or ROLE_DISPLAY["unknown"][0]
            label = msg.get("display_name") or ROLE_DISPLAY["unknown"][1]
            if not label or len(label) <= 1:
                label = ROLE_DISPLAY["unknown"][1]
            with st.chat_message("assistant", avatar=avatar):
                st.markdown(f"**{label}**\n\n{content}")


def main() -> None:
    st.set_page_config(
        page_title="专家圆桌系统",
        page_icon="🎯",
        layout="wide",
    )

    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "discussion_active" not in st.session_state:
        st.session_state.discussion_active = False
    if "round_index" not in st.session_state:
        st.session_state.round_index = 0
    if "rt_session" not in st.session_state:
        st.session_state.rt_session = None
    if "rt_experts" not in st.session_state:
        st.session_state.rt_experts = []
    if "rt_result" not in st.session_state:
        st.session_state.rt_result = {}
    if "memory_saved" not in st.session_state:
        st.session_state.memory_saved = False
    if "pending_initial_input" not in st.session_state:
        st.session_state.pending_initial_input = ""
    if "should_run_initial" not in st.session_state:
        st.session_state.should_run_initial = False
    if "pending_followup" not in st.session_state:
        st.session_state.pending_followup = ""
    if "should_run_followup" not in st.session_state:
        st.session_state.should_run_followup = False

    submitted, question, uploaded_files = render_sidebar()

    st.title("🎯 AI 产品专家圆桌")

    history_container = st.container()
    status_placeholder = st.empty()

    running_discussion = (
        st.session_state.should_run_initial or st.session_state.should_run_followup
    )

    # ── 侧边栏首轮提交：仅设 pending，本帧不跑 LLM ─────────────────────────
    if submitted:
        if not question and not uploaded_files:
            st.warning("请输入问题或上传文件后再提交。")
        else:
            enriched = _enrich_question(question, uploaded_files)
            st.session_state.pending_initial_input = (
                enriched or "（见附件材料）"
            )
            st.session_state.should_run_initial = True
            st.session_state.messages = []
            st.session_state.discussion_active = False
            st.session_state.memory_saved = False
            st.session_state.rt_session = None
            st.session_state.rt_experts = []
            st.session_state.rt_result = {}
            st.session_state.round_index = 0
            st.session_state.should_run_followup = False
            st.session_state.pending_followup = ""
            st.rerun()

    # ── 静态历史区（不在此 empty / 动态重绘）────────────────────────────────
    with history_container:
        if st.session_state.messages:
            _render_message_list(
                _dedupe_summary_messages(st.session_state.messages)
            )
        if st.session_state.discussion_active and not running_discussion:
            st.success("✅ 本轮讨论已完成，可继续在下方追问")
            _render_memory_save_controls()
        elif (
            not st.session_state.messages
            and not st.session_state.discussion_active
            and not running_discussion
        ):
            st.info("💬 在左侧输入问题，开始专家圆桌讨论")

    # ── 追问：先 append 用户消息，下帧再跑讨论 ───────────────────────────────
    if st.session_state.discussion_active and not running_discussion:
        followup_input = st.chat_input("继续补充、追问或纠正专家观点...")
        if followup_input:
            text = followup_input.strip()
            st.session_state.messages.append(_message_user(text))
            st.session_state.pending_followup = text
            st.session_state.should_run_followup = True
            st.rerun()

    # ── 首轮讨论（rerun 后执行）────────────────────────────────────────────
    if st.session_state.should_run_initial:
        st.session_state.should_run_initial = False
        user_input = st.session_state.pending_initial_input
        try:
            run_discussion_streaming(
                status_placeholder,
                user_input=user_input,
                is_followup=False,
            )
        except SystemExit:
            status_placeholder.empty()
            st.error("未配置有效的 API Key，请检查 .env 文件。")
            st.session_state.discussion_active = False
        except Exception as exc:
            status_placeholder.empty()
            st.error(f"讨论失败：{exc}")
            st.session_state.discussion_active = False

    # ── 追问轮讨论（rerun 后执行，历史区已含用户追问）──────────────────────
    if st.session_state.should_run_followup:
        st.session_state.should_run_followup = False
        followup = st.session_state.pending_followup
        try:
            run_discussion_streaming(
                status_placeholder,
                followup=followup,
                is_followup=True,
            )
        except SystemExit:
            status_placeholder.empty()
            st.error("未配置有效的 API Key，请检查 .env 文件。")
        except Exception as exc:
            status_placeholder.empty()
            st.error(f"追问讨论失败：{exc}")


if __name__ == "__main__":
    main()
