# 进度追踪

> 最后更新：2026-05-27 · 分支 `experiment/pony-roundtable-ui` · Phase 2.2 **Accepted** · 功能闭环 **`6cb4ef9`** · 最终 tag **`phase-2.2-sse-mock-integration`** · Phase 2.1 **`3360287`** · main **`5d2bb24`**

## 已完成

### Phase 1.5 — Streamlit 圆桌 MVP（`main` 已封版）

- [x] 多轮追问、静态历史渲染、专家 panel 去重
- [x] 主持人开场代码拼接、收场 JSON → 三行小结
- [x] `force_summary_markdown`、消息重建、小结去重
- [x] 手动 memory 沉淀、session JSON 存档、OCR 附件
- [x] **`DEBUG_SUMMARY=False`**，tag **`phase-1.5-summary-done`**

### Phase 2.0 — Pony 前端 Mock

- [x] `README_STRUCTURE.md` monorepo 边界
- [x] `docs/meeting-event-spec.md` 初版事件协议
- [x] `frontend/` Next.js 16 + TS + Tailwind + Framer Motion
- [x] `useMeetingPlayer` 播放状态机 + `mockEvents` Demo
- [x] RoundTableScene / PonyAgent / SpeechBubble / SummaryCard

### Phase 2.1 — 契约 + 播放器 + UI + 本地验收（**已收口**）

| Batch | Commit | 内容 |
|-------|--------|------|
| A | `100ab73` | 扩展 `meeting-event-spec.md`；同步 docs |
| B | `9c7f236` | `types.ts`、`meeting-player.ts`、`useMeetingPlayer` |
| C | `95fa3d6` | UI polish、`meetingUi.ts`、`mockScenarios.ts` |
| 验收 | `3360287` | Motion tween；顶部气泡 `placement=bottom` |
| D | `525cc93` | Phase 2.1 交接文档锚点 |

**Tags**：`phase-2.1-pony-ui-polish` → `95fa3d6` · `phase-2.1-pony-ui-accepted` → `3360287`

### Phase 2.2 — Mock SSE integration（**已收口**）

| Batch | Commit / Tag | 内容 |
|-------|----------------|------|
| A | `bf66604` | 架构决策文档 |
| B | `855efd9` | FastAPI 骨架、`GET /health`、CORS |
| C | `741c181` | mock-stream、scenarios、pytest |
| C tag | **`phase-2.2-mock-sse-backend`** → `741c181` | 后端 mock SSE 验收 |
| D | `7e5620c` | 联调 / 本地验收文档 |
| E | `fa086f8` | `useMeetingEventStream`（buffer） |
| F1 | `6cb4ef9` | `NEXT_PUBLIC_MEETING_SOURCE=mock\|sse`（默认 mock） |
| F2 / Final | docs + **`phase-2.2-sse-mock-integration`** | 端到端验收归档 |

**Phase 2.2 Final 验收（2026-05-27）**

| 项 | 结果 |
|----|------|
| Backend pytest | **15 passed** |
| Frontend `npm run build` | passed |
| Frontend `npm run lint` | passed |
| Mock 默认模式（无 env） | passed — 原 mock UI，不需 backend，无 EventSource |
| SSE opt-in（`NEXT_PUBLIC_MEETING_SOURCE=sse`） | passed — 缓冲至 `meeting_done` 后播放 |
| 默认数据源 | **mock** |
| 边收边播 | 未实现（刻意） |
| 真实 LLM | 未接入 |
| `protocolVersion` | **`"1.0"`**（MeetingEvent 契约，≠ 项目 Phase 编号） |

## 进行中

- [ ] **Phase 2.3** — `roundtable/` → `MeetingEvent` 适配器 + 真实流式（后续）

## 已知 gap

| 项 | 状态 |
|----|------|
| `reaction` mock/UI | 协议有；主 mock 无 |
| `mockScenarios` / source UI 切换 | Phase 2.2.1+ |
| 边收边播 | Phase 2.3+ |
| TS/Python mock 文案 | 手工对齐；漂移风险 |
| 用户 `question` 不驱动剧本 | 至 Phase 2.3 |

## Phase 2 Roadmap

- [x] **Phase 2.1** — Frontend mock + contract + acceptance
- [x] **Phase 2.2** — Mock SSE integration（tag `phase-2.2-sse-mock-integration`）
- [ ] **Phase 2.3** — `roundtable/` → `MeetingEvent` 适配器
- [ ] **Phase 2.3.1** — Expert text polish
- [ ] **Phase 2.4** — Streamlit downline decision

### Phase 2.2 批次计划（已完成）

| Batch | 状态 | 交付 |
|-------|------|------|
| A–C | ✅ | backend mock SSE + tag `phase-2.2-mock-sse-backend` |
| D | ✅ | 联调文档 |
| E | ✅ | `useMeetingEventStream` |
| F1 | ✅ | env `mock\|sse` 接线 |
| F2 / Final | ✅ | 验收归档 + tag `phase-2.2-sse-mock-integration` |
| 2.2.1+ | ⏳ | dev-only source/scenario UI（后续，非 2.2 范围） |

## 验证清单

```powershell
# Streamlit（main）
streamlit run app.py

# Pony UI（默认 mock，端口 3000）
cd frontend
npm run dev

# Pony UI（SSE opt-in，需 backend :8000）
# $env:NEXT_PUBLIC_MEETING_SOURCE="sse"
# $env:NEXT_PUBLIC_MEETING_SCENARIO="default"
# $env:NEXT_PUBLIC_MEETING_PACE="4.0"
# npm run dev

# Backend mock SSE（端口 8000，需 Python 3.11+）
cd backend
py -3.12 -m pip install -e ".[dev]"
py -3.12 -m uvicorn app.main:app --reload --port 8000

# 健康检查（应 sse: "mock_stream"）
curl.exe http://127.0.0.1:8000/health

# Mock SSE 流
curl.exe -N "http://127.0.0.1:8000/api/meetings/mock-stream?scenario=default&pace=1.0"

# 后端测试
py -3.12 -m pytest

# 回滚锚点
git checkout phase-2.1-pony-ui-accepted      # 前端功能验收
git checkout phase-2.2-mock-sse-backend           # 仅后端 mock SSE
git checkout phase-2.2-sse-mock-integration     # Phase 2.2 全链路验收
```
