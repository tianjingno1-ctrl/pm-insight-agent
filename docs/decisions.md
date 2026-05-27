# 设计决策与已知问题

> 最后更新：2026-05-26 · commit `d9f80aa`

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

**原因**：圆桌可读性；病句仍待 Phase 1.5.4 加强。

---

### 8. moderator.py 与 discussion.py 双轨

**决策**：Streamlit 主路径用 `discussion.run_moderator_opening/closing`；`moderator.generate_round_summary` 为 CLI/遗留。

**注意**：`add_turn(..., "主持人小结")` 与 `主持人（总结）` 两种 role，`_turn_to_message` 均已映射到 summary。

---

## 已知问题与解决方案

| 问题 | 状态 | 处理 |
|------|------|------|
| 重复小结两块 | ✅ 已修 | `_dedupe_summary_messages` + rebuild |
| summary 未识别 | ✅ 已修 | 放宽 `_looks_like_summary_message` |
| `st.code` 对、`st.markdown` 仍旧格式 | 🔄 验证中 | summary 分支改用 `normalized_content` + widget `key`；排查是否专家气泡夹带旧小结 |
| 专家病句/自造词 | ❌ 待做 | Phase 1.5.4 polish + 词表 |
| LLM 小结 JSON 字段损坏（`##本轮小`） | ⚠️ 可恢复 | `force_summary_markdown` 抽取重建 |
| `requirements.txt` 曾被误提交为大文件 | ⚠️ 注意 | commit 中已含完整依赖列表，换环境用 `pip install -r requirements.txt` |
| Windows 控制台编码 | ✅ | `app.py` 顶部 utf-8 reconfigure |
| Python 3.8 | ⚠️ 仅部分兼容 | 推荐 3.10+；typing 已改 `List` |

## 修改边界（换会话时勿破）

用户常要求 **只改 `app.py`** 时，不要动：

- `roundtable/discussion.py` 小结生成逻辑
- `synthesis.py` memory upsert
- ChromaDB / OCR 底层 / 专家选择核心

小结问题优先查：`app.py` 的 `_render_message_list`、`_turn_to_message`、`_dedupe_summary_messages`。

## 常量开关

```python
# app.py
DEBUG_SUMMARY = True   # 验证小结渲染；通过后改 False
```
