# -*- coding: utf-8 -*-
"""
PM Insight Roundtable · Streamlit 可视化界面
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from core.llm import check_api_key, get_llm
from core.utils import read_project_context
from roundtable.agent_loader import load_expert_agents
from roundtable.agent_registry import AgentRegistry
from roundtable.discussion import run_expert_round, run_moderator_opening
from roundtable.expert_selector import auto_select_experts
from roundtable.moderator import generate_round_summary
from roundtable.session import add_turn, create_session, save_session
from roundtable.synthesis import update_memory_files

MEMORY_FILES = {
    "历史洞察": Path("memory/insights.md"),
    "历史决策": Path("memory/decisions.md"),
    "待办事项": Path("memory/todos.md"),
}


def _read_memory_file(path: Path) -> str:
    if not path.is_file():
        return "暂无记录"
    try:
        content = path.read_text(encoding="utf-8").strip()
    except OSError:
        return "暂无记录"
    return content if content else "暂无记录"


def _default_round_goal(result: dict) -> str:
    plan = result.get("discussion_plan") or []
    if plan:
        return plan[0]
    return "从各自专业角度分析用户需求与可行方案"


def _turn_role(turn) -> str:
    if isinstance(turn, dict):
        return turn.get("role", "")
    return turn.role


def _turn_content(turn) -> str:
    if isinstance(turn, dict):
        return turn.get("content", "")
    return turn.content


def _extract_display_messages(session) -> list[dict]:
    """从 session.turns 提取用于界面展示的发言（主持人 + 专家）。"""
    messages = []
    for turn in session.turns:
        role = _turn_role(turn)
        content = _turn_content(turn)
        if not content.strip():
            continue
        if role == "用户":
            continue
        if role == "主持人":
            messages.append({"type": "assistant", "name": None, "content": content})
        elif role == "主持人小结":
            continue
        else:
            expert_name = role.split("（")[0].strip() if "（" in role else role
            messages.append({"type": "expert", "name": expert_name, "content": content})
    return messages


def run_discussion(user_input: str) -> list[dict]:
    """执行一轮圆桌讨论，返回用于展示的 message 列表。"""
    check_api_key()
    llm = get_llm()
    registry = AgentRegistry(load_expert_agents())
    project_context = read_project_context()

    session = create_session(
        title=user_input[:40],
        original_input=user_input,
        selected_experts=[],
    )
    add_turn(session, "用户", user_input)
    save_session(session)

    result = auto_select_experts(llm, user_input, registry)
    experts = result["experts"]
    session.selected_experts = [expert.id for expert in experts]
    save_session(session)

    discussion_plan = result.get("discussion_plan") or []
    if discussion_plan:
        round_goal = discussion_plan[0]
    else:
        round_goal = _default_round_goal(result)

    run_moderator_opening(
        llm,
        session,
        experts,
        project_context=project_context,
        discussion_plan=discussion_plan,
        print_output=False,
    )

    run_expert_round(
        llm,
        session,
        experts,
        project_context=project_context,
        round_goal=round_goal,
        print_output=False,
    )

    generate_round_summary(llm, session, print_output=False)

    for turn in reversed(session.turns):
        if _turn_role(turn) == "主持人小结":
            summary = _turn_content(turn)
            report = f"## 1. 一句话结论\n{summary}\n"
            update_memory_files(session, report)
            break

    save_session(session)
    return _extract_display_messages(session)


def render_memory_panel() -> None:
    st.markdown("### 📚 记忆面板")
    for label, path in MEMORY_FILES.items():
        with st.expander(label, expanded=False):
            st.markdown(_read_memory_file(path))


def render_sidebar() -> tuple[bool, str]:
    with st.sidebar:
        st.title("🎯 专家圆桌系统")
        question = st.text_area(
            "请输入你的问题",
            height=120,
            placeholder="描述你的产品想法、问题或决策…",
            key="user_question",
        )
        submitted = st.button("提交", type="primary", use_container_width=True)
        st.divider()
        render_memory_panel()
    return submitted, (question or "").strip()


def main() -> None:
    st.set_page_config(
        page_title="专家圆桌系统",
        page_icon="🎯",
        layout="wide",
    )

    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "discussion_complete" not in st.session_state:
        st.session_state.discussion_complete = False

    submitted, question = render_sidebar()

    st.title("🎯 AI 产品专家圆桌")

    if submitted:
        if not question:
            st.warning("请输入问题后再提交。")
        else:
            try:
                with st.spinner("专家讨论中..."):
                    st.session_state.messages = run_discussion(question)
                    st.session_state.discussion_complete = True
                st.rerun()
            except SystemExit:
                st.error("未配置有效的 API Key，请检查 .env 文件。")
            except Exception as exc:
                st.error(f"讨论失败：{exc}")
                st.session_state.discussion_complete = False

    if st.session_state.discussion_complete and st.session_state.messages:
        for msg in st.session_state.messages:
            if msg["type"] == "assistant":
                with st.chat_message("assistant"):
                    st.markdown(msg["content"])
            else:
                with st.chat_message(name=msg["name"]):
                    st.markdown(msg["content"])
        st.success("✅ 本轮讨论已完成，记忆文件已更新")
    elif not submitted or not st.session_state.discussion_complete:
        st.info("等待讨论开始...")


if __name__ == "__main__":
    main()
