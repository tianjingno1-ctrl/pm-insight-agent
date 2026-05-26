from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

SKIP_DIRS = frozenset({".github", "examples", "scripts", "integrations"})


@dataclass
class ExpertAgent:
    id: str  # 由文件名生成，例如 product-strategist.md → product-strategist
    name: str  # 优先读取 Markdown 第一个一级标题；没有则由文件名转换
    category: str  # 文件所在的上级文件夹名
    path: str  # 文件完整路径（字符串）
    description: str  # Markdown 前 300 个字符
    prompt: str  # 完整 Markdown 文件内容


def _filename_to_name(stem: str) -> str:
    return stem.replace("-", " ").title()


def _extract_h1(content: str) -> Optional[str]:
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("# ") and not stripped.startswith("##"):
            return stripped[2:].strip()
    return None


def _parse_expert_agent(md_path: Path, base_dir: Path) -> ExpertAgent:
    content = md_path.read_text(encoding="utf-8")
    stem = md_path.stem
    name = _extract_h1(content) or _filename_to_name(stem)
    return ExpertAgent(
        id=stem,
        name=name,
        category=md_path.parent.name,
        path=str(md_path.resolve()),
        description=content[:300],
        prompt=content,
    )


def load_expert_agents(base_dir: str = "agents_library/agency-agents") -> List[ExpertAgent]:
    """
    扫描 base_dir 下所有子目录中的 .md 文件（不包括根目录的 README.md、CONTRIBUTING.md 等）。
    每个 .md 文件转换为一个 ExpertAgent 对象。
    跳过以下目录：.github、examples、scripts、integrations。
    返回所有专家的列表。
    """
    base = Path(base_dir)
    if not base.is_dir():
        return []

    agents: List[ExpertAgent] = []
    for md_path in sorted(base.rglob("*.md")):
        rel = md_path.relative_to(base)
        if len(rel.parts) < 2:
            continue
        if any(part in SKIP_DIRS for part in rel.parts[:-1]):
            continue
        agents.append(_parse_expert_agent(md_path, base))
    return agents
