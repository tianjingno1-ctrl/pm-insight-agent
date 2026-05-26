# -*- coding: utf-8 -*-
from pathlib import Path

MEMORY_DIR = Path("memory")
MAX_SECTION_CHARS = 800


def _read_tail(path: Path, max_chars: int = MAX_SECTION_CHARS) -> str:
    """读取文件末尾最多 max_chars 字符；不存在或为空则返回空字符串。"""
    if not path.is_file():
        return ""
    try:
        content = path.read_text(encoding="utf-8").strip()
    except OSError:
        return ""
    if not content:
        return ""
    if len(content) <= max_chars:
        return content
    return content[-max_chars:]


def load_memory_context() -> str:
    """
    读取 insights.md、decisions.md、todos.md，拼接为历史上下文字符串。
    各文件最多取最后 800 字；文件不存在或为空则跳过。
    若三者皆空，返回 ""。
    """
    sections = []

    insights = _read_tail(MEMORY_DIR / "insights.md")
    if insights:
        sections.append(f"=== 历史洞察 ===\n{insights}")

    decisions = _read_tail(MEMORY_DIR / "decisions.md")
    if decisions:
        sections.append(f"=== 历史决策 ===\n{decisions}")

    todos = _read_tail(MEMORY_DIR / "todos.md")
    if todos:
        sections.append(f"=== 待办事项 ===\n{todos}")

    return "\n\n".join(sections)
