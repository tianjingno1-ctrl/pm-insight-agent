# AI 会话交接包

> **用途**：粘贴给新 AI / 外部评估者，用于**续接开发**或**方案评审**。  
> 维护方式：对 Cursor 说「更新交接包」→ 按 `.cursorrules` 刷新 `docs/`。

---

## 复制给新 AI 的提示词（从这里开始）

你是 **pm-insight-agent** 项目的续接开发者或方案评审 AI。请严格基于下列上下文工作，不要臆造未实现功能。

### 项目是什么（一句话）

**面向产品经理的 AI 专家圆桌**：用户提需求 → 多专家短发言 → 主持人固定三行小结 → 可追问 → 可沉淀长期记忆；正在从 **Streamlit 原型** 演进为 **小马 AI 风格 Next.js 前端 + 未来 FastAPI/SSE 后端** 的 monorepo。

### 当前 Git 锚点

| 分支 | 说明 | 锚点 |
|------|------|------|
| `main` | Streamlit Phase 1.5 **已封版** | `5d2bb24`，tag `phase-1.5-summary-done`，`DEBUG_SUMMARY=False` |
| `experiment/pony-roundtable-ui` | 小马圆桌（**当前主开发线**） | **HEAD `741c181`**（Batch C mock SSE） |

**Phase 2.1 tags（勿移动）**

| Tag | Commit | 含义 |
|-----|--------|------|
| `phase-2.1-pony-ui-polish` | `95fa3d6` | UI polish 完成点 |
| `phase-2.1-pony-ui-accepted` | `3360287` | **前端功能验收**；Pony UI 回滚锚点 |

**Phase 2.2 backend SSE tag（勿移动）**

| Tag | Commit | 含义 |
|-----|--------|------|
| `phase-2.2-mock-sse-backend` | `741c181` | **Mock SSE 后端验收**；`/health` + `/api/meetings/mock-stream` |

> `525cc93` = Phase 2.1 文档交接 · `bf66604` = 2.2 架构文档 · `855efd9` = 2.2 骨架 · `741c181` = 2.2 mock SSE 代码 + 验收 tag。

### 当前阶段（2026-05-27）

```text
✅ Streamlit 圆桌 MVP 已封版（main，DEBUG 关）
✅ Phase 2.1 Pony 前端（tag phase-2.1-pony-ui-accepted @ 3360287）
✅ Phase 2.2 mock SSE backend（tag phase-2.2-mock-sse-backend @ 741c181）
⏳ Phase 2.2 Batch E — 前端 useMeetingEventStream（未开始）
⏳ reaction 有协议、无 UI；主 mock 无 reaction 事件
❌ ChromaDB / 向量 RAG 未接入
```

### 启动命令

| 目标 | 命令 | 端口 |
|------|------|------|
| 旧 Streamlit UI | `streamlit run app.py` | 8501 |
| Pony UI | `cd frontend && npm run dev` | 3000 |
| Mock SSE API | 见下方「Backend 启动」 | **8000** |
| CLI 报告/PRD | `python main.py` | — |

#### Backend 启动（Windows，Python 3.11+）

默认 `python` 若为 3.8，请用 **`py -3.12`**（与 `backend/README.md` 一致）：

```powershell
cd backend
py -3.12 -m pip install -e ".[dev]"
py -3.12 -m uvicorn app.main:app --reload --port 8000
```

健康检查（新进程应返回 `"sse":"mock_stream"`）：

```powershell
curl.exe http://127.0.0.1:8000/health
```

Mock SSE 流：

```powershell
curl.exe -N "http://127.0.0.1:8000/api/meetings/mock-stream?scenario=default&pace=1.0"
```

#### 双端口本地联调（Batch D）

| 终端 | 命令 | 验证 |
|------|------|------|
| 1 | `cd backend` → `py -3.12 -m uvicorn app.main:app --reload --port 8000` | `curl.exe http://127.0.0.1:8000/health` |
| 2 | `cd frontend` → `npm run dev` | 浏览器 `http://localhost:3000`（仍为 mockEvents，至 Batch E） |

**端口冲突**：若 8000 已被旧 uvicorn 占用（`[Errno 10048]`），先结束旧进程再启动，否则 `/health` 可能仍显示 `"sse":"not_implemented"` 且 mock-stream 404。

```powershell
# 查看占用（可选）
Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | Select-Object OwningProcess
```

#### Mock SSE curl 验收清单（已通过 @ `741c181`）

| 检查 | 命令 / 预期 |
|------|-------------|
| 流内容 | `curl.exe -N ".../mock-stream?scenario=default&pace=1.0"` 含 `"type":"meeting_started"`、`speech`、`summary`、`meeting_done` |
| 禁止项 | 输出中无 `event: speech`、无顶层 `"timestamp"` / `"metadata"` |
| `protocolVersion` | 仅 `meeting_started` 上出现 **`"1.0"`**（MeetingEvent 契约版本，≠ 项目 Phase 2.1） |
| 400 | `curl.exe -i "...?scenario=unknown"` |
| 422 | `curl.exe -i "...?pace=0.1"` 或 `pace=5` |
| pytest | `cd backend` → `py -3.12 -m pytest` → 15 passed |

### 修改边界（评审/开发必守）

1. **`experiment/pony-roundtable-ui` 分支**：主改 `frontend/`、`docs/`；**不重构** `app.py`、`roundtable/`
2. **`main` 分支 Streamlit**：仅 bugfix，不大改 discussion 收场逻辑
3. 长期记忆：**仅按钮写入** `memory/*.md`，讨论中不自动写
4. 未来后端 SSE 必须兼容 `docs/meeting-event-spec.md` 的 `MeetingEvent`

### 下一步 P0（Phase 2.2 — 架构已决，见 `docs/architecture.md`）

| 项 | 决策 |
|----|------|
| 目录 | **`backend/`** FastAPI；不用顶层 `api/`；不改 `app.py` / `roundtable/` |
| Endpoint | `GET /api/meetings/mock-stream?scenario=&pace=` |
| SSE | `data:` = MeetingEvent JSON；无自定义 SSE `event:` 类型 |
| 前端拉流 | **`useMeetingEventStream`** + 保留 **`useMeetingPlayer`** |
| 播放 MVP | 缓冲后播放；`NEXT_PUBLIC_MEETING_SOURCE=mock\|sse`（默认 mock） |

### 下一步 P1（Phase 2.3+）

1. `roundtable/discussion.py` → `MeetingEvent[]` 适配器
2. `force_summary_markdown` → `summary` 事件
3. Phase 2.3.1：专家文本强清洗

### 详细文档

- 架构：`docs/architecture.md`
- 进度：`docs/progress.md`
- 决策/坑：`docs/decisions.md`
- 事件协议：`docs/meeting-event-spec.md`
- Monorepo 规则：`README_STRUCTURE.md`

---

## 项目文件结构树（带模块说明）

> 树中 `[技术]` = 主要技术栈，`[关联]` = 主要依赖/数据流向。  
> `agents_library/` 仅列顶层（内含大量第三方 agent markdown，非自研核心）。

```text
pm-insight-agent/                          # monorepo 根
│
├── app.py                                   # [Streamlit] 旧版 Web UI 主入口
│   │                                        # 职责：多轮追问、消息列表渲染、memory 按钮、OCR 附件
│   │                                        # [关联] → roundtable/*, core/llm, memory/
│   │                                        # 状态：legacy，仅 bugfix
│   │
├── main.py                                  # [Python CLI] 命令行圆桌 + 报告/PRD
│   │                                        # 职责：交互式讨论、SUMMARY/PRD/END 命令
│   │                                        # [关联] → roundtable/*, synthesis, moderator（CLI 路径）
│   │                                        # 状态：并行存在，非 Streamlit 主路径
│   │
├── project_context.md                       # [Markdown] 项目背景，注入专家 prompt
├── requirements.txt                         # [pip] Python 依赖（Streamlit, LangChain, pytesseract…）
├── README.md                                # 用户安装/运行说明
├── README_STRUCTURE.md                      # [文档] monorepo 目录归属与改动的硬性规则
├── .cursorrules                             # Cursor：「更新交接包」等自动化规则
├── .env / .env.example                      # LLM API Key、LLM_PROVIDER
│
├── core/                                    # Python 基础设施层
│   ├── llm.py                               # [LangChain/OpenAI 兼容] get_llm, check_api_key
│   │                                        # [关联] ← app.py, main.py, roundtable/*
│   ├── utils.py                             # read_project_context, 敏感词检查等
│   └── report.py                            # 报告文件读写（CLI output）
│
├── roundtable/                              # ★ 圆桌核心业务逻辑（Python，未来 backend 复用）
│   ├── discussion.py                        # 专家发言、主持人开/收场、文本清洗、force_summary_markdown
│   │                                        # [关联] ← app.run_discussion_streaming, main.py
│   │                                        # [技术] LLM prompt + JSON 收场 + 错词表
│   ├── session.py                           # RoundtableSession, turns, save/load JSON, OCR
│   │                                        # [关联] ← discussion, app, synthesis；→ memory/sessions/*.json
│   ├── synthesis.py                         # 长报告、PRD、update_memory_files（md upsert）
│   │                                        # [关联] ← app 沉淀按钮, main.py PRD
│   ├── expert_selector.py                   # auto_select_experts（LLM 选题 + discussion_plan）
│   │                                        # [关联] ← app.run_discussion_streaming
│   ├── agent_loader.py                      # 从 agents_library 加载 ExpertAgent
│   ├── agent_registry.py                    # AgentRegistry 分类检索
│   └── moderator.py                         # 打断分类、旧版阶段性小结（CLI 遗留，非 app 主路径）
│
├── memory/                                  # 持久化数据（非向量库）
│   ├── insights.md                          # 长期：一句话结论
│   ├── decisions.md                         # 长期：决策
│   ├── todos.md                             # 长期：待办
│   ├── open_questions.md                    # 长期：未决问题
│   ├── memory_loader.py                     # 加载 memory 注入 prompt
│   └── sessions/                            # 每轮讨论 JSON 存档（RoundtableSession 序列化）
│       └── YYYYmmdd_HHMMSS.json
│
├── docs/                                    # 产品与协议文档（可自由更新）
│   ├── handoff.md                           # ★ 本文件：AI 会话交接
│   ├── architecture.md                      # 架构说明
│   ├── progress.md                          # 进度追踪
│   ├── decisions.md                         # 设计决策与已知坑
│   └── meeting-event-spec.md                # MeetingEvent 协议（前端 mock ↔ 未来 SSE 共用）
│
├── frontend/                                # ★ 新 UI（Next.js，experiment 分支主开发区）
│   ├── app/
│   │   ├── page.tsx                         # 入口 → RoundTableScene
│   │   ├── layout.tsx                       # 根布局、metadata
│   │   └── globals.css                      # 浅色渐变背景
│   ├── components/
│   │   ├── RoundTableScene.tsx              # 主场景：圆桌布局 + 输入 + 播放控制
│   │   ├── PonyAgent.tsx                    # 单角色头像、情绪环、speaking 动画
│   │   ├── SpeechBubble.tsx                 # 气泡：emotion/action/target；top/bottom placement；多 keyframe 用 tween
│   │   ├── MeetingInput.tsx                 # 用户问题输入
│   │   └── SummaryCard.tsx                  # 「🎯 本轮决策」三行小结
│   ├── hooks/
│   │   └── useMeetingPlayer.ts              # ★ 事件播放状态机（mock；Phase 2.2 旁路 SSE hook）
│   ├── lib/
│   │   ├── types.ts                         # MeetingEvent / AgentId 类型
│   │   ├── meeting-player.ts                # MeetingPlayer 接口与实现
│   │   ├── meetingUi.ts                     # emotion 样式、action 标签、target 关系文案
│   │   ├── mockEvents.ts                    # 默认 mock 一场圆桌（demo 主路径）
│   │   └── mockScenarios.ts                 # concise / verbose / weak 压力测试场景（未接 UI 切换）
│   ├── package.json                         # [Next 16, React, Tailwind, framer-motion]
│   └── (node_modules/, .next/ 不提交 git)
│
├── agents_library/                          # 外部 agent 定义库（markdown persona）
│   └── agency-agents/                       # 按 design/engineering/marketing… 分类
│       └── …                                # [关联] → agent_loader.py 读取
│
├── output/                                  # CLI 生成的报告输出目录
│
└── backend/                                 # Phase 2.2 Batch B+ 创建；mock SSE only
                                             # Phase 2.2 不 import roundtable/
```

---

## 模块关系图（评估用）

```mermaid
flowchart TB
    subgraph UI["表现层"]
        ST[app.py Streamlit]
        FE[frontend/ Next.js Mock]
        CLI[main.py CLI]
    end

    subgraph RT["roundtable/ 业务层"]
        DIS[discussion.py]
        SES[session.py]
        SYN[synthesis.py]
        EXP[expert_selector.py]
        AG[agent_loader + registry]
    end

    subgraph CORE["core/"]
        LLM[llm.py]
    end

    subgraph DATA["数据层"]
        MEM[memory/*.md]
        JSON[memory/sessions/*.json]
    end

    subgraph PROTO["协议层"]
        SPEC[docs/meeting-event-spec.md]
        HOOK[useMeetingPlayer.ts]
    end

    ST --> DIS & EXP & SES & SYN
    CLI --> DIS & SES & SYN
    FE --> HOOK
    HOOK -.->|未来 SSE| SPEC
    DIS & EXP --> LLM
    DIS --> SES
    SES --> JSON
    SYN --> MEM
    ST --> MEM
    AG --> DIS & EXP
    DIS -.->|force_summary → summary event| SPEC
```

---

## 双轨 UI 对照（评审重点）

| 维度 | Streamlit `app.py` | Next.js `frontend/` |
|------|-------------------|---------------------|
| 状态 | main 封版，legacy | experiment 分支，主开发 |
| 事件模型 | Python dict messages | `MeetingEvent` TS 类型 |
| 小结格式 | `force_summary_markdown` → markdown 三行 | `SummaryCard` direction/disagreement/nextStep |
| 播放 | 静态列表一次性渲染 | `useMeetingPlayer` 定时播放 |
| 后端 | 进程内直接调 roundtable | 尚无 backend，纯 mock |
| 迁移策略 | 保留至 backend 就绪 | UI 不动，只换 hook 事件源 |

---

## 核心函数速查

### app.py（Streamlit）

`run_discussion_streaming`, `_render_message_list`, `_rebuild_messages_from_session`, `_dedupe_summary_messages`, `_turn_to_message`, `_looks_like_summary_message`, `DEBUG_SUMMARY=False`

### roundtable/discussion.py

`run_expert_round`, `run_moderator_opening`, `run_moderator_closing`, `force_summary_markdown`, `sanitize_discussion_text`, `polish_discussion_text`

### frontend/hooks/useMeetingPlayer.ts

暴露：`currentEvent`, `summary`, `isPlaying`, `hasStarted`, `isComplete`, `start()`, `pause()`, `resume()`, `replay()`, `reset()`

**播放语义（Phase 2.1 已验收）**

| 方法 | 行为 |
|------|------|
| `start` | 从头开始播放 |
| `pause` | 暂停当前进度 |
| `resume` | 从暂停位置继续（非重头 `start`） |
| `replay` | 会议结束后重新播放，**不**回到输入态 |
| `reset` | 回到输入态，清空进度 |

---

## Phase 2.1 完成记录（Batch A–C + 验收 hotfix）

### 一、完成状态

- [x] Pony roundtable frontend mock
- [x] `MeetingEvent` 契约扩展（Batch A 文档 + Batch B 类型）
- [x] `MeetingPlayer` API 修正（pause / resume / replay / isComplete）
- [x] UI polish（emotion / action / target / SummaryCard / 移动端）
- [x] 本地验收 hotfix（Motion tween + 顶部气泡 placement）

### 二、关键提交

| Commit | 说明 |
|--------|------|
| `100ab73` | `docs: extend MeetingEvent spec and sync Phase 2.1 contract` |
| `9c7f236` | `feat(frontend): align MeetingEvent types and fix MeetingPlayer API` |
| `95fa3d6` | `feat(frontend): polish pony roundtable UI experience` |
| `3360287` | `fix(frontend): keep speech bubbles visible during playback` |

### 三、验收记录

- `npm run build` 通过
- `npm run dev` 本地浏览器验收通过
- 运行时修复：
  - Framer Motion：多 keyframe + spring/inertia 报错 → shake/bounce 改 `tween`
  - 顶部专家 `SpeechBubble` 被视口裁切 → `bubblePlacement="bottom"`（仅 `position: top` 角色）

### 四、当前功能要点

- 默认播放：`mockEvents.ts`（未改默认文案）
- 压力测试数据：`mockScenarios.ts`（`concise` / `verbose` / `weak`），UI 尚未切换入口
- `SpeechBubble`：emotion / action / `targetId` 关系行；顶部角色气泡向下展开
- speaking / targeted 高亮保留（`PonyAgent` ring + 虚线）

### 五、Phase 2.2 架构要点（Batch A 已写入文档）

详见 `docs/architecture.md`、`docs/decisions.md` §12、`docs/meeting-event-spec.md` SSE 节。

- **`backend/`** 独立服务；`backend/pyproject.toml`；不碰根 `requirements.txt`
- Mock 流：`meeting_started` → … → `summary` → `meeting_done` → close
- **`summary` ≠ `meeting_done`**
- 数据：`backend/app/data/scenarios.py` 手工对齐 TS（漂移风险已记录）

### 六、Phase 2.2 实施批次

| Batch | 状态 | 目标 |
|-------|------|------|
| **A** | ✅ `bf66604` | 架构决策文档 |
| **B** | ✅ `855efd9` | FastAPI 骨架 + `/health` |
| **C** | ✅ `741c181` + tag `phase-2.2-mock-sse-backend` | mock-stream + scenarios + tests |
| **D** | 🔄 文档 | 联调 / 验收锚点（本批） |
| **E** | ⏳ | `useMeetingEventStream`（buffer） |
| **F1** | ⏳ | `NEXT_PUBLIC_MEETING_SOURCE` + E2E |
| **2.2.1 / F2** | ⏳ | dev-only source/scenario UI |

---

## 已知注意事项

1. **`DEBUG_SUMMARY=False`**（main 已封版；勿在文档中写 True）
2. **`reaction`**：协议含此 type，**mock/UI 均未实现**（主 mock 无 reaction 事件）
3. **用户输入**：`question` 仅作启动入口，**不驱动** `mockEvents` 内容（固定脚本）
4. **control events**：`meeting_started` / `meeting_done` / `error` 已在 hook 中 `switch(type)` 处理
5. Mock 播放：`useMeetingPlayer.ts`；SSE 拉流：`useMeetingEventStream`（Batch E）
6. **Phase 2.2** 可创建 `backend/`（Batch B+）；**不改** `app.py` / `roundtable/`
7. Streamlit 勿用 `_render_messages` 动态重绘；memory 仅按钮写入
8. **Framer Motion**：多 keyframe 动画必须用 `tween`，勿对 3+ keyframe 使用 spring/inertia

---

## 给方案评审 AI 的评估清单

1. **Monorepo 边界**是否合理？（`README_STRUCTURE.md`）
2. **MeetingEvent 协议**是否足够支撑 SSE 与 mock 对齐？
3. **useMeetingPlayer 隔离**是否利于后端接入而不重写 UI？
4. **roundtable/ 复用**路径是否清晰（discussion → API → SSE → frontend）？
5. **Streamlit 遗留**何时下线？建议：backend + SSE 跑通后再弃
6. **风险点**：专家文本质量、无向量记忆、双 UI 维护成本

---

*交接包版本：2026-05-27 Phase 2.2 · HEAD `741c181` · tag `phase-2.2-mock-sse-backend` · 前端 tag `phase-2.1-pony-ui-accepted` @ `3360287` · main @ `5d2bb24`*
