# Phase 2.3 Demo LLM — 多角色团队说明

> **读者**：产品经理 · 测试 · 前端 · 后端 · 项目汇报/评审  
> **技术交接（操作向）**：[`handoff-phase-2.3-demo-llm.md`](./handoff-phase-2.3-demo-llm.md)  
> **功能锚点**：`57c75ac` · tag `phase-2.3-demo-llm`  
> **分支**：`experiment/pony-roundtable-ui`

---

## 一句话总结

在已有「小马 AI 圆桌」前端与 SSE 管道上，新增 **按议题生成会议内容** 的演示能力：后端可调用真实大模型（或自动降级为本地脚本），把结果转成标准会议事件推给前端播放；**默认 mock 体验不变**。

---

## 按角色速览

| 角色 | 你最需要知道 |
|------|----------------|
| **产品经理** | 用户给议题 → 多角色中文讨论 → 小结 → 圆桌播放；不是真多 Agent，但是真 LLM 可演示 |
| **测试** | 测 mock 回归、SSE+llm+topic、无 key fallback、curl 与浏览器双路径；不测外网 LLM 自动化 |
| **前端** | 只加 env 与 URL 参数；播放逻辑未改；默认仍本地 mock |
| **后端** | 新 `llm_meeting` 服务 + `scenario=llm`；httpx 调 OpenAI-compatible API |
| **汇报/评审** | 验证了「议题 → 生成 → 事件协议 → SSE → UI」全链路；稳定优先，非最终架构 |

---

## 1. 这个阶段做了什么功能

### 用户可见能力

- 通过环境变量指定**会议议题**（如「AI会不会取代产品经理」）。
- 启动演示模式后，页面展示一场**围绕议题**的圆桌讨论（多段发言 + 三行式小结 + 正常结束）。
- 网络或模型不可用时，**仍能完整播完一场会**（本地 fallback 脚本）。

### 系统能力

| 能力 | 说明 |
|------|------|
| `scenario=llm` | 后端 mock-stream 新增 LLM 演示场景 |
| `topic` 参数 | Query / 前端 env 注入议题 |
| LLM 生成 | 一次调用生成结构化 JSON 脚本（标题、多角色发言、小结） |
| Fallback | 无 API Key 或调用/解析失败 → 本地脚本，内容仍含 topic |
| 事件转换 | 脚本 → 现有 `MeetingEvent` 类型 → SSE |
| 前端播放 | 沿用 Phase 2.2：缓冲至 `meeting_done` 后播放 |
| Mock 保留 | 不设 SSE 相关 env 时，行为与 Phase 2.1 一致 |

### 未做（本阶段明确排除）

- 多 Agent 独立编排与多轮调度  
- Token 级流式输出  
- 边生成边播放  
- 前端议题输入框 / 场景切换 UI  
- 修改 `MeetingEvent` 协议字段  

---

## 2. 为什么这么做

| 决策 | 原因 |
|------|------|
| **先全量生成再播放** | 明天/现场演示要稳：避免模型延迟导致页面空等或半截断流 |
| **复用 SSE + MeetingEvent** | Phase 2.2 已验证管道；前端播放器无需重写 |
| **一次 LLM 调用多角色** | 最快打通「真模型 + 圆桌」；多 Agent 留 Phase 2.4 |
| **Fallback 必做** | Key 缺失、网络、解析失败不能砸演示 |
| **不改默认 mock** | 开发/回归不依赖 backend；降低协作成本 |
| **env 配置议题** | 本批不加 UI，减少前端范围；议题仍可控 |

**产品价值**：证明「PM 提议题 → AI 多视角讨论 → 结构化小结 → 可播放会议」的产品形态可行，且与后续 Streamlit/roundtable 演进路径兼容。

---

## 3. 现在能怎么演示

### 路径 A：真实 LLM（推荐对外演示）

**终端 1 — 后端**

```powershell
cd backend
$env:OPENAI_API_KEY="你的 key"
$env:OPENAI_BASE_URL="https://api.openai.com/v1"
$env:OPENAI_MODEL="gpt-4o-mini"
py -3.12 -m uvicorn app.main:app --reload --port 8000
```

**终端 2 — 前端**

```powershell
cd frontend
$env:NEXT_PUBLIC_MEETING_SOURCE="sse"
$env:NEXT_PUBLIC_MEETING_SCENARIO="llm"
$env:NEXT_PUBLIC_MEETING_TOPIC="AI会不会取代产品经理"
$env:NEXT_PUBLIC_MEETING_PACE="4.0"
npm run dev
```

浏览器打开：**http://localhost:3000** → 等待缓冲完成 → 开始播放。

### 路径 B：Fallback（现场保底）

后端去掉 `OPENAI_API_KEY`，前端 env 与路径 A 相同。内容与议题相关，但文案为预设模板，非模型实时创作。

### 路径 C：默认 Mock（回归）

不设置任何 `NEXT_PUBLIC_*`，仅 `npm run dev`。无需 backend。

### 推荐演示议题

- AI 会不会取代产品经理（主议题）  
- 创业公司应该先追求增长还是利润  
- 远程办公是否会降低团队创造力  
- AI 圆桌会议能不能提升团队决策质量  

### 汇报用一句话

> 用户给出议题后，后端用大模型生成多角色圆桌脚本，转成标准会议事件经 SSE 推送；前端按既有播放器展示。当前为「先成稿、再播放」，以保证演示稳定。

---

## 4. 用到了什么技术

| 层级 | 技术 |
|------|------|
| 前端 | Next.js 16、React、TypeScript、`EventSource`（SSE 客户端）、既有 `useMeetingPlayer` / Framer Motion UI |
| 后端 | FastAPI、Uvicorn、Pydantic v2、**httpx**（异步 HTTP 调 LLM） |
| 协议 | `MeetingEvent` JSON（`meeting_started` / `speech` / `summary` / `meeting_done`），SSE `data:` 行 |
| LLM | OpenAI Chat Completions 兼容 API（`response_format: json_object` 优先，失败则降级请求） |
| 配置 | 后端 env：`OPENAI_*`；前端 build-time env：`NEXT_PUBLIC_MEETING_*` |
| 测试 | pytest（含 asyncio）、ESLint、Next.js build |
| 仓库 | monorepo；本阶段**未改** `app.py`、`roundtable/`、根 `requirements.txt` |

---

## 5. 前端、后端各自改了什么

### 后端（`backend/`）

| 文件 | 变更 |
|------|------|
| **`app/services/llm_meeting.py`**（新） | LLM 调用、JSON 解析、fallback 脚本、`script_to_meeting_events()` |
| `app/config.py` | 读取 `OPENAI_API_KEY` / `BASE_URL` / `MODEL` |
| `app/services/mock_stream.py` | `scenario=llm` 时走 LLM 解析链 |
| `app/routers/meetings.py` | 新增 query 参数 `topic` |
| `app/data/scenarios.py` | `SUPPORTED_SCENARIOS` 增加 `llm`（静态 mock 四场景不变） |
| `pyproject.toml` | 生产依赖增加 `httpx` |
| **`tests/test_llm_meeting.py`**（新） | fallback、解析、事件形状、原 scenario 回归 |

**API 形态（未新增路径，仅扩展参数）**

```http
GET /api/meetings/mock-stream?scenario=llm&topic=<议题>&pace=4.0
```

### 前端（`frontend/`）

| 文件 | 变更 |
|------|------|
| **`lib/meetingSource.ts`** | `getMeetingTopic()`；既有 `getMeetingSource` 等 |
| `hooks/useMeetingEventStream.ts` | URL 组装时可选附加 `topic`（URL encode） |
| `components/RoundTableScene.tsx` | 传入 `topic`；SSE 模式逻辑 Phase 2.2 已有 |
| `README.md` | Demo LLM env 说明 |

**未改**：`MeetingEvent` 类型、`useMeetingPlayer` 播放语义、默认 `mockEvents` 数据源。

---

## 6. 测试应该怎么测

### 自动化（CI / 本地必跑）

```powershell
cd backend
py -3.12 -m pytest          # 预期 22 passed，不调用真实 LLM API

cd ..\frontend
npm run build
npm run lint
```

### 后端接口（测试 / 后端）

| # | 用例 | 步骤 | 预期 |
|---|------|------|------|
| B1 | Health | `curl.exe http://127.0.0.1:8000/health` | 200，`sse: mock_stream` |
| B2 | LLM fallback SSE | 无 `OPENAI_API_KEY`，`scenario=llm&topic=测试议题&pace=4.0` | 含 topic 文案、`meeting_started`、`speech`、`summary`、`meeting_done` |
| B3 | 原 mock 场景 | `scenario=default/concise/verbose/weak` | 与 Phase 2.2 一致 |
| B4 | 非法 scenario | `scenario=unknown` | 400 |
| B5 | 非法 pace | `pace=0.1` 或 `5` | 422 |
| B6 | 真实 LLM | 配置有效 Key 后同 B2 | 内容与议题相关且非固定 fallback 口吻（**手工**） |

### 前端（测试 / 前端）

| # | 用例 | 步骤 | 预期 |
|---|------|------|------|
| F1 | 默认 mock | 无 `NEXT_PUBLIC_*`，`npm run dev` | 原 mock 可播；Network 无 mock-stream |
| F2 | SSE + llm | 按 §3 路径 A/B 启动 | 连接 SSE；缓冲文案；`meeting_done` 后可播 |
| F3 | 议题可见 | F2 + 指定 TOPIC | 发言/议题介绍含该中文议题 |
| F4 | 不崩溃 | 后端未启动时开 SSE | 轻量错误提示，页面不白屏（Phase 2.2 行为） |
| F5 | env 变更 | 改 `NEXT_PUBLIC_MEETING_TOPIC` 不重启 | 应重启 dev 后生效（负向确认） |

### 不建议自动化

- 真实 LLM API 调用（费用、不稳定、无 Key 在 CI）  
- 浏览器 E2E（本阶段未引入 Playwright 等）  

### 缺陷记录建议

记录：是否 fallback、议题、事件条数、是否出现 `Unknown scenario 'llm'`（多为旧 backend 进程）。

---

## 7. 当前边界和限制

| 边界 | 说明 |
|------|------|
| 非多 Agent | 单次 LLM 生成整份脚本，非分角色独立调度 |
| 非流式 | 用户需等待整段生成 + SSE 缓冲后才开始播 |
| 角色 UI | 仍显示 Phase 2.1 四专家；LLM 小马名映射到四槽位 |
| 事件形态 | 加入/议题等在协议层体现为 `speech`，非最终协议 |
| 议题入口 | 仅 env/query，页内输入框未接后端 |
| 安全 | API Key 仅后端 env，不得进仓库或前端 |
| Windows | 后端建议 `py -3.12`（系统默认 Python 可能为 3.8） |
| 端口 | 8000 被旧进程占用会导致 `llm` 不可用 |

---

## 8. 后续可以怎么优化

| 阶段 | 方向 | 主要受益角色 |
|------|------|----------------|
| **2.4** | 真多 Agent（Moderator + 分角色 prompt、多轮） | 产品、后端 |
| **2.5** | Token/SSE 流式、边生成边播 | 产品、前端、后端 |
| **2.6** | 事件协议统一（`message`、`agent_joined` 等） | 全员 |
| **2.7** | 小马角色与 UI 一致 | 产品、前端 |
| **2.8** | 议题输入、scenario/模型选择、演示模式面板 | 产品、测试 |
| **2.9** | 日志、trace、fallback 原因、超时重试 | 测试、后端、运维 |
| **2.3+** | `roundtable/` → MeetingEvent 适配、对接 legacy Streamlit | 后端、产品 |

---

## 9. 本项目 / 本阶段做得好的地方

1. **增量交付**：在 Phase 2.2 SSE 集成之上加能力，未推翻播放器与协议。  
2. **演示韧性**：Fallback 保证「无 Key 也能完整演示」，降低现场风险。  
3. **职责清晰**：后端负责「生成 + 转事件」；前端负责「拉流 + 播放」；契约不变。  
4. **默认 mock 守护**：日常开发不依赖 backend，回归成本低。  
5. **测试可重复**：22 个 pytest 覆盖解析、转换、fallback、原场景，且不打外网。  
6. **文档可复现**：`handoff-phase-2.3-demo-llm.md` + tag `phase-2.3-demo-llm` 固定演示节点。  
7. **兼容开放 API**：`OPENAI_BASE_URL` 可换国内/自建兼容端点，便于试点。  
8. **范围克制**：明确「演示版」边界，避免评审阶段过度承诺多 Agent / 实时流。

---

## 附录：Git 与文档索引

| 资源 | 说明 |
|------|------|
| 功能 commit | `57c75ac` — `feat(demo): add LLM-generated meeting script over SSE` |
| 演示 tag | `phase-2.3-demo-llm` |
| 操作交接 | [`handoff-phase-2.3-demo-llm.md`](./handoff-phase-2.3-demo-llm.md) |
| 事件协议 | [`meeting-event-spec.md`](./meeting-event-spec.md) |
| 总交接 | [`handoff.md`](./handoff.md) |
| 后端 README | [`../backend/README.md`](../backend/README.md) |
| 前端 README | [`../frontend/README.md`](../frontend/README.md) |

---

*文档版本：Phase 2.3-Demo-LLM · 与 `handoff-phase-2.3-demo-llm.md` 对齐*
