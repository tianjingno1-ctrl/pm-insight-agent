# 设计决策与已知问题

> 最后更新：2026-05-27 · experiment `0713f93` · main `5d2bb24`（tag `phase-1.5-summary-done`）

## 关键设计决策

### 1. 消息渲染：静态列表，不用动态 empty 重绘

**决策**：讨论进行中只更新 `status_placeholder.info`；完整历史在 `rerun` 后由 `_render_message_list` 一次性渲染。

**原因**：Streamlit 对 `container.empty()` + 反复 `chat_message` 易出现 DOM/setIn 错位。

**遗留**：`_render_messages(container, ...)` 仍保留，标注勿在主流程调用。

---

### 2. 小结数据源：以 `session.turns` 为准，结束时全量重建

**决策**：每轮结束 `st.session_state.messages = _rebuild_messages_from_session(session, experts)`，不再仅靠增量 append。

**原因**：增量 append 易产生重复小结、type 不一致。

---

### 3. 小结格式：展示层与存储层都 force

**决策**：`run_moderator_closing` 写入时已 `_build_summary_three_lines`；UI 层再次 `force_summary_markdown`（dedupe、render、`_message_summary`）。

**原因**：兼容旧 session 脏数据、LLM 乱造字段名（当前趋势 / 最大封闭）。

**原则**：`force_summary_markdown` 内禁止「看起来已格式化就 return 原文」。

---

### 4. 小结识别：宁可宽松，靠 dedupe 收口

**决策**：`_looks_like_summary_message` 见「本轮小结」或任意 1 个 field marker 即 True；`role` 含「总结/小结」即 summary。

**原因**：`hits >= 2` 曾漏判；专家句偶发「下一步建议」误判成本低于漏渲染 force。

---

### 5. 长期记忆：仅用户按钮写入

**决策**：`update_memory_files` 只在点击「沉淀本次决策到长期记忆」时调用。

**原因**：避免讨论中间状态污染 memory；多轮后 upsert 同 session_id。

---

### 6. 主持人开场不调 LLM

**决策**：`run_moderator_opening` 用 `_build_moderator_opening_text` 代码拼接。

**原因**：减少幻觉、专家介绍乱编、延迟。

---

### 7. 专家发言：短 + polish

**决策**：`_enforce_short_speech`（约 120 字 / 3 句）+ `polish_discussion_text`。

**原因**：圆桌可读性；病句仍待 Phase 2.3.1 加强。

---

### 8. moderator.py 与 discussion.py 双轨

**决策**：Streamlit 主路径用 `discussion.run_moderator_opening/closing`；`moderator.generate_round_summary` 为 CLI/遗留。

**注意**：`add_turn(..., "主持人小结")` 与 `主持人（总结）` 两种 role，`_turn_to_message` 均已映射到 summary。

---

### 9. MeetingEvent control events are non-visual by default

**决策**：`meeting_started` / `meeting_done` **默认不**作为角色气泡展示。

**原因**：

- 通常无 `speakerId`，若按 `speech` 处理会出现空气泡或时间轴空转。
- 更适合顶部状态条、会场初始化/结束态（见 `docs/meeting-event-spec.md`）。

**约定**：默认 `duration_ms = 0`；hook 必须能跳过或快速消费此类事件。

---

### 10. Phase 2.1 split into 2.1a and 2.1b

| 子阶段 | 范围 |
|--------|------|
| **2.1a** | 契约文档（Batch A）→ `frontend/lib/types.ts` + `MeetingPlayer` interface → `useMeetingPlayer`：`switch(type)` 骨架、**pause / resume / replay** 语义修复 |
| **2.1b** | UI polish：emotion 视觉化、action 标签、targetId 高亮、SummaryCard 文案、replay 按钮、移动端、多 mock 场景 |

**原则**：2.1b 不改 `app.py` / `roundtable/`；不创建 `backend/`（至 Phase 2.2）。

---

### 11. Streamlit freeze / downline split

| 模式 | 含义 |
|------|------|
| **freeze** | `main` 上 **停止功能开发**，仅 bugfix / 必要 debug；`DEBUG_SUMMARY=False` 已封版 |
| **downline** | 当 **Next.js + SSE + memory 闭环** 可替代核心路径后，再移除 Streamlit 或迁入 `legacy/` |

**当前**：Streamlit 仍在 `main` 维护；新产品体验在 `experiment/pony-roundtable-ui` 的 `frontend/`。

---

## 已知问题与解决方案

| 问题 | 状态 | 处理 |
|------|------|------|
| 重复小结两块 | ✅ 已修 | `_dedupe_summary_messages` + rebuild |
| summary 未识别 | ✅ 已修 | 放宽 `_looks_like_summary_message` |
| Streamlit 小结正式渲染 | ✅ 已封版 | main `5d2bb24`，`DEBUG_SUMMARY=False` |
| 专家病句/自造词 | ❌ 待做 | Phase 2.3.1 |
| LLM 小结 JSON 字段损坏 | ⚠️ 可恢复 | `force_summary_markdown` |
| Pony：`reaction` 有协议无 UI | ⏳ 已知 | Phase 2.1 标 reserved；2.1b 可选 |
| Pony：pause 后「继续」调用 `start()` 重头 | ❌ 待修 | Phase 2.1a hook |
| Pony：用户 `question` 不驱动 mock | ⏳ 已知 | mock 阶段仅作启动入口；2.3 接 API |
| `requirements.txt` 体积 | ⚠️ 注意 | 完整 `pip install -r requirements.txt` |
| Python 3.8 全局旧 Streamlit | ⚠️ 注意 | 用 venv / `python -m streamlit --version` |

## 修改边界（换会话时勿破）

**Streamlit 线**（仅 bugfix）：`app.py` 小结渲染优先查 `_render_message_list`、`_turn_to_message`、`_dedupe_summary_messages`。

**Pony 线**（experiment 分支）：主改 `frontend/`、`docs/`；**不重构** `roundtable/`；**不创建** `backend/` 直至 Phase 2.2。

用户常要求 **只改 `app.py`** 时，不要动 `discussion.py` 收场、`synthesis.py` upsert、ChromaDB/OCR 核心。

## 常量开关

```python
# app.py（main 已封版）
DEBUG_SUMMARY = False
```
