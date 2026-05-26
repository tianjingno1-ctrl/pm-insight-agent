from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path

SESSIONS_DIR = Path("memory/sessions")


@dataclass
class DiscussionTurn:
    role: str  # 发言角色，例如 "Product Strategist" 或 "主持人"
    content: str  # 发言内容
    created_at: str  # 时间字符串，格式 "%Y-%m-%d %H:%M:%S"


@dataclass
class RoundtableSession:
    session_id: str
    title: str
    original_input: str  # 用户最初粘贴的原始内容
    current_context: str  # 累计上下文（每次用户补充后追加）
    selected_experts: list  # 选中的专家 id 列表
    turns: list = field(default_factory=list)  # DiscussionTurn 列表（存为 dict）
    decisions: list = field(default_factory=list)  # 达成的结论列表（字符串）
    open_questions: list = field(default_factory=list)  # 未决问题列表（字符串）
    todos: list = field(default_factory=list)  # 待办事项列表（字符串）
    created_at: str = ""
    updated_at: str = ""


def _now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _session_id() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def create_session(title: str, original_input: str, selected_experts: list) -> RoundtableSession:
    """创建新 session，自动生成 session_id（用时间戳格式 YYYYmmdd_HHMMSS）和 created_at"""
    now = _now_str()
    return RoundtableSession(
        session_id=_session_id(),
        title=title,
        original_input=original_input,
        current_context=original_input,
        selected_experts=list(selected_experts),
        created_at=now,
        updated_at=now,
    )


def save_session(session: RoundtableSession) -> Path:
    """
    把 session 序列化为 JSON 保存到 memory/sessions/{session_id}.json。
    保存前自动更新 updated_at。
    返回保存的文件路径。
    """
    session.updated_at = _now_str()
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    path = SESSIONS_DIR / f"{session.session_id}.json"
    path.write_text(
        json.dumps(asdict(session), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return path


def load_session(session_id: str) -> RoundtableSession:
    """从 memory/sessions/{session_id}.json 读取并反序列化为 RoundtableSession 对象"""
    path = SESSIONS_DIR / f"{session_id}.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    return RoundtableSession(**data)


def list_sessions() -> list:
    """
    返回所有历史 session 的摘要列表，每项是一个 dict：
    {"session_id": ..., "title": ..., "created_at": ..., "updated_at": ..., "turns_count": ...}
    按 created_at 倒序排列（最新的在前）
    """
    if not SESSIONS_DIR.is_dir():
        return []

    summaries = []
    for path in SESSIONS_DIR.glob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        summaries.append(
            {
                "session_id": data.get("session_id", path.stem),
                "title": data.get("title", ""),
                "created_at": data.get("created_at", ""),
                "updated_at": data.get("updated_at", ""),
                "turns_count": len(data.get("turns", [])),
            }
        )
    summaries.sort(key=lambda item: item.get("created_at", ""), reverse=True)
    return summaries


def add_turn(session: RoundtableSession, role: str, content: str) -> None:
    """向 session.turns 追加一条发言记录"""
    turn = DiscussionTurn(role=role, content=content, created_at=_now_str())
    session.turns.append(asdict(turn))


def update_context(session: RoundtableSession, new_input: str) -> None:
    """
    把 new_input 追加到 session.current_context。
    格式：在原有内容后加一个空行，再加 "[用户补充 时间]" 标记，再加内容。
    """
    marker = f"[用户补充 {_now_str()}]"
    if session.current_context:
        session.current_context = f"{session.current_context}\n\n{marker}\n{new_input}"
    else:
        session.current_context = f"{marker}\n{new_input}"


def format_turns_for_prompt(session: RoundtableSession, max_chars: int = 6000) -> str:
    """
    把 session.turns 格式化为适合放进 LLM prompt 的字符串。
    格式：每条发言用 "## 角色名\n内容\n" 分隔。
    如果总长度超过 max_chars，只保留最近的发言（从后往前截取）。
    """
    if not session.turns:
        return ""

    blocks: list[str] = []
    for turn in session.turns:
        role = turn.get("role", "") if isinstance(turn, dict) else turn.role
        content = turn.get("content", "") if isinstance(turn, dict) else turn.content
        blocks.append(f"## {role}\n{content}\n")

    selected: list[str] = []
    total = 0
    for block in reversed(blocks):
        if selected and total + len(block) > max_chars:
            break
        selected.append(block)
        total += len(block)
        if total >= max_chars:
            break

    if not selected:
        return blocks[-1][:max_chars]

    selected.reverse()
    return "".join(selected)


if __name__ == "__main__":
    session = create_session(
        title="测试圆桌",
        original_input="用户希望做一个会议记录分析工具。",
        selected_experts=["product-manager", "engineering-frontend-developer"],
    )
    add_turn(session, "Product Manager", "建议先明确目标用户和使用场景。")
    add_turn(session, "主持人", "请各位专家从需求优先级角度发表看法。")
    update_context(session, "补充：需要支持导出 PDF 报告。")

    saved_path = save_session(session)
    print(f"已保存: {saved_path}")

    loaded = load_session(session.session_id)
    print(f"session_id: {loaded.session_id}")
    print(f"turns 数量: {len(loaded.turns)}")

    print("\nlist_sessions():")
    for item in list_sessions():
        print(item)
