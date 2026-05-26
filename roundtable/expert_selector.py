import json
import re

from roundtable.agent_registry import AgentRegistry

DOMAIN_KEYWORDS = {
    "product": ["需求", "用户", "痛点", "PRD", "功能", "MVP", "产品", "路线图", "优先级", "feature", "requirement"],
    "design": ["体验", "界面", "交互", "用户流程", "UI", "UX", "可用性", "原型", "设计"],
    "engineering": ["开发", "架构", "接口", "数据库", "技术", "性能", "部署", "代码", "API", "系统"],
    "marketing": ["增长", "获客", "投放", "转化", "渠道", "内容", "SEO", "推广", "运营"],
    "sales": ["客户", "成交", "线索", "销售", "报价", "CRM", "商务"],
    "finance": ["成本", "收入", "定价", "利润", "预算", "商业模式", "付费", "变现", "ROI"],
    "strategy": ["战略", "定位", "竞争", "市场", "壁垒", "差异化", "竞品", "方向"],
    "support": ["客服", "投诉", "工单", "用户反馈", "售后", "服务"],
    "testing": ["测试", "质量", "bug", "验收", "稳定性", "QA"],
    "project-management": ["排期", "项目", "里程碑", "负责人", "风险", "进度", "计划", "deadline"],
    "specialized": ["安全", "合规", "隐私", "数据", "法律", "监管", "风控"],
    "academic": ["研究", "分析", "报告", "数据分析", "调研"],
}

_FALLBACK_DISCUSSION_PLAN = [
    "明确议题背景与目标",
    "多角度分析与碰撞",
    "归纳结论与行动项",
]


def _match_domains(user_input: str) -> list:
    text = user_input.casefold()
    matched = []
    for domain, keywords in DOMAIN_KEYWORDS.items():
        for keyword in keywords:
            if keyword.casefold() in text:
                matched.append(domain)
                break
    return matched


def _append_candidates(candidates: list, seen_ids: set, agents: list, per_category_limit: int) -> None:
    added = 0
    for agent in agents:
        if agent.id in seen_ids:
            continue
        seen_ids.add(agent.id)
        candidates.append(agent)
        added += 1
        if added >= per_category_limit:
            break


def select_candidate_agents(user_input: str, registry: AgentRegistry, max_candidates: int = 15) -> list:
    """
    根据 DOMAIN_KEYWORDS 扫描 user_input，找出匹配的分类。
    从每个匹配分类中取最多 2 个专家加入候选列表。
    如果匹配分类不足，补充 product 和 strategy 分类的专家。
    最终返回不超过 max_candidates 个专家（ExpertAgent 对象列表，去重）。
    """
    matched_domains = _match_domains(user_input)
    candidates: list = []
    seen_ids: set = set()

    for domain in matched_domains:
        _append_candidates(candidates, seen_ids, registry.list_by_category(domain), 2)
        if len(candidates) >= max_candidates:
            return candidates[:max_candidates]

    if len(matched_domains) < 2:
        for domain in ("product", "strategy"):
            _append_candidates(candidates, seen_ids, registry.list_by_category(domain), 2)
            if len(candidates) >= max_candidates:
                return candidates[:max_candidates]

    return candidates[:max_candidates]


def extract_json_from_text(text: str) -> str:
    """
    从 LLM 返回的文本中提取 JSON 字符串。
    先尝试直接 json.loads；
    失败则用正则找第一个 { 到最后一个 } 之间的内容再试；
    都失败则返回空字符串。
    """
    if not text:
        return ""

    stripped = text.strip()
    try:
        json.loads(stripped)
        return stripped
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", stripped, re.DOTALL)
    if not match:
        return ""

    candidate = match.group(0)
    try:
        json.loads(candidate)
        return candidate
    except json.JSONDecodeError:
        return ""


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


def _build_fallback_selection(candidates: list) -> dict:
    return {
        "topic_type": "未分类议题",
        "recommended_experts": [
            {
                "id": agent.id,
                "name": agent.name,
                "reason": "规则初筛推荐",
            }
            for agent in candidates[:5]
        ],
        "missing_perspectives": [],
        "discussion_plan": list(_FALLBACK_DISCUSSION_PLAN),
    }


def select_experts_with_llm(llm, user_input: str, candidates: list, max_experts: int = 7) -> dict:
    """
    把候选专家列表和用户输入交给 LLM，让它选出最合适的 3-7 个专家。

    返回格式（dict）：
    {
      "topic_type": "本次议题类型",
      "recommended_experts": [
        {"id": "专家id", "name": "专家名", "reason": "选择原因"}
      ],
      "missing_perspectives": ["用户没想到但重要的视角"],
      "discussion_plan": ["第一轮讨论什么", "第二轮讨论什么", "如何收敛"]
    }

    如果 LLM 返回非法 JSON，则降级处理：直接用候选列表的前 5 个专家构造返回值。
    """
    if not candidates:
        return _build_fallback_selection([])

    candidates_payload = [
        {
            "id": agent.id,
            "name": agent.name,
            "category": agent.category,
            "description": agent.description[:200],
        }
        for agent in candidates
    ]
    candidates_json = json.dumps(candidates_payload, ensure_ascii=False, indent=2)

    prompt = f"""你是一个 AI 圆桌会议的专家调度器。

你的任务是根据用户输入，从候选专家列表中选出最适合参与本次讨论的专家。

规则：
1. 不要只选产品经理视角，要主动补充用户可能没想到但重要的视角。
2. 最少选 3 个专家，最多选 {max_experts} 个专家。
3. 涉及产品需求时，通常需要产品、用户研究、技术、项目管理视角。
4. 涉及商业化、获客时，加入营销、销售或财务视角。
5. 涉及数据、隐私、安全时，加入安全或合规视角。
6. 输入模糊时，加入 strategy 类专家澄清方向。
7. 输出必须是合法 JSON，不要输出任何 Markdown 标记或代码块。

用户输入：
{user_input}

候选专家列表（JSON）：
{candidates_json}

请直接输出 JSON，格式如下：
{{
  "topic_type": "本次议题类型",
  "recommended_experts": [
    {{"id": "专家id", "name": "专家名", "reason": "为什么需要这个专家"}}
  ],
  "missing_perspectives": ["用户没有主动提到但应该考虑的视角"],
  "discussion_plan": ["第一轮讨论什么", "第二轮讨论什么", "第三轮如何收敛"]
}}"""

    try:
        response = llm.call([{"role": "user", "content": prompt}])
        raw_text = _llm_response_to_text(response)
        json_str = extract_json_from_text(raw_text)
        if json_str:
            parsed = json.loads(json_str)
            if isinstance(parsed, dict) and parsed.get("recommended_experts"):
                return parsed
    except Exception:
        pass

    return _build_fallback_selection(candidates)


def auto_select_experts(llm, user_input: str, registry: AgentRegistry, max_experts: int = 7) -> dict:
    """
    完整的专家选择流程：
    1. 调用 select_candidate_agents 初筛候选专家
    2. 调用 select_experts_with_llm 精选
    3. 根据精选结果，从 registry 中取出完整的 ExpertAgent 对象列表
    4. 返回：
    {
      "topic_type": str,
      "experts": [ExpertAgent, ...],   # 完整专家对象
      "reasons": {"专家id": "原因"},
      "missing_perspectives": [...],
      "discussion_plan": [...]
    }
    """
    candidates = select_candidate_agents(user_input, registry)
    selection = select_experts_with_llm(llm, user_input, candidates, max_experts=max_experts)

    experts = []
    reasons = {}
    for item in selection.get("recommended_experts", [])[:max_experts]:
        if not isinstance(item, dict):
            continue
        agent_id = item.get("id")
        if not agent_id:
            continue
        agent = registry.get_by_id(agent_id)
        if agent is None:
            continue
        experts.append(agent)
        reasons[agent_id] = item.get("reason", "")

    if not experts:
        experts = candidates[:5]
        reasons = {agent.id: "规则初筛推荐" for agent in experts}

    return {
        "topic_type": selection.get("topic_type", "未分类议题"),
        "experts": experts,
        "reasons": reasons,
        "missing_perspectives": selection.get("missing_perspectives", []),
        "discussion_plan": selection.get("discussion_plan", []),
    }
