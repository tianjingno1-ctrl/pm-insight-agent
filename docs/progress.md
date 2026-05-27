# 进度追踪

> 最后更新：2026-05-27 · 分支 `experiment/pony-roundtable-ui` @ **`3360287`**（tag **`phase-2.1-pony-ui-accepted`**）· main @ **`5d2bb24`**（tag `phase-1.5-summary-done`）

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
- [x] `docs/handoff.md` 结构树与模块说明

### Phase 2.1 — 契约 + 播放器 + UI + 本地验收（**已收口**）

| Batch | Commit | 内容 |
|-------|--------|------|
| A | `100ab73` | 扩展 `meeting-event-spec.md`；同步 `decisions.md` / `progress.md` / `handoff.md` |
| B | `9c7f236` | `types.ts`、`meeting-player.ts`、`useMeetingPlayer`（pause/resume/replay/isComplete） |
| C | `95fa3d6` | UI polish：`meetingUi.ts`、`mockScenarios.ts`、emotion/action/target、SummaryCard |
| 验收 | `3360287` | Motion 多 keyframe → tween；顶部专家气泡 `placement=bottom` |

**Tags**

| Tag | Commit | 说明 |
|-----|--------|------|
| `phase-2.1-pony-ui-polish` | `95fa3d6` | UI polish 完成点（勿移动） |
| `phase-2.1-pony-ui-accepted` | `3360287` | 本地验收通过，**推荐回滚锚点** |

**验收**

- [x] `npm run build` 通过
- [x] `npm run dev` 浏览器验收通过

## 进行中

- [ ] **Phase 2.2** — FastAPI/SSE mock backend（`backend/` 尚未创建）

## 已知 gap（文档已记录）

| 项 | 状态 |
|----|------|
| `reaction` 在协议中，mock/UI 未实现 | 主 mock 无 reaction 事件 |
| `mockScenarios`（concise/verbose/weak） | 数据已有，UI 无切换入口 |
| 用户输入不驱动 `mockEvents` | 仅启动播放固定脚本 |
| `backend/` | **尚未创建**（Phase 2.2 再建） |

## Phase 2 Roadmap

- [x] **Phase 2.1** — Contract + player API + UI polish + 本地验收
- [ ] **Phase 2.2** — FastAPI/SSE mock backend（仍不接真实 roundtable）
- [ ] **Phase 2.3** — Real roundtable events（Python → `MeetingEvent` 适配器）
- [ ] **Phase 2.3.1** — Expert text polish（`polish_discussion_text`、词表）
- [ ] **Phase 2.4** — Streamlit freeze/downline decision（移除或 `legacy/`）

### Phase 2.2 建议入口（来自 Phase 2.1 收口）

1. FastAPI/SSE 按 `meeting-event-spec.md` 推送静态或预录事件流
2. **不动** `app.py`、`roundtable/`
3. 新建 `backend/` 或 `api/` 前先在 `docs/` 确认目录策略
4. 前端新增 `useMeetingPlayerFromSSE`（或类似），与 `useMeetingPlayer` 并存
5. 保留 `mockEvents` 为 fallback / demo

## 验证清单

```bash
# 旧 UI（main）
streamlit run app.py

# 新 UI（experiment 分支，Phase 2.1 验收点）
cd frontend && npm run dev
# 可选：git checkout phase-2.1-pony-ui-accepted
```
