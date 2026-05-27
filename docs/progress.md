# 进度追踪

> 最后更新：2026-05-27 · 分支 `experiment/pony-roundtable-ui` @ **`741c181`** · tag **`phase-2.2-mock-sse-backend`** · Phase 2.1 功能 **`3360287`**（`phase-2.1-pony-ui-accepted`）· main **`5d2bb24`**

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

### Phase 2.2 — FastAPI mock SSE backend

| Batch | Commit / Tag | 内容 |
|-------|----------------|------|
| A | `bf66604` | 架构决策文档（`backend/`、SSE 契约、批次计划） |
| B | `855efd9` | FastAPI 骨架、`GET /health`、CORS、`backend/README` |
| C | `741c181` | `GET /api/meetings/mock-stream`、scenarios、pytest |
| C 验收 tag | **`phase-2.2-mock-sse-backend`** → `741c181` | Mock SSE 后端验收锚点 |
| D | （本批，仅 docs） | 联调文档、双端口验收、protocolVersion 说明 |

**Batch C 验收记录**

- Endpoint：`GET /api/meetings/mock-stream?scenario=&pace=`
- Scenarios：`default` / `concise` / `verbose` / `weak`
- Tests：`py -3.12 -m pytest` → **15 passed**
- curl：health `sse: "mock_stream"`；mock-stream 含 `meeting_started` / `speech` / `summary` / `meeting_done`
- Errors：`scenario=unknown` → 400；`pace=0.1` / `pace=5` → 422
- Wire：无自定义 SSE `event:`；无顶层 `timestamp` / `metadata`
- `protocolVersion`：**`"1.0"`**（MeetingEvent 契约版本，非项目 Phase 编号）

## 进行中

- [ ] **Phase 2.2 Batch D** — 联调文档锚点（本批）
- [ ] **Phase 2.2 Batch E** — `useMeetingEventStream`（buffer 模式）
- [ ] **Phase 2.2 Batch F1** — `NEXT_PUBLIC_MEETING_SOURCE` + 端到端

## 已知 gap

| 项 | 状态 |
|----|------|
| 前端 SSE hook | Batch E 未开始 |
| `reaction` mock/UI | 协议有；主 mock 无 |
| `mockScenarios` UI 切换 | Phase 2.2.1 / F2 |
| TS/Python mock 文案 | 手工对齐；漂移风险 |
| 用户 `question` 不驱动剧本 | 至 Phase 2.3 |

## Phase 2 Roadmap

- [x] **Phase 2.1** — Frontend mock + contract + acceptance
- [ ] **Phase 2.2** — Mock SSE backend ✅（后端） + frontend stream hook（待 E）
- [ ] **Phase 2.3** — `roundtable/` → `MeetingEvent` 适配器
- [ ] **Phase 2.3.1** — Expert text polish
- [ ] **Phase 2.4** — Streamlit downline decision

### Phase 2.2 批次计划

| Batch | 状态 | 交付 |
|-------|------|------|
| A | ✅ | 架构决策文档 |
| B | ✅ | `backend/` 骨架、`/health` |
| C | ✅ | mock-stream、scenarios、tests、tag |
| D | 🔄 | 联调文档（`docs/` + `backend/README.md`） |
| E | ⏳ | `useMeetingEventStream` |
| F1 | ⏳ | env 数据源切换 + E2E |
| 2.2.1 / F2 | ⏳ | dev-only UI 切换 |

## 验证清单

```powershell
# Streamlit（main）
streamlit run app.py

# Pony UI（默认 mock，端口 3000）
cd frontend
npm run dev

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
git checkout phase-2.2-mock-sse-backend      # 后端 mock SSE
```
