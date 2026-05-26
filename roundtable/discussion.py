from roundtable.agent_loader import ExpertAgent
from roundtable.session import (
    RoundtableSession,
    add_turn,
    format_turns_for_prompt,
    save_session,
)


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


def _call_llm(llm, prompt: str) -> str:
    response = llm.call([{"role": "user", "content": prompt}])
    return _llm_response_to_text(response).strip()


def run_expert_round(
    llm,
    session: RoundtableSession,
    experts: list,
    project_context: str,
    round_goal: str,
    print_output: bool = True,
) -> None:
    """
    让每个专家依次发言。
    每个专家发言后立即写入 session.turns 并保存 session。
    """
    spoken_count = 0

    for expert in experts:
        if not isinstance(expert, ExpertAgent):
            continue

        if print_output:
            print()
            print("-" * 40)
            print(f"🎯 专家发言：{expert.name} [{expert.category}]")
            print("-" * 40)

        previous_turns = format_turns_for_prompt(session)
        if not previous_turns.strip():
            previous_turns = "（暂无）"

        prompt = f"""你现在要扮演以下专家角色，请严格站在该专家立场发言。

【专家角色提示词】
{expert.prompt}

【项目背景】
{project_context}

【用户原始输入】
{session.original_input}

【当前累计上下文】
{session.current_context}

【前面专家已发表的观点】
{previous_turns}

【本轮讨论目标】
{round_goal}

请你严格站在你的专家立场发言，输出以下结构（使用中文）：

### 核心判断
（你对当前问题最重要的判断）

### 机会点
（你看到的产品或业务机会）

### 风险点
（你看到的风险或隐患）

### 被忽略的盲点
（其他角色可能没注意到的重要视角）

### 建议行动
1. （第一条可执行建议）
2. （第二条可执行建议）
3. （第三条可执行建议）

要求：必须结合用户输入的具体内容，不要泛泛而谈。"""

        try:
            content = _call_llm(llm, prompt)
            add_turn(session, expert.name, content)
            save_session(session)
            spoken_count += 1
            if print_output:
                print()
                print(content)
        except Exception as exc:
            if print_output:
                print(f"[错误] 专家 {expert.name} 发言失败：{exc}")

    if print_output:
        print()
        print(f"✅ 本轮圆桌讨论完成，共 {spoken_count} 位专家发言。")


def run_moderator_opening(
    llm,
    session: RoundtableSession,
    experts: list,
    project_context: str,
    discussion_plan: list,
    print_output: bool = True,
) -> None:
    """
    主持人开场白。在专家发言前调用，让主持人介绍本次讨论议题和参与专家。
    开场白写入 session.turns，role 为 "主持人"。
    """
    original_input = session.original_input.strip()
    if len(original_input) > 400:
        original_input_summary = original_input[:400] + "..."
    else:
        original_input_summary = original_input

    experts_lines = []
    for expert in experts:
        if isinstance(expert, ExpertAgent):
            experts_lines.append(f"- {expert.name}（{expert.category}）")
        elif isinstance(expert, dict):
            experts_lines.append(
                f"- {expert.get('name', expert.get('id', '未知专家'))}（{expert.get('category', '')}）"
            )
    experts_list = "\n".join(experts_lines) if experts_lines else "（暂无专家）"

    plan_text = "\n".join(f"- {item}" for item in discussion_plan) if discussion_plan else "（待定）"

    prompt = f"""你是 AI 圆桌会议主持人。

请用简洁的中文做开场白，介绍：
1. 本次讨论的核心议题（基于用户输入概括）
2. 参与本次讨论的专家名单和各自职责
3. 讨论计划（按 discussion_plan 说明）

【用户原始输入摘要】
{original_input_summary}

【参与专家】
{experts_list}

【讨论计划】
{plan_text}

输出要简洁，不超过 300 字，使用中文。"""

    try:
        content = _call_llm(llm, prompt)
        add_turn(session, "主持人", content)
        save_session(session)
        if print_output:
            print()
            print("-" * 40)
            print("🎙️ 主持人开场")
            print("-" * 40)
            print()
            print(content)
            print()
    except Exception as exc:
        if print_output:
            print(f"[错误] 主持人开场失败：{exc}")
