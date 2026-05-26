# -*- coding: utf-8 -*-
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

from roundtable.session import RoundtableSession, format_turns_for_prompt

REPORTS_DIR = Path("output/reports")
MEMORY_INSIGHTS = Path("memory/insights.md")
MEMORY_DECISIONS = Path("memory/decisions.md")
MEMORY_TODOS = Path("memory/todos.md")
MEMORY_OPEN_QUESTIONS = Path("memory/open_questions.md")


# ---------------------------------------------------------------------------
# 内部工具函数
# ---------------------------------------------------------------------------

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
    """
    兼容两种报告格式：
      - 旧格式：## 1. 一句话结论  （单行文本）
      - 新格式：## 结论            （bullet list，取第一条）
    """
    if not report or not str(report).strip():
        return "（未能从报告中提取一句话结论）"

    report = str(report)

    # ① 旧格式：## 1. 一句话结论
    match = re.search(
        r"##\s*1\.\s*一句话结论\s*\n+(.*?)(?=\n##\s|\Z)",
        report,
        re.DOTALL,
    )
    if match:
        text = match.group(1).strip()
        if text:
            first_line = next(
                (ln.strip() for ln in text.splitlines() if ln.strip()), ""
            )
            return first_line or text

    # ② 新格式：## 结论（bullet list，取第一条 bullet）
    match = re.search(
        r"##\s*结论\s*\n+(.*?)(?=\n##\s|\Z)",
        report,
        re.DOTALL,
    )
    if match:
        block = match.group(1).strip()
        bullet_match = re.search(r"^[-*]\s+(.+)", block, re.MULTILINE)
        if bullet_match:
            return bullet_match.group(1).strip()
        first_line = next(
            (ln.strip() for ln in block.splitlines() if ln.strip()), ""
        )
        if first_line:
            return first_line

    return "（未能从报告中提取一句话结论）"


def _upsert_memory_file(
    path: Path,
    block: str,
    session_id: Optional[str] = None,
) -> None:
    """
    写入记忆文件中的 session 块。

    - session_id 为 None：纯追加（向后兼容）。
    - session_id 有值且文件中尚无该块：追加。
    - session_id 有值且已有该块：替换旧块为最新内容。

    多轮追问场景下，同一 session 的长期记忆应覆盖为最新沉淀结果，而不是跳过。
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    normalized_block = block if block.endswith("\n") else f"{block}\n"

    if not session_id:
        separator = "" if not existing or existing.endswith("\n") else "\n"
        path.write_text(f"{existing}{separator}{normalized_block}", encoding="utf-8")
        return

    escaped_id = re.escape(session_id)
    # 从含 (session_id) 的 ## 标题行起，到下一个 ## 标题前或文件结尾
    pattern = re.compile(
        rf"^## .*?\({escaped_id}\).*?(?=\n## |\Z)",
        re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(existing)

    if match:
        updated = existing[: match.start()] + normalized_block + existing[match.end() :]
        path.write_text(updated, encoding="utf-8")
    else:
        separator = "" if not existing or existing.endswith("\n") else "\n"
        path.write_text(f"{existing}{separator}{normalized_block}", encoding="utf-8")


# ---------------------------------------------------------------------------
# 公开接口
# ---------------------------------------------------------------------------

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
## 3. 专家观点摘要
| 专家 | 核心观点 | 主要担忧 | 建议 |
|------|----------|----------|------|

## 4. 共识结论
## 5. 关键分歧
## 6. 被忽略但重要的视角
## 7. 产品机会
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
    在报告生成后，把关键信息追加写入四个记忆文件：
      - memory/insights.md       ：本次讨论的一句话结论（兼容新旧报告格式）
      - memory/decisions.md      ：本次达成的决策
      - memory/todos.md          ：本次待办事项
      - memory/open_questions.md ：本次未决问题

    同一 session_id 再次沉淀时会 upsert 覆盖旧块；不同 session_id 继续追加。
    多轮追问后用户再次点击「沉淀到长期记忆」时，memory 文件会更新为最新结论。

    decisions / todos / open_questions 均从 session 字段读取，
    使用 getattr 防御式写法，兼容旧版 session 对象缺少字段的情况。
    """
    date_str = session.updated_at or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    header = f"## {session.title} ({session.session_id})\n日期：{date_str}\n"
    sid = session.session_id

    # ── insights ──────────────────────────────────────────────────────────
    conclusion = _extract_one_line_conclusion(report)
    insights_block = f"{header}一句话结论：{conclusion}\n---\n"
    _upsert_memory_file(MEMORY_INSIGHTS, insights_block, sid)

    # ── decisions ─────────────────────────────────────────────────────────
    if getattr(session, "decisions", None):
        decisions_body = "\n".join(f"- {item}" for item in session.decisions)
    else:
        decisions_body = "（本次暂无记录决策）"
    decisions_block = f"{header}{decisions_body}\n---\n"
    _upsert_memory_file(MEMORY_DECISIONS, decisions_block, sid)

    # ── todos ─────────────────────────────────────────────────────────────
    if getattr(session, "todos", None):
        todos_body = "\n".join(f"- {item}" for item in session.todos)
    else:
        todos_body = "（本次暂无记录待办）"
    todos_block = f"{header}{todos_body}\n---\n"
    _upsert_memory_file(MEMORY_TODOS, todos_block, sid)

    # ── open questions ────────────────────────────────────────────────────
    if getattr(session, "open_questions", None):
        questions_body = "\n".join(f"- {item}" for item in session.open_questions)
    else:
        questions_body = "（本次暂无未决问题）"
    questions_block = f"{header}{questions_body}\n---\n"
    _upsert_memory_file(MEMORY_OPEN_QUESTIONS, questions_block, sid)