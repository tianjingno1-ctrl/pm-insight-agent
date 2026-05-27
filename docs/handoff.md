# AI 会话交接包

> **用法**：新开 Cursor/Chat 窗口时，将本文全文粘贴为第一条消息。  
> 说「更新交接包」可让 Cursor 按 `.cursorrules` 刷新 `docs/`。

---

## 复制给新 AI 的提示词（从这里开始）

你是 **pm-insight-agent** 项目的续接开发者。请严格基于下列上下文工作，不要臆造未实现功能。

### 项目是什么

面向产品经理的 **AI 专家圆桌**（Streamlit）。用户提问 → 自动选 3–4 名专家 → 主持人开场 → 专家短发言 → 主持人收场 **固定三行小结** → 可追问多轮 → 手动沉淀到 `memory/*.md`。

启动：`streamlit run app.py`（不是 `main.py`，除非做 CLI 报告）。

### 当前 Git 锚点

- 最新 commit：`d9f80aa` — `修复消息重建与小结识别，待修summary正式渲染变量`
- 标签：`phase-1.5-before-summary-render-final`
- 工作区：提交时应为 clean（换会话前先 `git status`）

### 当前进度（一句话）

重复小结已修；summary 识别与 `force_summary_markdown` 在 DEBUG 下已验证；**待确认**正式 `st.markdown(normalized_content)` 与 `st.code` 一致，然后 `DEBUG_SUMMARY=False`。

### 下一步优先任务（P0）

1. 保持 `DEBUG_SUMMARY=True`，跑一轮，确认边框内小结为：
   ```markdown
   ## 本轮小结
   - 当前倾向：...
   - 最大分歧：...
   - 下一步建议：...
   ```
2. 若 `st.code` 对、边框内仍见「当前趋势 / 最大封闭」，查是否 **另一条 expert 消息** 夹带旧格式（非 summary 分支）
3. 通过后改 `DEBUG_SUMMARY=False`，commit

### P1（随后）

- Phase 1.5.4：专家文本强清洗（`polish_discussion_text`、词表）
- 勿在本阶段改：ChromaDB、讨论中自动 memory、大改 discussion 收场逻辑

### 核心文件与函数

| 文件 | 关键符号 |
|------|----------|
| `app.py` | `main`, `run_discussion_streaming`, `_render_message_list`, `_rebuild_messages_from_session`, `_dedupe_summary_messages`, `_turn_to_message`, `_looks_like_summary_message`, `DEBUG_SUMMARY` |
| `roundtable/discussion.py` | `run_expert_round`, `run_moderator_opening`, `run_moderator_closing`, `force_summary_markdown`, `sanitize_discussion_text`, `polish_discussion_text` |
| `roundtable/session.py` | `RoundtableSession`, `add_turn`, `save_session`, `extract_text_from_image_bytes` |
| `roundtable/synthesis.py` | `update_memory_files`, `_upsert_memory_file`, `synthesize_roundtable_report` |
| `roundtable/moderator.py` | `classify_user_interruption`, `generate_round_summary`（非 Streamlit 主路径） |

### summary 渲染正确写法（app.py）

```python
if is_summary:
    normalized_content = force_summary_markdown(msg.get("content") or "")
    if DEBUG_SUMMARY:
        st.caption("调试：摘要已规范化")
        st.code(normalized_content, language="markdown", key=f"rt_summary_code_{i}")
    with st.container(border=True):
        st.markdown(normalized_content, key=f"rt_summary_md_{i}")
    continue
```

**禁止**在 summary 分支正式渲染使用 `msg["content"]` 或未规范化的 `content`。

### 数据流备忘

```
用户输入 → run_discussion_streaming
  → opening → experts → closing(add_turn 主持人（总结）)
  → _rebuild_messages_from_session → rerun
  → _render_message_list(_dedupe_summary_messages(messages))
```

### 详细文档

- 架构：`docs/architecture.md`
- 进度：`docs/progress.md`
- 决策/坑：`docs/decisions.md`

### 对你的要求

1. 先读相关文件再改，最小 diff
2. 用户说「只改 app.py」时遵守
3. 用中文回复用户
4. 改完后如用户要求可更新交接包

---

## 核心函数速查（自动生成）

### app.py（38 个）

`_read_memory_file`, `_default_round_goal`, `_turn_role`, `_turn_content`, `_speaker_key_from_expert`, `_speaker_key_from_role_text`, `_target_speaker_keys`, `_fallback_expert`, `_pick_expert_for_key`, `_prepare_expert_panel`, `_match_expert_for_turn`, `_display_for_speaker_key`, `_message_user`, `_message_moderator`, `_message_summary`, `_message_expert`, `_looks_like_summary_message`, `_is_summary_message`, `_dedupe_summary_messages`, `_rebuild_messages_from_session`, `_turn_to_message`, `_limit_experts`, `_extract_display_messages`, `_append_new_turns_to_messages`, `_build_memory_report`, `_latest_summary_for_memory`, `_persist_to_long_term_memory`, `_render_messages`（遗留）, `run_discussion_streaming`, `_enrich_question`, `render_memory_panel`, `render_sidebar`, `_render_memory_save_controls`, `_render_message_list`, `main`

### roundtable/discussion.py（34 个）

`force_summary_markdown`, `sanitize_discussion_text`, `polish_discussion_text`, `run_expert_round`, `run_moderator_opening`, `run_moderator_closing`, `format_round_summary`, `has_bad_language`, …

### roundtable/session.py

`DiscussionTurn`, `RoundtableSession`, `create_session`, `save_session`, `load_session`, `add_turn`, `update_context`, `format_turns_for_prompt`, `extract_text_from_image_bytes`

### roundtable/synthesis.py

`synthesize_roundtable_report`, `update_memory_files`, `generate_prd_only`, `_upsert_memory_file`

### roundtable/moderator.py

`classify_user_interruption`, `generate_round_summary`

---

## 最近完成（摘要）

- 消息全量重建 + 小结去重
- summary 识别放宽 + `_turn_to_message` 映射 `type=summary`
- `force_summary_markdown` 在 dedupe/render/重建三处统一调用
- summary 渲染改用 `normalized_content` + Streamlit widget key

---

## 已知注意事项

1. `DEBUG_SUMMARY` 当前为 **True**（`app.py` 第 58 行附近）
2. 不要用 `_render_messages` 动态重绘主历史
3. memory 仅按钮写入；session JSON 在 `memory/sessions/`
4. 专家文本质量差 → Phase 1.5.4，不是小结 bug
5. summary 正式渲染必须用 `normalized_content`，不能用 `msg["content"]`（DEBUG 下 `st.code` 已验证正确，但边框内 `st.markdown` 可能仍用旧变量）

---

*交接包版本：2026-05-26 · 与 commit d9f80aa 对齐*
