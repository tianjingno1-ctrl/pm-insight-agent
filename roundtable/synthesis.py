# -*- coding: utf-8 -*-
import re
from datetime import datetime
from pathlib import Path

from roundtable.session import RoundtableSession, format_turns_for_prompt, save_session

REPORTS_DIR = Path("output/reports")
MEMORY_INSIGHTS = Path("memory/insights.md")
MEMORY_DECISIONS = Path("memory/decisions.md")
MEMORY_TODOS = Path("memory/todos.md")


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


def _call_llm(llm, prompt: str, *, tag: str = "LLM") -> str:
    try:
        response = llm.call([{"role": "user", "content": prompt}])
        result = _llm_response_to_text(response).strip()
        if not result:
            print(f"[{tag}] 生成失败：模型返回空内容")
        return result
    except Exception as e:
        print(f"[{tag}] 生成失败：{e}")
        return ""


def _truncate_context(full_context: str, max_chars: int = 3000) -> str:
    """只保留最近 max_chars 字符的上下文。"""
    if len(full_context) <= max_chars:
        return full_context
    return full_context[-max_chars:]


def _get_turns_text(session: RoundtableSession) -> str:
    turns = format_turns_for_prompt(session, max_chars=20000)
    return turns if turns.strip() else "（暂无讨论记录）"


def _build_summary_context(session: RoundtableSession) -> str:
    turns = _get_turns_text(session)
    full_context = f"{session.original_input}\n\n{session.current_context}\n\n{turns}"
    return _truncate_context(full_context, 3000)


def _extract_one_line_conclusion(report: str) -> str:
    match = re.search(
        r"##\s*1\.\s*一句话结论\s*\n+(.*?)(?=\n##\s|\Z)",
        report,
        re.DOTALL,
    )
    if match:
        return match.group(1).strip()
    return "（未能从报告中提取一句话结论）"


def _append_memory_file(path: Path, block: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    separator = "" if not existing or existing.endswith("\n") else "\n"
    path.write_text(f"{existing}{separator}{block}\n", encoding="utf-8")


def synthesize_roundtable_report(
    llm,
    session: RoundtableSession,
    project_context: str,
    print_output: bool = True,
) -> str:
    """
    将整个圆桌会议 session 整合为最终 Markdown 报告。
    返回报告文本字符串。
    """
    context_text = _build_summary_context(session)
    project_ctx = _truncate_context(project_context, 1500)

    prompt = f"""你是资深产品负责人和 AI 圆桌会议总编辑。

请基于以下完整讨论记录，生成一份可直接给产品经理使用的中文 Markdown 报告。
不要简单罗列专家原话，要做判断和整合。如果信息不足，明确标记"待确认"。

【项目背景】
{project_ctx}

【讨论上下文（保留最近内容）】
{context_text}

请严格按以下结构输出（不可省略任何章节标题）：

# AI 圆桌会议总结报告

## 1. 一句话结论
（用一句话说明本次讨论最重要的判断）

## 2. 背景与问题定义
（说明本次讨论的核心问题是什么）

## 3. 专家观点摘要
| 专家 | 核心观点 | 主要担忧 | 建议 |
|------|----------|----------|------|

## 4. 共识结论
（列出所有专家共同支持的判断）

## 5. 关键分歧
（列出不同专家之间的冲突观点，并说明如何决策）

## 6. 被忽略但重要的视角
（用户一开始没有想到，但专家补充出来的重要角度）

## 7. 产品机会
（可以转化为哪些功能、流程、服务或商业机会）

## 8. PRD 初稿
### 背景
### 目标
### 用户画像
### 用户故事
### 功能范围
### MVP 范围
### 非功能需求
### 验收标准
### 数据指标

## 9. 风险清单
| 风险 | 影响 | 概率 | 应对策略 | 负责人建议 |
|------|------|------|----------|------------|

## 10. Backlog
| 需求 | 优先级 | 用户价值 | 复杂度 | 建议版本 |
|------|--------|----------|--------|----------|

## 11. 下一步行动项
| 任务 | 负责人建议 | 优先级 | 预计产出 |
|------|------------|--------|----------|

## 12. 建议下一轮继续讨论的问题
1.
2.
3.
4.
5."""

    print("📝 正在生成报告，请稍候（最长 60 秒）...")
    report = _call_llm(llm, prompt, tag="SUMMARY")
    if not report:
        report = "# AI 圆桌会议总结报告\n\n报告生成失败，请缩短讨论内容后重试。\n"

    if print_output:
        print()
        print("-" * 40)
        print("📄 圆桌会议总结报告已生成")
        print("-" * 40)
        print()
        print(report)
        print()

    return report


def save_report(content: str, session_id: str) -> Path:
    """
    保存报告到 output/reports/roundtable_{session_id}.md。
    返回保存路径。
    """
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    path = REPORTS_DIR / f"roundtable_{session_id}.md"
    path.write_text(content, encoding="utf-8")
    return path


def generate_prd_only(
    llm,
    session: RoundtableSession,
    project_context: str,
    print_output: bool = True,
) -> str:
    """
    只生成 PRD 部分，不生成完整报告。
    适合用户输入 PRD 指令时调用。
    返回 PRD 文本字符串。
    """
    context_text = _build_summary_context(session)
    project_ctx = _truncate_context(project_context, 1500)

    prompt = f"""你是资深产品经理。

请基于以下讨论记录，生成一份结构清晰的中文 PRD 初稿。

【项目背景】
{project_ctx}

【讨论记录（保留最近内容）】
{context_text}

请输出以下结构：

# PRD 初稿

## 背景与目标

## 目标用户

## 用户故事
（格式：作为[用户角色]，我希望[功能]，以便[价值]）

## 功能需求
| 功能模块 | 描述 | 优先级 | 验收标准 |
|----------|------|--------|----------|

## MVP 范围

## 非功能需求

## 风险与假设"""

    print("📝 正在生成 PRD，请稍候（最长 60 秒）...")
    prd = _call_llm(llm, prompt, tag="PRD")
    if not prd:
        prd = "# PRD 初稿\n\nPRD 生成失败，请缩短讨论内容后重试。\n"

    if print_output:
        print()
        print("-" * 40)
        print("📝 PRD 初稿已生成")
        print("-" * 40)
        print()
        print(prd)
        print()

    return prd


def update_memory_files(session: RoundtableSession, report: str) -> None:
    """
    在报告生成后，把关键信息追加写入：
    - memory/insights.md：追加本次讨论的一句话结论和日期
    - memory/decisions.md：追加本次达成的决策（从 session.decisions 读取）
    - memory/todos.md：追加本次待办事项（从 session.todos 读取）

    如果文件不存在则自动创建。
    """
    date_str = session.updated_at or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    header = f"## {session.title} ({session.session_id})\n日期：{date_str}\n"

    conclusion = _extract_one_line_conclusion(report)
    insights_block = f"{header}一句话结论：{conclusion}\n---\n"
    _append_memory_file(MEMORY_INSIGHTS, insights_block)

    if session.decisions:
        decisions_body = "\n".join(f"- {item}" for item in session.decisions)
    else:
        decisions_body = "（本次暂无记录决策）"
    decisions_block = f"{header}{decisions_body}\n---\n"
    _append_memory_file(MEMORY_DECISIONS, decisions_block)

    if session.todos:
        todos_body = "\n".join(f"- {item}" for item in session.todos)
    else:
        todos_body = "（本次暂无记录待办）"
    todos_block = f"{header}{todos_body}\n---\n"
    _append_memory_file(MEMORY_TODOS, todos_block)
