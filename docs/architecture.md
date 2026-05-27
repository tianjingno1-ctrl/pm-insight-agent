# 架构说明

> 最后更新：2026-05-27 · main `5d2bb24` · experiment `27bdeff`

## 项目定位（一句话）

**面向产品经理的 AI 专家圆桌**：Streamlit 原型已封版；正在 monorepo 内建设 **Next.js 小马风格 UI Mock**，未来以 **FastAPI/SSE + MeetingEvent 协议** 对接既有 `roundtable/` Python 逻辑。

## 技术栈

| 层级 | 技术 |
|------|------|
| 旧 UI | Streamlit 1.40（`app.py`，legacy bugfix only） |
| 新 UI | Next.js 16 + TypeScript + Tailwind + Framer Motion（`frontend/`） |
| 事件协议 | `MeetingEvent`（`docs/meeting-event-spec.md`） |
| LLM | LangChain + OpenAI 兼容 API（DeepSeek 默认，`core/llm.py`） |
| 业务逻辑 | 自研 `roundtable/`（未来 `backend/` 复用） |
| 会话持久化 | JSON `memory/sessions/` |
| 长期记忆 | Markdown `memory/*.md`（非向量库） |
| CLI | `main.py`（报告/PRD，与 Streamlit 并行） |

**未接入**：ChromaDB、FastAPI backend、SSE 实时流。

## 完整结构树

详见 **`docs/handoff.md`** 中的「项目文件结构树」与「模块关系图」（供 AI 评估用）。

## 目录结构与职责

```
pm-insight-agent/
├── app.py                 # Streamlit 主界面：多轮追问、消息渲染、小结去重、memory 按钮
├── main.py                # CLI：需求分析 + 圆桌报告 + PRD
├── project_context.md     # 项目背景（注入专家 prompt）
├── requirements.txt
├── .env / .env.example    # API Key、LLM_PROVIDER
│
├── core/
│   ├── llm.py             # get_llm、check_api_key
│   ├── utils.py           # read_project_context 等
│   └── report.py          # 报告文件读写
│
├── roundtable/
│   ├── discussion.py      # 专家发言、主持人开/收场、文本清洗、force_summary_markdown
│   ├── session.py         # RoundtableSession、turns、save/load、OCR
│   ├── synthesis.py       # 报告合成、PRD、update_memory_files（upsert）
│   ├── moderator.py       # 打断分类、阶段性小结（CLI 遗留，app 主流程用 discussion）
│   ├── expert_selector.py # auto_select_experts
│   ├── agent_loader.py    # 加载专家 YAML/配置 → ExpertAgent
│   └── agent_registry.py  # AgentRegistry 分类检索
│
├── memory/
│   ├── insights.md / decisions.md / todos.md / open_questions.md
│   ├── sessions/*.json    # 每轮讨论完整存档
│   └── memory_loader.py   # 记忆加载（供 prompt 使用）
│
└── docs/                  # 会话交接文档（本目录）
```

## 核心数据流

```mermaid
flowchart TD
    A[用户侧边栏/追问] --> B[app.main]
    B --> C[run_discussion_streaming]
    C --> D[auto_select_experts]
    C --> E[run_moderator_opening]
    C --> F[run_expert_round x N]
    C --> G[run_moderator_closing]
    G --> H[session.turns + JSON]
    C --> I[_rebuild_messages_from_session]
    I --> J[_render_message_list]
    B --> K[用户点击沉淀 memory]
    K --> L[update_memory_files]
```

## 关键模块 API（精简）

### `app.py`

| 函数 | 职责 |
|------|------|
| `run_discussion_streaming` | 一轮完整讨论；结束时 `messages = _rebuild_messages_from_session` + `rerun` |
| `_render_message_list` | 静态渲染历史；summary 用 `normalized_content = force_summary_markdown(...)` |
| `_rebuild_messages_from_session` | 从 `session.turns` 全量重建，避免重复小结 |
| `_dedupe_summary_messages` | 连续小结只留最后一条并规范化 |
| `_turn_to_message` | turn → UI message dict；主持人总结 → `type=summary` |
| `_prepare_expert_panel` | 按 speaker_key 去重，默认 product+tech+growth，最多 4 人 |
| `_persist_to_long_term_memory` | 按钮触发 `update_memory_files` |

### `roundtable/discussion.py`

| 函数 | 职责 |
|------|------|
| `run_expert_round` | 单专家发言 → `polish_discussion_text` + 短发言限制 |
| `run_moderator_opening` | 代码拼接开场（不调 LLM） |
| `run_moderator_closing` | LLM JSON → `_build_summary_three_lines` → `add_turn(主持人（总结）)` |
| `force_summary_markdown` | 抽取字段 → 强制 `## 本轮小结` + 三行 bullet |
| `sanitize_discussion_text` | 错词替换、去重空行 |

### `roundtable/session.py`

| 类型/函数 | 职责 |
|-----------|------|
| `RoundtableSession` | turns、decisions、todos、open_questions |
| `add_turn` / `save_session` / `load_session` | 持久化 |
| `extract_text_from_image_bytes` | 附件 OCR |

### `roundtable/synthesis.py`

| 函数 | 职责 |
|------|------|
| `synthesize_roundtable_report` | 长报告生成 |
| `update_memory_files` | 按 session_id upsert 四个 md 文件 |
| `generate_prd_only` | PRD 初稿 |

### `roundtable/moderator.py`（次要）

| 函数 | 职责 |
|------|------|
| `classify_user_interruption` | 用户打断类型分类 |
| `generate_round_summary` | 旧版阶段性小结（`主持人小结` role） |

## Streamlit 状态字段

| `st.session_state` 键 | 含义 |
|------------------------|------|
| `messages` | UI 消息列表（dict：type/user/assistant/expert/summary） |
| `rt_session` | 当前 `RoundtableSession` |
| `rt_experts` / `rt_result` | 专家列表与选题结果 |
| `round_index` | 追问轮次 |
| `should_run_initial` / `should_run_followup` | 延迟到 rerun 后跑 LLM |
| `discussion_active` | 是否可追问 |
| `memory_saved` | 是否已沉淀 memory |

## 启动方式

```bash
streamlit run app.py
```

CLI：

```bash
python main.py
```
