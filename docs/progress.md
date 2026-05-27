# 进度追踪

> 最后更新：2026-05-27 · 分支 `experiment/pony-roundtable-ui` @ **`0713f93`** · main @ **`5d2bb24`**（tag `phase-1.5-summary-done`）

## 已完成

### Phase 1.5 — Streamlit 圆桌 MVP（`main` 已封版）

- [x] 多轮追问、静态历史渲染、专家 panel 去重
- [x] 主持人开场代码拼接、收场 JSON → 三行小结
- [x] `force_summary_markdown`、消息重建、小结去重
- [x] 手动 memory 沉淀、session JSON 存档、OCR 附件
- [x] **`DEBUG_SUMMARY=False`**，tag **`phase-1.5-summary-done`**

### Phase 2.0 — Pony 前端 Mock（`experiment/pony-roundtable-ui`）

- [x] `README_STRUCTURE.md` monorepo 边界
- [x] `docs/meeting-event-spec.md` 初版事件协议
- [x] `frontend/` Next.js 16 + TS + Tailwind + Framer Motion
- [x] `useMeetingPlayer` 播放状态机 + `mockEvents` Demo
- [x] RoundTableScene / PonyAgent / SpeechBubble / SummaryCard
- [x] `docs/handoff.md` 结构树与模块说明（`0713f93`）

### Phase 2 — 契约文档（Batch A，进行中）

- [x] **Batch A**：扩展 `meeting-event-spec.md`（control events、optional 字段、Phase 2.1 子集）
- [x] 同步 `decisions.md` / `progress.md` / `handoff.md` 漂移修正

## 进行中

- [ ] **Phase 2.1a** — Contract + player API cleanup（代码，未开始）
- [ ] **Phase 2.1b** — Pony UI polish（代码，未开始）

## 已知 gap（文档已记录，代码未改）

| 项 | 状态 |
|----|------|
| `reaction` 在协议中，mock/UI 未实现 | 协议标 **reserved / optional** |
| `meeting_started` / `meeting_done` / `error` | 协议已定义；UI 与 hook 待 2.1a |
| `backend/` | **尚未创建** |
| 用户输入不驱动 `mockEvents` | 仅启动播放固定脚本 |

## Phase 2 Roadmap

- [ ] **Phase 2.1a** — Contract + player API cleanup（types、`MeetingPlayer`、hook `switch(type)`、pause/resume/replay）
- [ ] **Phase 2.1b** — Pony UI polish（emotion / action / target / SummaryCard / 移动端 / 多 mock）
- [ ] **Phase 2.2** — FastAPI/SSE mock backend（仍不接真实 roundtable）
- [ ] **Phase 2.3** — Real roundtable events（Python → `MeetingEvent` 适配器）
- [ ] **Phase 2.3.1** — Expert text polish（`polish_discussion_text`、词表）
- [ ] **Phase 2.4** — Streamlit freeze/downline decision（移除或 `legacy/`）

## 验证清单

```bash
# 旧 UI（main）
streamlit run app.py

# 新 UI（experiment 分支）
cd frontend && npm run dev
```
