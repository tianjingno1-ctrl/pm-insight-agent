# Phase 2.3 Demo LLM Handoff

## 1. 当前情况

**Phase 2.3-Demo-LLM** 已完成并可演示。

| 项 | 值 |
|----|-----|
| 功能 commit | `57c75ac` — `feat(demo): add LLM-generated meeting script over SSE` |
| Backend pytest | 22 passed |
| Frontend build | passed |
| Frontend lint | passed |
| Fallback SSE | 已验证 |
| 工作区 | clean（提交本文档前请再确认） |

核心链路：

```text
用户设置会议议题
→ 后端调用真实 LLM 或 fallback 脚本
→ 转换为现有 MeetingEvent
→ SSE mock-stream
→ 前端缓冲完成后播放
```

---

## 2. 我们做到哪里了

### 已完成

- 新增 `scenario=llm`，支持 query / env 注入 `topic`
- OpenAI-compatible Chat Completions（`OPENAI_API_KEY` / `OPENAI_BASE_URL` / `OPENAI_MODEL`）
- 无 key、请求失败、JSON 解析失败 → **自动 fallback**（仍发出 `meeting_done`）
- 后端生成会议脚本并转为 SSE 可播放事件
- 前端 `NEXT_PUBLIC_MEETING_TOPIC` 注入议题
- 默认 **mock** 模式未破坏（不设 `NEXT_PUBLIC_MEETING_SOURCE` 时无需 backend）

### 当前不是

- 真正多 Agent 编排
- token-level streaming
- 边生成边播放
- 完整小马角色 UI

当前策略：**先生成完整会议脚本，再经 SSE 按节奏播放**（为演示稳定）。

---

## 3. 当前架构

```text
topic
→ backend: resolve_llm_meeting_events()
   ├─ OPENAI_API_KEY 存在 → LLM JSON 脚本
   └─ 否则 / 失败 → fallback_demo_script(topic)
→ script_to_meeting_events()
→ GET /api/meetings/mock-stream?scenario=llm&topic=...&pace=...
→ SSE data: MeetingEvent JSON
→ frontend: useMeetingEventStream (buffer)
→ useMeetingPlayer → RoundTableScene
```

### 事件适配

业务含义含 `meeting_started`、加入圆桌、`topic` 介绍、发言、`summary`、`meeting_done`。为复用 Phase 2.1 播放器，**输出层统一为契约内类型**（加入/议题/发言 → `speech` 等）。

### 角色映射（演示用）

| LLM 角色 | 前端槽位 (AgentId) | UI 显示 |
|----------|---------------------|---------|
| Twilight Sparkle | `host` | 主持人 |
| Rainbow Dash | `growth` | 增长专家 |
| Rarity | `product` | 产品专家 |
| Fluttershy | `tech` | 技术专家 |

非最终角色系统；实现见 `backend/app/services/llm_meeting.py`。

---

## 4. 如何演示

### 4.1 后端 — 真实 LLM

```powershell
cd backend
$env:OPENAI_API_KEY="你的 key"
$env:OPENAI_BASE_URL="https://api.openai.com/v1"
$env:OPENAI_MODEL="gpt-4o-mini"
py -3.12 -m uvicorn app.main:app --reload --port 8000
```

OpenAI-compatible 服务可替换 `OPENAI_BASE_URL` / `OPENAI_MODEL`（DeepSeek、Moonshot、SiliconFlow 等）。

### 4.2 后端 — fallback

```powershell
cd backend
Remove-Item Env:OPENAI_API_KEY -ErrorAction SilentlyContinue
py -3.12 -m uvicorn app.main:app --reload --port 8000
```

### 4.3 前端 SSE + llm

```powershell
cd frontend
$env:NEXT_PUBLIC_MEETING_SOURCE="sse"
$env:NEXT_PUBLIC_MEETING_SCENARIO="llm"
$env:NEXT_PUBLIC_MEETING_TOPIC="AI会不会取代产品经理"
$env:NEXT_PUBLIC_MEETING_PACE="4.0"
npm run dev
```

浏览器：**http://localhost:3000**

### 4.4 演示前检查

健康检查：

```powershell
curl.exe http://127.0.0.1:8000/health
```

SSE（fallback 亦可）：

```powershell
curl.exe -N "http://127.0.0.1:8000/api/meetings/mock-stream?scenario=llm&topic=AI%E4%BC%9A%E4%B8%8D%E4%BC%9A%E5%8F%96%E4%BB%A3%E4%BA%A7%E5%93%81%E7%BB%8F%E7%90%86&pace=4.0"
```

预期包含：`meeting_started`、`speech`、`summary`、`meeting_done`。

### 4.5 前端预期

- 页面不崩溃
- SSE 连接 backend
- 缓冲至 `meeting_done` 后可播放
- 内容围绕议题（如「AI会不会取代产品经理」）

---

## 5. 演示话术

### 简短版

```text
这是真实大模型驱动的 AI 圆桌原型：根据议题生成多角色讨论，转成标准会议事件，经 SSE 给前端播放。为稳定，当前先生成完整脚本再事件流播放。
```

### 稍完整版

```text
本 Demo 验证「议题 → AI 圆桌 → 标准事件 → 播放」全链路。前端只播放 MeetingEvent，不关心内容来自 mock、fallback 还是 LLM。后端 scenario=llm 读取议题，调用 OpenAI-compatible API 生成 JSON 脚本，再转为 SSE 事件；前端缓冲后播放。模型波动时可 fallback，保证演示不中断。
```

### 被问「是不是多 Agent」

```text
当前是一次 LLM 调用生成多角色脚本，不是完整多 Agent 编排；主要验证体验、协议与前后端链路。后续会拆成独立 Agent 与 Moderator 轮次控制。
```

### 被问「为什么不是边生成边播」

```text
稳定性取舍：先完整生成再 SSE 播放，避免现场网络与模型延迟影响演示。下一阶段会做流式生成与边收边播。
```

### 备用议题

- AI 会不会取代产品经理
- 创业公司应该先追求增长还是利润
- 远程办公是否会降低团队创造力
- AI 圆桌会议能不能提升团队决策质量

修改 `NEXT_PUBLIC_*` 后需**重启** `npm run dev`。

---

## 6. 后续优化路线

| 阶段 | 目标 |
|------|------|
| **2.4** | 真实多 Agent 编排（Moderator + 独立角色 prompt、多轮引用） |
| **2.5** | 边生成边播 / token streaming、前端增量播放 |
| **2.6** | 统一事件协议（`agent_joined`、`message` 等前端原生支持） |
| **2.7** | 小马角色与 UI 对齐（头像、入场、语气） |
| **2.8** | 演示与生产配置分离（议题输入、scenario/模型选择） |
| **2.9** | 可观测性（LLM 耗时、fallback 原因、traceId、超时重试） |

---

## 7. 风险和注意事项

- **勿将 API Key 提交进仓库**；仅在本地终端 `$env:OPENAI_API_KEY=...`
- **`Unknown scenario 'llm'`**：8000 上多为旧 backend → `netstat -ano | findstr :8000` → `taskkill /PID <pid> /F` → 重启
- 修改 `NEXT_PUBLIC_MEETING_SOURCE` / `SCENARIO` / `TOPIC` / `PACE` 后需重启 frontend
- **无 key 走 fallback 是正常行为**，不是故障
- **真实 LLM** 建议演示前用实际 key 再测一次（当前以 fallback curl 为主验证）

---

## 8. 提交信息与 tag

| 项 | 值 |
|----|-----|
| 功能 | `57c75ac feat(demo): add LLM-generated meeting script over SSE` |
| 本文档 | `docs: add Phase 2.3 demo LLM handoff` |
| 建议 tag | `phase-2.3-demo-llm` |

回滚演示节点：

```powershell
git checkout phase-2.3-demo-llm
```

**多角色说明（产品 / 测试 / 前后端 / 汇报）**：见 [`phase-2.3-demo-llm-team-brief.md`](./phase-2.3-demo-llm-team-brief.md)。
