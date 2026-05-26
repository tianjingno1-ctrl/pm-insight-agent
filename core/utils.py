import re
from pathlib import Path
from typing import List

DEFAULT_PROJECT_CONTEXT = """# 项目背景

产品名称：（请填写）

目标用户：（请填写）

当前阶段：MVP

核心目标：
- （请填写）
"""


def read_multiline_input(prompt_text: str = "", end_marker: str = "END") -> str:
    """
    读取用户多行输入，直到单独一行等于 end_marker（不区分大小写）为止。
    返回合并后的字符串。如果输入为空则返回空字符串。
    prompt_text 不为空时先打印提示语。
    """
    if prompt_text:
        print(prompt_text)

    lines: List[str] = []
    marker = end_marker.strip().upper()

    while True:
        try:
            line = input()
        except EOFError:
            break
        if line.strip().upper() == marker:
            break
        lines.append(line)

    return "\n".join(lines).strip()


def read_project_context(path: str = "project_context.md") -> str:
    """
    读取 project_context.md 文件内容。
    文件不存在时自动创建默认模板并返回模板内容。
    """
    context_path = Path(path)
    if context_path.is_file():
        return context_path.read_text(encoding="utf-8")

    context_path.write_text(DEFAULT_PROJECT_CONTEXT, encoding="utf-8")
    return DEFAULT_PROJECT_CONTEXT


def print_divider(char: str = "─", width: int = 50) -> None:
    """打印一行分隔线"""
    print(char * width)


def print_header(title: str) -> None:
    """打印带分隔线的标题，例如：
    ──────────────────────────────────────────────────
    PM Insight Roundtable · AI 产品圆桌会议
    ──────────────────────────────────────────────────
    """
    print_divider()
    print(title)
    print_divider()


def check_sensitive_info(text: str) -> list:
    """
    检测文本中是否包含敏感信息。
    检测项：手机号（11位数字）、邮箱、API Key（sk- 开头）、身份证号（18位）。
    返回检测到的敏感信息类型列表，例如 ["手机号", "邮箱"]。
    没有则返回空列表。
    """
    if not text:
        return []

    found: List[str] = []

    if re.search(r"(?<!\d)1\d{10}(?!\d)", text):
        found.append("手机号")

    if re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text):
        found.append("邮箱")

    if re.search(r"sk-[A-Za-z0-9]{8,}", text):
        found.append("API Key")

    if re.search(r"(?<!\d)\d{17}[\dXx](?!\d)", text):
        found.append("身份证号")

    return found
