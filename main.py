"""
PM Insight Roundtable：AI 产品圆桌会议
"""

import sys
from pathlib import Path

from core.llm import check_api_key, get_llm
from core.report import save_legacy_report
from core.utils import (
    check_sensitive_info,
    print_divider,
    print_header,
    read_multiline_input,
    read_project_context,
)
from roundtable.agent_loader import load_expert_agents
from roundtable.agent_registry import AgentRegistry
from roundtable.discussion import run_expert_round, run_moderator_opening
from roundtable.expert_selector import auto_select_experts
from roundtable.moderator import (
    classify_user_interruption,
    generate_round_summary,
    print_interruption_result,
)
from roundtable.session import add_turn, create_session, save_session, update_context
from roundtable.synthesis import (
    generate_prd_only,
    save_report,
    synthesize_roundtable_report,
    update_memory_files,
)

SESSIONS_OUTPUT_DIR = Path("output/sessions")
_INITIAL_COMMANDS = frozenset({"SUMMARY", "PRD", "END"})

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


def _is_initial_command(text: str) -> bool:
    return text.strip().upper() in _INITIAL_COMMANDS


def _normalize_command(text: str) -> str:
    return text.strip().upper()


def _read_follow_up_input() -> str:
    """
    读取圆桌跟进输入。
    单独一行的 END / SUMMARY / PRD 视为指令；多行补充以 ### 结束。
    """
    print_divider("─", 50)
    print("💬 请继续输入（补充信息/新问题），或输入以下指令：")
    print("   SUMMARY - 生成完整报告")
    print("   PRD     - 只生成 PRD")
    print("   END     - 结束讨论")
    print("   （多行补充内容请以单独一行 ### 结束）")
    print_divider("─", 50)

    try:
        first_line = input().strip()
    except EOFError:
        return ""

    if not first_line:
        return ""

    if _normalize_command(first_line) in _INITIAL_COMMANDS:
        return first_line

    lines = [first_line]
    while True:
        try:
            line = input()
        except EOFError:
            break
        stripped = line.strip()
        if _normalize_command(stripped) in _INITIAL_COMMANDS:
            return stripped
        if stripped == "###":
            break
        lines.append(line)

    return "\n".join(lines).strip()


def _handle_session_command(
    cmd: str,
    *,
    llm,
    session,
    project_context: str,
) -> str:
    """
    处理 END / SUMMARY / PRD 指令。
    返回：'exit' 结束会话，'continue' 继续主循环（如 PRD 后）。
    """
    if cmd == "END":
        print("\n👋 感谢参与圆桌讨论！")
        return "exit"

    if cmd == "SUMMARY":
        print("\n📝 正在生成完整报告...")
        report = synthesize_roundtable_report(llm, session, project_context)
        path = save_report(report, session.session_id)
        update_memory_files(session, report)
        print(f"\n✅ 报告已保存：{path}")
        return "exit"

    if cmd == "PRD":
        print("\n📄 正在生成 PRD...")
        prd = generate_prd_only(llm, session, project_context)
        path = save_report(prd, f"{session.session_id}_prd")
        print(f"\n✅ PRD 已保存：{path}")
        return "continue"

    return "unknown"


def _save_session_transcript(session) -> Path:
    """将会话完整讨论记录保存到 output/sessions/session_{session_id}.txt"""
    SESSIONS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = SESSIONS_OUTPUT_DIR / f"session_{session.session_id}.txt"

    lines = [
        f"会话 ID: {session.session_id}",
        f"标题: {session.title}",
        f"创建时间: {session.created_at}",
        f"更新时间: {session.updated_at}",
        "",
        "【原始输入】",
        session.original_input,
        "",
        "【累计上下文】",
        session.current_context,
        "",
        "【讨论记录】",
        "",
    ]
    for turn in session.turns:
        if isinstance(turn, dict):
            role = turn.get("role", "")
            content = turn.get("content", "")
            created_at = turn.get("created_at", "")
        else:
            role = turn.role
            content = turn.content
            created_at = turn.created_at
        lines.append(f"--- {role} ({created_at}) ---")
        lines.append(content)
        lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def _default_round_goal(result: dict) -> str:
    plan = result.get("discussion_plan") or []
    if plan:
        return plan[0]
    return "从各自专业角度分析用户需求与可行方案"


def run_roundtable() -> None:
    # Step 1：初始化
    print_header("PM Insight Roundtable · AI 产品圆桌会议")
    check_api_key()
    llm = get_llm()
    registry = AgentRegistry(load_expert_agents())
    project_context = read_project_context()

    # Step 2：获取用户输入
    while True:
        print()
        print("请描述你的产品想法、问题或决策（支持多行，输入 END 结束）：")
        user_input = read_multiline_input()
        if not user_input:
            print("输入不能为空，程序退出。")
            sys.exit(1)
        if _is_initial_command(user_input):
            print("⚠️ 请先描述你的产品想法，再使用指令。")
            continue
        break

    warnings = check_sensitive_info(user_input)
    if warnings:
        print(f"⚠️  检测到可能的敏感信息：{warnings}，请确认是否继续？(y/n): ", end="")
        confirm = input().strip().lower()
        if confirm != "y":
            sys.exit(0)

    # Step 3：创建 session
    session = create_session(
        title=user_input[:40],
        original_input=user_input,
        selected_experts=[],
    )
    add_turn(session, "用户", user_input)
    save_session(session)
    print(f"\n📁 会话已创建：{session.session_id}")

    # Step 4：自动选择专家
    print("\n🔍 正在分析议题并选择专家...")
    result = auto_select_experts(llm, user_input, registry)
    experts = result["experts"]
    session.selected_experts = [expert.id for expert in experts]
    save_session(session)

    print(f"\n✅ 已选定 {len(result['experts'])} 位专家参与本次圆桌：")
    for expert in result["experts"]:
        print(f"  · {expert.name} [{expert.category}]")

    missing = result.get("missing_perspectives") or []
    if missing:
        print("\n💡 主持人补充视角：")
        for perspective in missing:
            print(f"  · {perspective}")

    try:
        # Step 5：主持人开场
        print("\n🎙️ 主持人开场中...")
        run_moderator_opening(
            llm,
            session,
            experts,
            project_context=project_context,
            discussion_plan=result.get("discussion_plan") or [],
        )

        # Step 6：主讨论循环
        round_num = 1
        session_done = False
        while not session_done:
            print(f"\n{'═' * 50}")
            print(f"📋 第 {round_num} 轮讨论")
            print(f"{'═' * 50}")

            discussion_plan = result.get("discussion_plan") or []
            if discussion_plan:
                round_goal = discussion_plan[min(round_num - 1, len(discussion_plan) - 1)]
            else:
                round_goal = _default_round_goal(result)

            run_expert_round(
                llm,
                session,
                experts,
                project_context=project_context,
                round_goal=round_goal,
            )
            generate_round_summary(llm, session)

            while True:
                follow_up = _read_follow_up_input()
                if not follow_up:
                    print("输入为空，请重新输入，或输入 END 结束讨论。")
                    continue

                cmd = _normalize_command(follow_up)
                if cmd in _INITIAL_COMMANDS:
                    action = _handle_session_command(
                        cmd,
                        llm=llm,
                        session=session,
                        project_context=project_context,
                    )
                    if action == "exit":
                        session_done = True
                        break
                    round_num += 1
                    break

                classification = classify_user_interruption(llm, follow_up, session)
                print_interruption_result(classification)

                interruption_type = classification.get("type", "add_context")
                if interruption_type in ("end_session", "summarize_now", "generate_prd"):
                    mapped = {
                        "end_session": "END",
                        "summarize_now": "SUMMARY",
                        "generate_prd": "PRD",
                    }[interruption_type]
                    action = _handle_session_command(
                        mapped,
                        llm=llm,
                        session=session,
                        project_context=project_context,
                    )
                    if action == "exit":
                        session_done = True
                        break
                    round_num += 1
                    break

                add_turn(session, "用户补充", follow_up)
                update_context(session, follow_up)
                save_session(session)

                if classification.get("need_new_experts"):
                    print("\n🔍 正在补充新专家...")
                    new_result = auto_select_experts(llm, follow_up, registry)
                    existing_ids = {expert.id for expert in experts}
                    for expert in new_result["experts"]:
                        if expert.id not in existing_ids:
                            experts.append(expert)
                            existing_ids.add(expert.id)
                            session.selected_experts.append(expert.id)
                            print(f"  ➕ 新增专家：{expert.name} [{expert.category}]")
                    save_session(session)

                round_num += 1
                break
    finally:
        save_session(session)
        transcript_path = _save_session_transcript(session)
        print(f"\n📋 讨论记录已保存：{transcript_path}")


def main() -> None:
    try:
        run_roundtable()
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断，程序退出。")
        sys.exit(0)


if __name__ == "__main__":
    main()
