# 进度追踪

> 最后更新：2026-05-27 · experiment 分支 `27bdeff` · main `5d2bb24`

## 已完成

### Phase 1.5 — Streamlit 圆桌 MVP（main 已封版）

- [x] 多轮追问、静态历史渲染、专家 panel 去重
- [x] 主持人开场代码拼接、收场 JSON → 三行小结
- [x] `force_summary_markdown`、消息重建、小结去重
- [x] 手动 memory 沉淀、session JSON 存档、OCR 附件
- [x] `DEBUG_SUMMARY=False`，tag `phase-1.5-summary-done`

### Phase 2.0 — Pony 前端 Mock（experiment/pony-roundtable-ui）

- [x] `README_STRUCTURE.md` monorepo 边界
- [x] `docs/meeting-event-spec.md` 事件协议
- [x] `frontend/` Next.js 16 + TS + Tailwind + Framer Motion
- [x] `useMeetingPlayer` 播放状态机 + mockEvents Demo
- [x] RoundTableScene / PonyAgent / SpeechBubble / SummaryCard

## 进行中

- [ ] Pony UI 视觉与交互打磨
- [ ] 方案评审 / 后端 API 设计

## 待做（按优先级）

### P0 — 前后端桥接

1. 新建 `backend/` FastAPI 骨架
2. SSE 推送 `MeetingEvent`（兼容 `meeting-event-spec.md`）
3. `useMeetingPlayerFromSSE` 替换 mock 源

### P1 — 业务复用

1. 包装 `roundtable/discussion.py` 为 API
2. `force_summary_markdown` → `MeetingEvent.summary`
3. Phase 1.5.4 专家文本强清洗

### P2 — 产品化

1. 会话历史 UI、报告导出进 Next.js
2. 评估是否下线 Streamlit
3. ChromaDB / RAG（明确未启动）

## 验证清单

```bash
# 旧 UI
streamlit run app.py

# 新 UI
cd frontend && npm run dev
```
