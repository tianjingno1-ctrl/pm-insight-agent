# 进度追踪

> 最后更新：2026-05-26 · commit `d9f80aa`

## 已完成

### Phase 1.5 — Streamlit 圆桌 MVP

- [x] Streamlit 多轮追问（`chat_input` + `pending_followup` + rerun）
- [x] 首轮侧边栏提交 → `should_run_initial`，本帧不阻塞 UI
- [x] 静态历史区 `_render_message_list` + `status_placeholder`（避免 `empty()` 导致 setIn 错位）
- [x] 专家 panel 按 `speaker_key` 去重（product / tech / growth 默认 3 人，风险/战略关键词最多 4 人）
- [x] 主持人开场代码拼接（`run_moderator_opening`，不调 LLM）
- [x] 主持人收场 JSON → 固定三行小结写入 session
- [x] `force_summary_markdown`：抽取 → 清洗 → 重建（禁止 return 原文）
- [x] 专家短发言 + `polish_discussion_text`（LLM）
- [x] `sanitize_discussion_text` + `BAD_PHRASE_REPLACEMENTS` 错词表
- [x] 从 `session.turns` 全量 `_rebuild_messages_from_session`
- [x] `_dedupe_summary_messages`（连续小结只留最后一条）
- [x] `_looks_like_summary_message` 放宽识别（本轮小结 / 任意 field marker）
- [x] `_turn_to_message` 主持人总结 → `type=summary` + 重建时 force
- [x] 手动「沉淀到长期记忆」按钮（`update_memory_files`，讨论中不自动写）
- [x] memory 文件同 session_id upsert（`synthesis._upsert_memory_file`）
- [x] 图片附件 OCR 并入问题（`_enrich_question`）
- [x] session JSON 存档 `memory/sessions/`
- [x] Python 3.8 兼容 typing（`List` 等）

### 工程

- [x] 本地 Git commit：`修复消息重建与小结识别，待修summary正式渲染变量`
- [x] 标签 `phase-1.5-before-summary-render-final`

## 进行中

- [ ] **小结正式渲染验证**：`DEBUG_SUMMARY=True` 时 `st.code` 已正确，需确认边框内 `st.markdown(normalized_content)` 与 code 一致
- [ ] 验证通过后 `DEBUG_SUMMARY = False`

## 待做（按优先级）

### P0 — 小结与 UI

1. 确认 summary 分支正式渲染无「当前趋势 / 最大封闭」旧格式残留（排除专家气泡夹带旧小结）
2. 关闭 DEBUG 并回归测一轮完整流程

### P1 — 专家文本质量（Phase 1.5.4）

1. 强化 `polish_discussion_text` / 后处理规则（病句、自造词）
2. 扩展 `BAD_PHRASE_REPLACEMENTS` 与 `has_bad_language` 检测

### P2 — 体验

1. 追问轮动态换专家（代码内已有 TODO）
2. 会话列表 UI：加载历史 session
3. 最终报告大重构（与 `synthesize_roundtable_report` 整合进 Streamlit）

### 明确不做（当前阶段）

- ChromaDB / 向量 RAG
- 讨论中自动写入 memory
- 大改 `moderator.py` 主路径（app 已走 `discussion.run_moderator_closing`）

## 验证清单

```bash
streamlit run app.py
```

首轮示例：「我们要做一个面向中小企业老板的 AI 财务助手，2 周内 MVP 应该做什么？」

期望：

- 每轮仅 **1 块** 小结
- 格式：`## 本轮小结` + `- 当前倾向` / `- 最大分歧` / `- 下一步建议`
- 无重复小结气泡
