import re
from typing import Any, Dict, List, Optional, Set, Tuple

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
    # 仅保留较短尾部，减少脏文本诱导病句复读
    ctx = memory_context.strip()
    if len(ctx) > 1200:
        ctx = ctx[-1200:]
    return f"""
---
【历史参考（仅供背景；勿照抄措辞；若见病句、错词请忽略并用自然中文改写）】
{ctx}
---
"""


_EXPERT_DISPLAY_NAME = {
    "product": "产品专家",
    "tech": "技术专家",
    "growth": "增长专家",
    "risk": "风险专家",
    "design": "体验设计专家",
    "strategy": "战略专家",
    "priority": "优先级专家",
    "unknown": "专家",
}

_EXPERT_ANGLE = {
    "product": "功能边界与 MVP 取舍",
    "tech": "实现路径与工程取舍",
    "growth": "需求验证与成功信号",
    "risk": "误判、合规与数据可靠性",
    "design": "最小交互与可理解性",
    "strategy": "商业取舍与是否值得做",
    "priority": "优先级与排期取舍",
    "unknown": "专业判断",
}

# 每位专家只谈一个维度（禁止与其他角色混用）
_EXPERT_LENS = {
    "product": "只谈功能边界和该砍什么，不谈技术实现细节",
    "tech": "只谈最快实现路径和工程取舍，不谈商业战略",
    "growth": "只谈找谁验证、怎么判断需求有价值，不谈功能清单堆砌",
    "risk": "只谈数据可靠性、误判和合规边界，不谈功能设计",
    "design": "只谈最小交互和用户是否看得懂，不谈排期",
    "strategy": "只谈商业取舍和是否值得做，不谈接口细节",
    "priority": "只谈优先级与排期取舍",
    "unknown": "只补充一个其他专家尚未覆盖的新角度",
}

# 长短语优先，避免「需求」「用户」等泛词把一切判成 product
_INFER_PHRASE_RULES = [
    ("product", ("用户痛点", "功能边界", "mvp", "prd", "产品经理", "产品策略")),
    ("tech", ("技术专家", "engineering", "机器学习", "数据接入", "工程取舍")),
    ("growth", ("增长专家", "需求验证", "用户访谈", "成功信号", "获客")),
    ("risk", ("合规风险", "数据可靠", "隐私合规", "风控")),
    ("design", ("体验设计", "交互设计", "可用性")),
    ("strategy", ("商业模式", "商业取舍", "竞争格局")),
]

_INFER_WORD_RULES = [
    ("tech", ("技术", "工程", "架构", "开发", "api", "engineer", "engineering", "ai", "数据", "算法", "部署")),
    ("growth", ("增长", "验证", "访谈", "市场", "marketing", "运营", "转化", "调研")),
    ("risk", ("风险", "合规", "法务", "安全", "legal", "security", "隐私", "监管")),
    ("design", ("设计", "体验", "交互", "ui", "ux", "原型")),
    ("strategy", ("战略", "商业", "定价", "竞争", "strategy", "壁垒")),
    ("product", ("产品", "mvp", "功能", "pm", "product")),
    ("priority", ("优先级", "roadmap", "排期", "里程碑", "project-management")),
]

_CATEGORY_TO_KEY = {
    "product": "product",
    "engineering": "tech",
    "marketing": "growth",
    "specialized": "risk",
    "design": "design",
    "strategy": "strategy",
    "project-management": "priority",
    "finance": "strategy",
    "sales": "growth",
}

BAD_PHRASE_REPLACEMENTS = {
    "最大封闭": "最大分歧",
    "最大闭合": "最大分歧",
    "当前走势": "当前倾向",
    "当前热点": "当前倾向",
    "当前趋势": "当前倾向",
    "目前趋势": "当前倾向",
    "惨见底": "现金见底",
    "资金底见": "资金见底",
    "一句话积分": "一句话提示",
    "解析呼吸": "解析格式",
    "网银回收格式": "网银流水格式",
    "网银还原格式": "网银流水格式",
    "回收格式": "流水格式",
    "胎儿焦虑症": "现金流焦虑",
    "最小闭环收收": "最小闭环",
    "7日可依赖离线关闭完成环": "7日内可用离线规则完成闭环",
    "合规跑上": "合规上",
    "数据地第三方共享": "数据的第三方共享",
    "老赢回": "老板赢回",
    "内无法闭环": "短期内无法闭环",
    "未来7天只缺口": "未来7天现金缺口",
    "抢夺入口": "抢占入口",
    "数据地第三方共享条款": "数据的第三方共享条款",
    "老赢回现金折扣": "老板赢回的现金折扣",
    "最大成交量": "最大分歧",
    "最大加密": "最大分歧",
    "生长专家": "增长专家",
    "实际产权": "实际产品",
    "忽视合雷区": "忽视合规雷区",
    "四内可交付": "四天内可交付",
    "货运传输": "数据传输",
    "第三方货运传输": "第三方数据传输",
    "数据上知情": "数据知情",
    "更多参与参与": "更多参与",
    "上方准确复述": "准确复述",
    "剩余预警": "余额预警",
    "至少一个积分": "至少一个提示",
    "复述积分": "复述要点",
}

# 长词优先替换，避免短词误伤
_BAD_PHRASES_SORTED = sorted(BAD_PHRASE_REPLACEMENTS.keys(), key=len, reverse=True)

CURRENT_ALIASES = (
    "当前倾向",
    "当前趋势",
    "当前走势",
    "当前热点",
    "目前趋势",
)
DISAGREEMENT_ALIASES = (
    "最大分歧",
    "最大封闭",
    "最大闭合",
    "最大成交量",
    "最大加密",
)
NEXT_ALIASES = (
    "下一步建议",
    "下一步",
)

# 兼容旧内部引用
_SUMMARY_LABEL_TENDENCY = CURRENT_ALIASES
_SUMMARY_LABEL_DISAGREEMENT = DISAGREEMENT_ALIASES
_SUMMARY_LABEL_NEXT = NEXT_ALIASES

BAD_LANGUAGE_MARKERS = (
    "疑识别",
    "预测与精度",
    "算30天补",
    "致命置信度",
    "前期前看不懂",
    "漂移生成",
    "绝望紧张",
    "复述极限",
    "预算一个",
    "浪费资金缺口",
    "最终生成周末可测",
    "紧张的上涨",
    "高于好评崩溃",
    "结果付费快捷键",
    "抽取小额信贷",
    "生长专家",
    "主机",
    "货运传输",
    "实际产权",
    "忽视合雷区",
    "四内可交付",
    "添加成分",
    "剩余预警",
    "上方准确复述",
    "更多参与参与",
    "数据上知情",
    "一大笔钱",
    "报表必须解读",
    "复述积分",
    "第三方货运",
)


def infer_speaker_key_from_text(blob: str) -> str:
    """从文本推断角色；unknown 不回落到 product。"""
    text = (blob or "").lower()
    if not text.strip():
        return "unknown"
    for key, phrases in _INFER_PHRASE_RULES:
        if any(p.lower() in text for p in phrases):
            return key
    for key, words in _INFER_WORD_RULES:
        if any(w.lower() in text for w in words):
            return key
    return "unknown"


def get_assigned_speaker_key(expert: ExpertAgent) -> str:
    assigned = getattr(expert, "assigned_speaker_key", None)
    if assigned:
        return assigned
    return infer_speaker_key_from_expert(expert)


def assign_speaker_key(expert: ExpertAgent, speaker_key: str) -> None:
    expert.assigned_speaker_key = speaker_key


def infer_speaker_key_from_expert(expert: ExpertAgent) -> str:
    assigned = getattr(expert, "assigned_speaker_key", None)
    if assigned:
        return assigned
    cat = (expert.category or "").casefold()
    if cat in _CATEGORY_TO_KEY:
        return _CATEGORY_TO_KEY[cat]
    blob = f"{expert.id} {expert.name} {expert.category}"
    return infer_speaker_key_from_text(blob)


def expert_display_name(expert: ExpertAgent) -> str:
    key = get_assigned_speaker_key(expert)
    return _EXPERT_DISPLAY_NAME.get(key, _EXPERT_DISPLAY_NAME["unknown"])


def _expert_lens(expert: ExpertAgent) -> str:
    key = get_assigned_speaker_key(expert)
    return _EXPERT_LENS.get(key, _EXPERT_LENS["unknown"])


def _expert_labels_and_angles(experts: List[Any]) -> Tuple[List[str], List[str]]:
    labels, angles = [], []
    for expert in experts:
        if not isinstance(expert, ExpertAgent):
            continue
        key = get_assigned_speaker_key(expert)
        labels.append(_EXPERT_DISPLAY_NAME.get(key, "专家"))
        angles.append(_EXPERT_ANGLE.get(key, "专业判断"))
    return labels, angles


def sanitize_discussion_text(text: str) -> str:
    """清洗讨论文本：替换病句/错词、压缩重复与空行。"""
    if not text:
        return ""
    result = str(text)
    for bad in _BAD_PHRASES_SORTED:
        result = result.replace(bad, BAD_PHRASE_REPLACEMENTS[bad])
    result = re.sub(r"(预警)\1+", r"\1", result)
    result = re.sub(r"([\u4e00-\u9fa5]{2,6})\1+", r"\1", result)
    result = re.sub(r"本轮小结\s*\n+\s*本轮小结", "\n", result)
    result = re.sub(r"#{1,6}\s*本轮小结\s*", "\n", result)
    result = re.sub(r"\n{3,}", "\n\n", result)
    return result.strip()


DEFAULT_CURRENT = "本轮尚未形成明确倾向。"
DEFAULT_DISAGREEMENT = "暂无明显分歧。"
DEFAULT_NEXT = "继续补充约束后再讨论。"

# 兼容旧常量名
_SUMMARY_DEFAULT_TENDENCY = DEFAULT_CURRENT
_SUMMARY_DEFAULT_DISAGREEMENT = DEFAULT_DISAGREEMENT
_SUMMARY_DEFAULT_NEXT_STEP = DEFAULT_NEXT


def _strip_summary_headers(text: str) -> str:
    text = text or ""
    text = text.replace("## 本轮小结", "\n")
    text = text.replace("### 本轮小结", "\n")
    text = text.replace("🏁 本轮小结", "\n")
    text = text.replace("本轮小结", "\n")
    return text


def _clean_summary_value(value: str) -> str:
    """清洗单字段小结值（不是整段 markdown）。"""
    value = value or ""
    value = sanitize_discussion_text(value)

    value = re.sub(r"^[\s\-•*：:]+", "", value).strip()

    all_aliases = list(CURRENT_ALIASES) + list(DISAGREEMENT_ALIASES) + list(NEXT_ALIASES)
    for alias in all_aliases:
        value = re.sub(rf"^{re.escape(alias)}\s*[：:]\s*", "", value).strip()

    split_markers = list(all_aliases) + ["##", "本轮小结"]
    for marker in split_markers:
        idx = value.find(marker)
        if idx > 0:
            value = value[:idx].strip()

    value = re.sub(r"\s+", " ", value).strip()

    if value in all_aliases + ["待确认", ""]:
        return ""
    return value


def _extract_after_any(text: str, aliases: Tuple[str, ...]) -> str:
    text = _strip_summary_headers(text or "")

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    all_field_aliases = list(CURRENT_ALIASES) + list(DISAGREEMENT_ALIASES) + list(NEXT_ALIASES)

    for line in lines:
        clean_line = re.sub(r"^[\-•*\s]+", "", line).strip()
        for alias in aliases:
            match = re.match(rf"^{re.escape(alias)}\s*[：:]?\s*(.*)$", clean_line)
            if match:
                val = _clean_summary_value(match.group(1))
                if val:
                    return val

    alias_pattern = "|".join(re.escape(a) for a in aliases)
    stop_aliases = [a for a in all_field_aliases if a not in aliases]
    stop_pattern = "|".join(re.escape(a) for a in stop_aliases)

    if stop_pattern:
        pattern = rf"({alias_pattern})\s*[：:]\s*(.*?)(?=\n\s*(?:{stop_pattern})\s*[：:]|$)"
    else:
        pattern = rf"({alias_pattern})\s*[：:]\s*(.*)$"

    match = re.search(pattern, text, flags=re.S)
    if match:
        val = _clean_summary_value(match.group(2))
        if val:
            return val

    return ""


def _build_summary_three_lines(current: str, disagreement: str, next_step: str) -> str:
    """永远输出标准三行，不保留模型自由标题。"""
    current = _clean_summary_value(current) or DEFAULT_CURRENT
    disagreement = _clean_summary_value(disagreement) or DEFAULT_DISAGREEMENT
    next_step = _clean_summary_value(next_step) or DEFAULT_NEXT
    return (
        "## 本轮小结\n"
        f"- 当前倾向：{current}\n"
        f"- 最大分歧：{disagreement}\n"
        f"- 下一步建议：{next_step}"
    )


def force_summary_markdown(text: str) -> str:
    """
    强制小结格式：永远抽取 → 清洗 → 重建三行。
    禁止任何「看起来已格式化就 return 原文」的逻辑。
    """
    text = sanitize_discussion_text(text or "")

    current = _extract_after_any(text, CURRENT_ALIASES)
    disagreement = _extract_after_any(text, DISAGREEMENT_ALIASES)
    next_step = _extract_after_any(text, NEXT_ALIASES)

    return _build_summary_three_lines(current, disagreement, next_step)


def format_round_summary(tendency: str, disagreement: str, next_step: str) -> str:
    return _build_summary_three_lines(tendency, disagreement, next_step)


def _format_round_summary(tendency: str, disagreement: str, next_step: str) -> str:
    return format_round_summary(tendency, disagreement, next_step)


def has_bad_language(text: str) -> bool:
    """检测明显病句/错词（词表 + 规则）。"""
    if not text or not text.strip():
        return False
    for marker in BAD_LANGUAGE_MARKERS:
        if marker in text:
            return True
    for bad in BAD_PHRASE_REPLACEMENTS:
        if bad in text:
            return True
    if re.search(r"不用[^，。]{0,20}合规风险$", text):
        return True
    if "一大笔钱" in text:
        return True
    if re.search(r"真实情况$", text.strip()):
        return True
    if "积分" in text and "一句话" not in text:
        return True
    return False


def polish_discussion_text(llm, text: str, role: str = "") -> str:
    """用 LLM 将病句改写为自然中文（不增新观点）。"""
    if not text or not text.strip():
        return text
    prompt = f"""请把下面这段话改写成自然、通顺、专业的中文会议发言。
要求：
- 保留原意
- 不增加新观点
- 删除错词和病句
- 不要出现「积分、生长专家、主机、货运传输、实际产权」等明显错误词
- 最多100字
- 只输出一段话

发言角色：{role or "专家"}

原文：
{text}"""
    try:
        polished = _call_llm(llm, prompt)
        return polished.strip() if polished and polished.strip() else text
    except Exception:
        return text


def format_turns_slice(turns: List[Any], max_chars: int = 4000) -> str:
    """将 turns 子集格式化为 prompt 文本。"""
    if not turns:
        return "（本轮暂无讨论）"

    blocks: List[str] = []
    for turn in turns:
        if isinstance(turn, dict):
            role = turn.get("role", "")
            content = turn.get("content", "")
        else:
            role = turn.role
            content = turn.content
        blocks.append(f"## {role}\n{content}\n")

    selected: List[str] = []
    total = 0
    for block in reversed(blocks):
        if selected and total + len(block) > max_chars:
            break
        selected.append(block)
        total += len(block)
    selected.reverse()
    return "".join(selected) if selected else blocks[-1][:max_chars]


def _first_summary_field(data: dict, *keys: str, default: str = "待确认") -> str:
    for key in keys:
        value = data.get(key)
        if value is None:
            continue
        if isinstance(value, list):
            for item in value:
                text = str(item).strip()
                if text:
                    return text
            continue
        text = str(value).strip()
        if text:
            return text
    return default


_OUTPUT_RULES = """
【输出格式（违反即视为失败）】
你只能输出一段自然中文。
不要分段。
不要写标题。
不要写 Markdown。
不要写列表。
最多 120 个中文字符。
最多 3 句话。
必须从你的专家角色给出一个新角度，不能重复上一位专家已经说过的结论。
如果你同意上一位，只能用半句话确认，然后立刻补充新的执行、技术、验证、风险或设计角度。
禁止使用不自然词或错词，例如：最大封闭、当前趋势、目前趋势、惨见底、积分、抢夺入口、解析呼吸。
如果历史里出现这些词，请用自然中文改写，不要照抄。
"""


def _truncate_expert_prompt(prompt: str, max_chars: int = 600) -> str:
    text = (prompt or "").strip()
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n…（角色说明已截断）"


def _enforce_short_speech(text: str, max_chars: int = 120, max_sentences: int = 3) -> str:
    """后处理：强制短发言，去掉 Markdown/列表。"""
    if not text:
        return text
    cleaned = text.strip()
    cleaned = re.sub(r"#{1,6}\s*", "", cleaned)
    cleaned = re.sub(r"\*\*([^*]+)\*\*", r"\1", cleaned)
    cleaned = re.sub(r"^[\-\*•]\s+", "", cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r"\n+", " ", cleaned).strip()
    parts = re.split(r"(?<=[。！？!?])\s*", cleaned)
    parts = [p.strip() for p in parts if p.strip()]
    if not parts:
        parts = [cleaned]
    parts = parts[:max_sentences]
    result = "".join(parts)
    if len(result) > max_chars:
        result = result[:max_chars].rstrip("，。；、 ") + "。"
    return result


def _followup_prompt_block(round_index: int, followup: str) -> str:
    if not followup.strip():
        return ""
    return f"""
【本轮追问上下文】
这是第 {round_index} 轮讨论。
用户本轮追问/反馈是：「{followup}」
请基于此前上下文继续讨论，不要重复上一轮已经说过的内容。
"""


def _first_speaker_hint(is_followup: bool, is_first_in_round: bool) -> str:
    if not is_first_in_round:
        return (
            "- 先点名回应上一位的具体观点；若同意，一句话带过即可，"
            "然后必须给出上一位没提到的新信息，禁止复读。"
        )
    if is_followup:
        return "- 你是本轮第一位发言：回应主持人开场，并直接针对用户本轮追问表态。"
    return "- 你是本轮第一位发言：回应主持人开场，直接给出你的判断。"


_ROLE_PROPOSER = {
    "label": "方案提出者",
    "instruction": (
        "你的职责是【方案提出者】：用一句话点明核心判断，再给出一个可执行的第一步行动。"
    ),
}

_ROLE_DEVIL = {
    "label": "魔鬼代言人",
    "instruction": (
        "你的职责是【魔鬼代言人】：针对前面方案，点出一个最脆弱的假设和后果，再给一句修改建议。"
    ),
}

_ROLE_IMPLEMENTER = {
    "label": "落地拆解者",
    "instruction": (
        "你的职责是【落地拆解者】：用口语列出 1-2 条最关键的可执行任务，并点出一个仍未解决的问题。"
    ),
}

_ROLE_VALIDATOR = {
    "label": "补充验证者",
    "instruction": (
        "你的职责是【补充验证者】：指出一个前面没人提到的风险或机会，并说明为何重要。"
    ),
}

_ROLE_PROPOSER_IMPLEMENTER = {
    "label": "方案提出者+落地拆解者",
    "instruction": (
        "你同时承担【方案提出者】和【落地拆解者】：先给核心判断与第一步行动，再补 1 条关键任务。"
    ),
}

_ROLE_DEVIL_IMPLEMENTER = {
    "label": "魔鬼代言人+落地拆解者",
    "instruction": (
        "你同时承担【魔鬼代言人】和【落地拆解者】：先挑一个关键漏洞，再补 1 条落地任务。"
    ),
}

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
    followup: str = "",
    is_followup: bool = False,
    round_index: int = 1,
) -> None:
    """
    按专家人数动态分配圆桌角色后，依次发言。
    """
    memory_context = load_memory_context()
    memory_block = _memory_prompt_block(memory_context)
    followup_block = _followup_prompt_block(round_index, followup) if is_followup else ""

    valid_experts = [e for e in experts if isinstance(e, ExpertAgent)]
    total = len(valid_experts)
    spoken_count = 0
    expert_idx = 0
    first_in_round = True

    for expert in experts:
        if not isinstance(expert, ExpertAgent):
            continue

        role_config = _get_role_config(expert_idx, total)
        role_label = role_config["label"]
        expert_idx += 1
        speaker_key = get_assigned_speaker_key(expert)
        display_name = expert_display_name(expert)
        lens = _expert_lens(expert)

        if print_output:
            print()
            print("-" * 40)
            print(f"🎯 {display_name} [{role_label}]")
            print("-" * 40)

        previous_turns = format_turns_for_prompt(session, max_chars=8000)
        if not previous_turns.strip():
            previous_turns = "（暂无前序讨论）"

        first_hint = _first_speaker_hint(is_followup, first_in_round)

        role_brief = _truncate_expert_prompt(expert.prompt)

        prompt = f"""你现在扮演【{display_name}】，请严格站在该专家立场发言。

【你的专业视角（必须遵守，不得越界）】
{lens}

【专家背景（仅供参考，不要展开成长文）】
{role_brief}

【项目背景】
{project_context[:800]}

【用户原始输入】
{session.original_input[:800]}

【当前累积上下文】
{session.current_context[:600]}

【前面专家已发表的观点】
{previous_turns}

【本轮讨论目标】
{round_goal}
{followup_block}
{memory_block}

{first_hint}
- 你是{display_name}（职能键：{speaker_key}），只从本职能角度发言
- 不要模仿其他专家的措辞和结论

{_OUTPUT_RULES}"""

        try:
            raw = _call_llm(llm, prompt)
            clean = sanitize_discussion_text(raw)
            short = _enforce_short_speech(clean)
            polished = polish_discussion_text(llm, short, display_name)
            final = sanitize_discussion_text(_enforce_short_speech(polished))
            add_turn(session, f"{display_name}（{role_label}）", final)
            save_session(session)
            spoken_count += 1
            first_in_round = False
            if print_output:
                print()
                print(final)
        except Exception as exc:
            if print_output:
                print(f"[错误] 专家 {expert.name} 发言失败：{exc}")

    if print_output:
        print()
        print(f"✅ 本轮圆桌讨论完成，共 {spoken_count} 位专家发言。")


def _build_moderator_opening_text(
    session: RoundtableSession,
    experts: list,
    *,
    is_followup: bool = False,
    followup: str = "",
) -> str:
    """主持人开场由代码拼接，最多两句话，不调用 LLM。"""
    if is_followup and followup.strip():
        topic = followup.strip()
    else:
        topic = session.original_input.strip()
    if len(topic) > 160:
        topic = topic[:160] + "…"

    valid = [e for e in experts if isinstance(e, ExpertAgent)]
    labels, angles = _expert_labels_and_angles(valid)
    if not labels:
        return f"本轮只讨论：{topic}"

    label_text = "、".join(labels)
    angle_text = "、".join(angles)
    line1 = f"本轮只讨论：{topic}"
    line2 = f"请{label_text}分别从{angle_text}给判断。"
    return f"{line1}\n{line2}"


def run_moderator_opening(
    llm,
    session: RoundtableSession,
    experts: list,
    project_context: str,
    discussion_plan: list,
    print_output: bool = True,
    is_followup: bool = False,
    round_index: int = 1,
    followup: str = "",
) -> None:
    """
    主持人开场白。在专家发言前调用（文案由代码生成，避免模型乱编专家介绍）。
    """
    del llm, project_context, discussion_plan, round_index  # 保留签名兼容

    try:
        content = sanitize_discussion_text(
            _build_moderator_opening_text(
                session, experts, is_followup=is_followup, followup=followup
            )
        )
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


def run_moderator_closing(
    llm,
    session: RoundtableSession,
    print_output: bool = True,
    round_index: int = 1,
    round_start_index: int = 0,
    round_topic: str = "",
) -> None:
    """
    主持人收场总结。在所有专家发言后调用。
    内部解析 JSON 写入 session 字段；展示给用户的文案为轻量「本轮小结」。
    """
    current_turns = session.turns[round_start_index:] if round_start_index else list(session.turns)
    current_round_text = format_turns_slice(current_turns, max_chars=5000)
    earlier_turns = session.turns[:round_start_index] if round_start_index > 0 else []
    earlier_history = (
        format_turns_slice(earlier_turns, max_chars=2500)
        if earlier_turns
        else "（无更早轮次）"
    )
    topic = (round_topic or session.original_input or "").strip()
    if len(topic) > 500:
        topic = topic[:500] + "…"

    prompt = f"""你是 AI 圆桌会议主持人，现在需要对第 {round_index} 轮讨论做收场总结。

【本轮讨论主题（小结必须围绕此主题，不要被更早轮次带偏）】
{topic}

【本轮发言记录（小结必须主要依据此部分）】
{current_round_text}

【更早轮次背景（仅供参考，不要替代本轮结论；若本轮在讨论定价，不要只总结上一轮 MVP/Excel）】
{earlier_history}

请严格按照以下 JSON 格式输出，不要输出任何 JSON 以外的内容（展示文案由系统拼接，你只需填 JSON 值）：

{{
  "current_tendency": "当前倾向（一句话，自然中文）",
  "main_disagreement": "最大分歧（一句话，无则写「暂无明显分歧」）",
  "next_step": "下一步建议（一句话）",
  "decisions": [
    "结论1：具体可执行的决策（必须包含主语和动词）"
  ],
  "todos": [
    "任务1：[负责人角色] 在 [时间] 前完成 [具体事项]"
  ],
  "open_questions": [],
  "confidence": "高/中/低",
  "confidence_reason": "置信度判断理由，一句话"
}}

可选同义字段（若上面三项不好填，可填这些，系统会识别）：
- current_direction / decision 可代替 current_tendency
- main_dispute / disagreement / open_question 可代替 main_disagreement
- next_action / todo 可代替 next_step

要求：
- decisions 至少1条，最多5条
- todos 至少1条，每条必须有负责人角色和时间
- open_questions 如果没有可以为空列表
- 禁止病句、生造词；所有内容必须来自专家讨论，不要自行发明"""

    try:
        raw = _call_llm(llm, prompt)

        import json
        import re

        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            data = json.loads(match.group())
            session.decisions = data.get("decisions", [])
            session.todos = data.get("todos", [])
            session.open_questions = data.get("open_questions", [])

            tendency = _clean_summary_value(
                _first_summary_field(
                    data,
                    "current_tendency",
                    "current_direction",
                    "decision",
                    default="",
                )
            ) or DEFAULT_CURRENT
            disagreement = _clean_summary_value(
                _first_summary_field(
                    data,
                    "main_disagreement",
                    "main_dispute",
                    "disagreement",
                    default="",
                )
            ) or DEFAULT_DISAGREEMENT
            next_step = _clean_summary_value(
                _first_summary_field(
                    data,
                    "next_step",
                    "next_action",
                    "todo",
                    default="",
                )
            ) or DEFAULT_NEXT

            summary_text = _build_summary_three_lines(tendency, disagreement, next_step)

            add_turn(session, "主持人（总结）", summary_text)
            save_session(session)

            if print_output:
                print()
                print("-" * 40)
                print("🏁 主持人收场总结")
                print("-" * 40)
                print(summary_text)
        else:
            summary_text = _build_summary_three_lines("", "", "")
            add_turn(session, "主持人（总结）", summary_text)
            save_session(session)
            if print_output:
                print("[警告] 主持人总结 JSON 解析失败，已使用默认三行小结")

    except Exception as exc:
        if print_output:
            print(f"[错误] 主持人收场失败：{exc}")
