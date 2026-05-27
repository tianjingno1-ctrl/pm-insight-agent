# 进度追踪

> 最后更新：2026-05-27 · 分支 `experiment/pony-roundtable-ui` · 文档 HEAD **`525cc93`** · 功能验收 **`3360287`**（tag `phase-2.1-pony-ui-accepted`）· main **`5d2bb24`**

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

### Phase 2.2 Batch A — 架构决策文档（**本批，仅 docs**）

- [x] `backend/` 目录策略（独立 FastAPI；非 `api/`、非 Next Route）
- [x] SSE endpoint / `pace` / wire format / 分层模型
- [x] `useMeetingEventStream` + 缓冲后播放 MVP
- [x] Phase 2.2 不做清单与风险表
- [x] 修复 `README_STRUCTURE.md`、`architecture.md` 漂移

## 进行中

- [ ] **Phase 2.2 Batch B** — FastAPI 骨架 + `/health`
- [ ] **Phase 2.2 Batch C** — mock-stream + scenarios + tests
- [ ] **Phase 2.2 Batch D–F1** — 联调文档、SSE hook、env 数据源切换

## 已知 gap

| 项 | 状态 |
|----|------|
| `backend/` 目录 | Batch B 创建 |
| `reaction` mock/UI | 协议有；主 mock 无 |
| `mockScenarios` UI 切换 | Phase 2.2.1 / F2 |
| TS/Python mock 文案 | 手工对齐；漂移风险 |
| 用户 `question` 不驱动剧本 | 至 Phase 2.3 |

## Phase 2 Roadmap

- [x] **Phase 2.1** — Frontend mock + contract + acceptance
- [ ] **Phase 2.2** — FastAPI/SSE mock backend + frontend stream hook
- [ ] **Phase 2.3** — `roundtable/` → `MeetingEvent` 适配器
- [ ] **Phase 2.3.1** — Expert text polish
- [ ] **Phase 2.4** — Streamlit downline decision

### Phase 2.2 批次计划（实施顺序）

| Batch | 交付 |
|-------|------|
| A | 架构决策文档 ✅ |
| B | `backend/` 骨架、`GET /health`、`backend/README` |
| C | `GET /api/meetings/mock-stream`、scenarios、pytest |
| D | curl/双端口/PowerShell 联调文档 |
| E | `useMeetingEventStream`（buffer 至 `meeting_done`） |
| F1 | `NEXT_PUBLIC_MEETING_SOURCE`、E2E 验证 |
| 2.2.1 / F2 | dev-only Mock/SSE + scenario 控件 |

## 验证清单

```bash
# Streamlit（main）
streamlit run app.py

# Pony UI（默认 mock）
cd frontend && npm run dev

# Phase 2.1 功能回滚点
git checkout phase-2.1-pony-ui-accepted

# Phase 2.2 Batch C+ SSE（示例，Batch D 细化）
curl.exe http://127.0.0.1:8000/health
curl.exe -N "http://127.0.0.1:8000/api/meetings/mock-stream?scenario=default&pace=1.0"
```
