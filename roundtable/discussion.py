from memory.memory_loader import load_memory_context
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


def _memory_prompt_block(memory_context: str) -> str:
    if not memory_context.strip():
        return ""
    return f"""
---
【历史上下文】
以下是团队过去讨论的记录，请在发言时参考，避免重复已有结论，优先在已有基础上推进：
{memory_context}
---
"""


_ROLE_PROPOSER = {
    "label": "方案提出者",
    "instruction": (
        "你的职责是【方案提出者】。\n"
        "你必须给出一个具体可执行的方案，包含：\n"
        "1. 明确的第一步行动（具体到谁来做、做什么）\n"
        "2. 预期多少时间内可以验证效果\n"
        "3. 成功的判断标准是什么\n"
        "禁止只给方向性建议，必须落到具体行动。"
    ),
}

_ROLE_DEVIL = {
    "label": "魔鬼代言人",
    "instruction": (
        "你的职责是【魔鬼代言人】。\n"
        "你必须针对前面方案提出者的具体方案，找出漏洞和风险：\n"
        "1. 指出方案中最脆弱的一个假设，说明为什么它可能是错的\n"
        "2. 列出如果这个假设失败，会发生什么后果\n"
        "3. 提出一个让方案更稳健的修改建议\n"
        "禁止泛泛而谈，必须针对前面的具体方案来挑毛病。"
    ),
}

_ROLE_IMPLEMENTER = {
    "label": "落地拆解者",
    "instruction": (
        "你的职责是【落地拆解者】。\n"
        "你必须把前面的讨论翻译成可以直接执行的任务清单：\n"
        "1. 列出3条具体任务，每条包含：负责人角色、完成标准、截止时间建议\n"
        "2. 指出讨论中还有哪一个关键问题没有被解决\n"
        "3. 给出下一次会议需要确认的唯一最重要问题\n"
        "禁止接受模糊结论，如果前面的讨论没有落地，你要明确指出缺什么。"
    ),
}

_ROLE_VALIDATOR = {
    "label": "补充验证者",
    "instruction": (
        "你的职责是【补充验证者】。\n"
        "前面的专家已经覆盖了主要方案和风险，你需要找出他们集体忽视的盲点：\n"
        "1. 指出一个前面所有人都没有提到的风险或机会\n"
        "2. 说明为什么这个点被忽视是危险的\n"
        "3. 给出一个具体的补救或利用建议\n"
        "禁止重复前面已经提过的观点，必须带来新视角。"
    ),
}

_ROLE_PROPOSER_IMPLEMENTER = {
    "label": "方案提出者+落地拆解者",
    "instruction": (
        "你同时承担【方案提出者】和【落地拆解者】的职责。\n"
        "你必须给出一个具体可执行的方案，包含：\n"
        "1. 明确的第一步行动（具体到谁来做、做什么）\n"
        "2. 预期多少时间内可以验证效果\n"
        "3. 成功的判断标准是什么\n"
        "禁止只给方向性建议，必须落到具体行动。\n\n"
        "同时你必须把方案翻译成可以直接执行的任务清单：\n"
        "1. 列出3条具体任务，每条包含：负责人角色、完成标准、截止时间建议\n"
        "2. 指出讨论中还有哪一个关键问题没有被解决\n"
        "3. 给出下一次会议需要确认的唯一最重要问题\n"
        "禁止接受模糊结论，必须给出可落地的任务。"
    ),
}

_ROLE_DEVIL_IMPLEMENTER = {
    "label": "魔鬼代言人+落地拆解者",
    "instruction": (
        "你同时承担【魔鬼代言人】和【落地拆解者】的职责。\n"
        "你必须针对前面方案提出者的具体方案，找出漏洞和风险：\n"
        "1. 指出方案中最脆弱的一个假设，说明为什么它可能是错的\n"
        "2. 列出如果这个假设失败，会发生什么后果\n"
        "3. 提出一个让方案更稳健的修改建议\n"
        "禁止泛泛而谈，必须针对前面的具体方案来挑毛病。\n\n"
        "同时你必须把讨论翻译成可以直接执行的任务清单：\n"
        "1. 列出3条具体任务，每条包含：负责人角色、完成标准、截止时间建议\n"
        "2. 指出讨论中还有哪一个关键问题没有被解决\n"
        "3. 给出下一次会议需要确认的唯一最重要问题\n"
        "禁止接受模糊结论，如果前面的讨论没有落地，你要明确指出缺什么。"
    ),
}

# 基础角色配置（供引用与扩展）
_ROLE_CONFIGS = [
    _ROLE_PROPOSER,
    _ROLE_DEVIL,
    _ROLE_IMPLEMENTER,
    _ROLE_VALIDATOR,
    _ROLE_PROPOSER_IMPLEMENTER,
    _ROLE_DEVIL_IMPLEMENTER,
]


def _get_role_config(idx: int, total: int) -> dict:
    """根据专家总人数与当前序号，动态分配圆桌角色。"""
    if total <= 0:
        return _ROLE_PROPOSER

    if total == 1:
        return _ROLE_PROPOSER_IMPLEMENTER

    if total == 2:
        if idx == 0:
            return _ROLE_PROPOSER
        return _ROLE_DEVIL_IMPLEMENTER

    if total == 3:
        if idx == 0:
            return _ROLE_PROPOSER
        if idx == 1:
            return _ROLE_DEVIL
        return _ROLE_IMPLEMENTER

    # 4 位及以上：前三位按 3 人规则，其余为补充验证者
    if idx == 0:
        return _ROLE_PROPOSER
    if idx == 1:
        return _ROLE_DEVIL
    if idx == 2:
        return _ROLE_IMPLEMENTER
    return _ROLE_VALIDATOR


def run_expert_round(
    llm,
    session: RoundtableSession,
    experts: list,
    project_context: str,
    round_goal: str,
    print_output: bool = True,
) -> None:
    """
    按专家人数动态分配圆桌角色后，依次发言。
    1人：方案提出者+落地拆解者；2人：方案提出者 / 魔鬼代言人+落地拆解者；
    3人：方案提出者 / 魔鬼代言人 / 落地拆解者；
    4人及以上：前三位同上，其余为补充验证者。
    """
    memory_context = load_memory_context()
    memory_block = _memory_prompt_block(memory_context)

    valid_experts = [e for e in experts if isinstance(e, ExpertAgent)]
    total = len(valid_experts)
    spoken_count = 0
    expert_idx = 0

    for expert in experts:
        if not isinstance(expert, ExpertAgent):
            continue

        role_config = _get_role_config(expert_idx, total)
        role_label = role_config["label"]
        role_instruction = role_config["instruction"]
        expert_idx += 1

        if print_output:
            print()
            print("-" * 40)
            print(f"🎯 {expert.name} [{role_label}]")
            print("-" * 40)

        previous_turns = format_turns_for_prompt(session)
        if not previous_turns.strip():
            previous_turns = "（本轮第一位发言，暂无前序讨论）"

        prompt = f"""你现在扮演以下专家角色，请严格站在该专家立场发言。

【专家角色提示词】
{expert.prompt}

【本轮你的特定职责】
{role_instruction}

【项目背景】
{project_context}

【用户原始输入】
{session.original_input}

【当前累积上下文】
{session.current_context}

【前面专家已发表的观点】
{previous_turns}

【本轮讨论目标】
{round_goal}
{memory_block}
请用自然的会议发言风格输出，不要使用固定标题结构，像真实开会一样直接说话。

要求：
- 如果你是第一位发言，直接给出你的判断和方案，必须包含第一步具体行动、验证时间和成功标准
- 如果前面有人发言，必须先用一两句话点名回应某个具体观点（同意或反对），再展开你自己的主张
- 根据你的职责角色（{role_label}）约束自己的发言方向，但不要在输出中写出"我的职责是XXX"这种话
- 必须结合用户输入的具体内容，不要泛泛而谈
- 控制在400字以内，精炼有力"""

        try:
            content = _call_llm(llm, prompt)
            add_turn(session, f"{expert.name}（{role_label}）", content)
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
    开场白写入 session.turns，role 为"主持人"。
    """
    memory_context = load_memory_context()
    memory_block = _memory_prompt_block(memory_context)

    original_input = session.original_input.strip()
    if len(original_input) > 400:
        original_input_summary = original_input[:400] + "..."
    else:
        original_input_summary = original_input

    valid_experts = [e for e in experts if isinstance(e, ExpertAgent)]
    total = len(valid_experts)
    expert_idx = 0

    experts_lines = []
    for expert in experts:
        if isinstance(expert, ExpertAgent):
            role_label = _get_role_config(expert_idx, total)["label"]
            experts_lines.append(f"- {expert.name}（{expert.category}）→ 本轮职责：{role_label}")
            expert_idx += 1
        elif isinstance(expert, dict):
            name = expert.get("name", expert.get("id", "未知专家"))
            experts_lines.append(f"- {name} → 本轮职责：待定")
    experts_list = "\n".join(experts_lines) if experts_lines else "（暂无专家）"

    plan_text = "\n".join(f"- {item}" for item in discussion_plan) if discussion_plan else "（待定）"

    prompt = f"""你是 AI 圆桌会议主持人。

请用简洁的中文做开场白，介绍：
1. 本次讨论的核心议题（基于用户输入概括）
2. 参与本次讨论的专家名单和各自职责
3. 讨论计划
4. 如有历史上下文，简要提及上一次讨论的关键结论或待办，说明本次将如何在此基础上推进

【用户原始输入摘要】
{original_input_summary}

【参与专家及职责】
{experts_list}

【讨论计划】
{plan_text}
{memory_block}
输出要简洁，不超过300字，使用中文。"""

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
