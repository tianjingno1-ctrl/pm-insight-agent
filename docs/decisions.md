# 设计决策与已知问题

> 最后更新：2026-05-27 · experiment HEAD `741c181`（tag `phase-2.2-mock-sse-backend`）· Phase 2.1 前端 `3360287`（tag `phase-2.1-pony-ui-accepted`）· main `5d2bb24`

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

### 12. Phase 2.2 — FastAPI mock SSE backend（Batch A 架构决策）

**目录**：新建 **`backend/`** 独立 FastAPI 服务；**不用** 顶层 `api/`；**不在** `app.py` / `roundtable/` / Next API Route 实现 Phase 2.2 主 SSE。

**依赖**：`backend/pyproject.toml`（fastapi, uvicorn[standard], pydantic v2；dev: pytest, httpx, pytest-asyncio）；**不修改** 根 `requirements.txt`。

**Endpoint**：`GET /api/meetings/mock-stream?scenario=default|concise|verbose|weak&pace=1.0`

- `pace` ∈ [0.25, 4.0]；`effective_delay_ms ≈ delay_before_ms / pace`
- 未知 `scenario` → 400；`pace` 越界 → 422
- SSE：仅默认 message；`data:` = 单行 compact JSON；**禁止** SSE `event:` 与 JSON `type` 双轨

**流顺序（mock）**：`meeting_started`（含唯一 `protocolVersion`）→ `speech`/`reaction`… → `summary` → `meeting_done` → close

**`protocolVersion`**：当前 mock SSE 发送 **`"1.0"`**（见 `docs/meeting-event-spec.md`）。表示 **MeetingEvent 契约版本**，**不是**项目阶段号（Phase 2.1 / 2.2）。勿改为 `"2.1"`，除非 spec 有意升版。

**Batch C 验收**（`741c181`，tag `phase-2.2-mock-sse-backend`）：pytest 15 passed；curl mock-stream；scenarios `default|concise|verbose|weak`；400/422 错误分支；无 SSE `event:` / `timestamp` / `metadata`。

**契约**：`frontend/lib/types.ts` 为代码事实源；`meeting-event-spec.md` 人工同步；backend 局部 Pydantic，`extra='forbid'`；无顶层 `timestamp` / `metadata`；Phase 2.2 不做 codegen。

**Mock 数据**：`backend/app/data/scenarios.py` 手工对齐 TS mock；接受漂移风险。

**前端**：新增 **`useMeetingEventStream`**（拉流 + buffer + status）；**保留** `useMeetingPlayer`；MVP = 缓冲后播放；数据源 `NEXT_PUBLIC_MEETING_SOURCE=mock|sse`（默认 mock）；dev UI 切换 → Phase 2.2.1。

**SSE 场景播放控制**

| 控制 | 语义 |
|------|------|
| `pause` | 仅暂停 player 定时器；SSE 可继续 buffer |
| `resume` | 继续 player |
| `replay` | 重放已 buffer 的 events；不强制重连 SSE |
| `reset` | 关闭 EventSource、清空 buffer、回输入态 |

**CORS**：仅 `localhost:3000` / `127.0.0.1:3000`；端口 backend `8000`、frontend `3000`。

#### Phase 2.2 坚决不做

- 真实 LLM、数据库、多用户/多会议状态、鉴权
- 复杂断线重连、边收边播（→ 2.2.1 / 3）
- OpenAPI/JSON Schema 自动生成 TS/Python
- Phase 2.2 MVP 的 dev UI 数据源/scenario 切换控件
- 修改 `app.py`、`roundtable/`、根 `requirements.txt`
- 新增顶层 `timestamp`、`metadata`
- 移动 `phase-2.1-pony-ui-accepted` / `phase-2.1-pony-ui-polish` 含义

#### Phase 2.2 风险与规避

| 风险 | 规避 |
|------|------|
| CORS | 白名单 origin；或后续 Next rewrite（评审可选） |
| SSE buffering（代理/Nginx） | `X-Accel-Buffering: no`；开发直连 uvicorn |
| StreamingResponse 异常被吞 | 单测 + curl `-N`；日志包装 generator |
| Python 依赖污染 | 独立 `backend/pyproject.toml` |
| PowerShell `curl` 别名 | 文档写 `curl.exe` |
| 双端口忘启 backend | health 预检 + handoff 启动表 |
| EventSource 无自定义 header | 2.2 无鉴权；勿依赖 Authorization header |
| 断线重连 | 明确 deferred；`reset` + 手动重开 |
| player vs stream 语义冲突 | `summary` 结束播放；`meeting_done` 关流；文档区分 |
| TS/Python mock 文案漂移 | review checklist；弱场景边界 case |
| 浏览器同源 SSE 连接数 | 单流 MVP；勿多 Tab 压测 |
| mock 过干净漏测 UI | `weak` scenario 含边界 case |
| mock 被当作真实 orchestration | `mock_stream.py` 顶部 MOCK 警告注释 |

---

## 已知问题与解决方案

| 问题 | 状态 | 处理 |
|------|------|------|
| 重复小结两块 | ✅ 已修 | `_dedupe_summary_messages` + rebuild |
| summary 未识别 | ✅ 已修 | 放宽 `_looks_like_summary_message` |
| Streamlit 小结正式渲染 | ✅ 已封版 | main `5d2bb24`，`DEBUG_SUMMARY=False` |
| 专家病句/自造词 | ❌ 待做 | Phase 2.3.1 |
| LLM 小结 JSON 字段损坏 | ⚠️ 可恢复 | `force_summary_markdown` |
| Pony：`reaction` 有协议无 UI | ⏳ 已知 | 主 mock 无 reaction；Phase 2.2+ 可选 |
| Pony：pause 后「继续」调用 `start()` 重头 | ✅ 已修 | `9c7f236`：`resume()` / `replay()`；`RoundTableScene` 已接线 |
| Pony：Framer Motion 多 keyframe + spring 报错 | ✅ 已修 | `3360287`：shake/bounce 用 `tween` |
| Pony：顶部专家气泡被裁切 | ✅ 已修 | `3360287`：`bubblePlacement=bottom`（仅 top 角色） |
| Pony：用户 `question` 不驱动 mock | ⏳ 已知 | mock 阶段仅作启动入口；2.3 接 API |
| `requirements.txt` 体积 | ⚠️ 注意 | 完整 `pip install -r requirements.txt` |
| Python 3.8 全局旧 Streamlit | ⚠️ 注意 | 用 venv / `python -m streamlit --version` |

## 修改边界（换会话时勿破）

**Streamlit 线**（仅 bugfix）：`app.py` 小结渲染优先查 `_render_message_list`、`_turn_to_message`、`_dedupe_summary_messages`。

**Pony 线**（experiment 分支）：前端验收 tag `phase-2.1-pony-ui-accepted` @ `3360287`；后端 mock SSE tag `phase-2.2-mock-sse-backend` @ `741c181`。下一入口 Batch E：`useMeetingEventStream`。主改 `frontend/`、`docs/`、`backend/`；**不修改** `roundtable/` / `app.py`。SSE 拉流：**`useMeetingEventStream`**；播放：**`useMeetingPlayer`**（不替换）。

用户常要求 **只改 `app.py`** 时，不要动 `discussion.py` 收场、`synthesis.py` upsert、ChromaDB/OCR 核心。

## 常量开关

```python
# app.py（main 已封版）
DEBUG_SUMMARY = False
```
