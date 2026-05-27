# Phase 2.3 Demo LLM Handoff

## 1. 当前情况

当前已完成一个可演示版本：

```text
Phase 2.3-Demo-LLM
```

核心能力：

```text
用户设置会议议题
→ 后端调用真实 LLM 或 fallback 脚本生成圆桌会议内容
→ 后端转换为现有 MeetingEvent/SSE 可播放事件
→ 前端通过 SSE 接收
→ 前端缓冲完成后播放圆桌会议
```

当前 commit：

```text
57c75ac feat(demo): add LLM-generated meeting script over SSE
```

当前检查结果：

```text
Backend pytest: 22 passed
Frontend build: passed
Frontend lint: passed
Fallback curl: verified
Commit/push: done
Working tree: clean
```

当前 backend 状态：

```text
http://127.0.0.1:8000/health 正常
scenario=llm 已可用
无 OPENAI_API_KEY 时自动 fallback
```

---

## 2. 我们现在做到哪里了

### 已完成

- 新增 `scenario=llm`
- 支持通过 query/env 注入 topic
- 后端支持 OpenAI-compatible Chat Completions API
- 支持环境变量：
  - `OPENAI_API_KEY`
  - `OPENAI_BASE_URL`
  - `OPENAI_MODEL`
- LLM 成功时生成中文圆桌会议脚本
- LLM 失败、无 key、解析失败时自动 fallback
- fallback 内容围绕 topic，不会让演示中断
- LLM/fallback 结果会转为前端现有可播放事件
- SSE 保持原有播放管道
- 前端新增：
  - `NEXT_PUBLIC_MEETING_TOPIC`
- 默认 mock 模式未破坏
- 测试覆盖 fallback、JSON 解析、事件转换、原 scenario 回归

### 当前不是

当前版本不是完整正式版。

它不是：

- 真正多 Agent 编排
- token-level streaming
- 边生成边播放
- 完整的小马角色 UI
- 完整会议协议最终形态

当前版本采用的是：

```text
先生成完整会议脚本，再通过 SSE 事件流播放。
```

这是为了明天演示稳定。

---

## 3. 当前架构说明

### Demo 流程

```text
Frontend env:
NEXT_PUBLIC_MEETING_SOURCE=sse
NEXT_PUBLIC_MEETING_SCENARIO=llm
NEXT_PUBLIC_MEETING_TOPIC=AI会不会取代产品经理

↓ EventSource

Backend:
GET /api/meetings/mock-stream?scenario=llm&topic=...

↓ generate script

LLM or fallback:
{
  title,
  topic,
  messages,
  summary
}

↓ convert

MeetingEvent / playable SSE events

↓ stream

Frontend buffered playback

↓ render

RoundTableScene
```

### 当前事件适配

后端内部生成的业务含义包括：

- meeting_started
- agent_joined
- topic_introduced
- message
- summary
- meeting_done

但为了复用现有前端播放器，部分事件会映射为当前 UI 可识别的 `speech` 形态。

当前小马角色会映射到前端已有四个槽位：

| LLM 角色 | 前端槽位 |
|---|---|
| Twilight Sparkle | host |
| Rainbow Dash | product |
| Rarity | tech |
| Fluttershy | growth |

这是演示适配，不是最终角色系统。

---

## 4. 怎么演示

### 4.1 推荐演示方式：真实 LLM

打开终端 1，启动后端：

```powershell
cd backend
$env:OPENAI_API_KEY="你的 key"
$env:OPENAI_BASE_URL="https://api.openai.com/v1"
$env:OPENAI_MODEL="gpt-4o-mini"
py -3.12 -m uvicorn app.main:app --reload --port 8000
```

如果使用 OpenAI-compatible 服务，例如 DeepSeek、Moonshot、SiliconFlow，则替换：

```powershell
$env:OPENAI_BASE_URL="你的 OpenAI-compatible base url"
$env:OPENAI_MODEL="你的模型名"
```

打开终端 2，启动前端：

```powershell
cd frontend
$env:NEXT_PUBLIC_MEETING_SOURCE="sse"
$env:NEXT_PUBLIC_MEETING_SCENARIO="llm"
$env:NEXT_PUBLIC_MEETING_TOPIC="AI会不会取代产品经理"
$env:NEXT_PUBLIC_MEETING_PACE="4.0"
npm run dev
```

浏览器打开：

```text
http://localhost:3000
```

预期效果：

- 页面正常加载
- 前端连接 SSE
- 后端生成会议内容
- 前端缓冲完成后播放
- 圆桌内容围绕“AI会不会取代产品经理”
- 最终完成会议播放

---

### 4.2 备用演示方式：fallback

如果现场网络、模型 API、key 出问题，直接用 fallback。

终端 1：

```powershell
cd backend
Remove-Item Env:OPENAI_API_KEY -ErrorAction SilentlyContinue
py -3.12 -m uvicorn app.main:app --reload --port 8000
```

终端 2 不变：

```powershell
cd frontend
$env:NEXT_PUBLIC_MEETING_SOURCE="sse"
$env:NEXT_PUBLIC_MEETING_SCENARIO="llm"
$env:NEXT_PUBLIC_MEETING_TOPIC="AI会不会取代产品经理"
$env:NEXT_PUBLIC_MEETING_PACE="4.0"
npm run dev
```

fallback 也会：

- 生成围绕 topic 的内容
- 发出 SSE
- 触发前端播放
- 正常发出 `meeting_done`

### fallback 演示话术

```text
当前系统内置了演示保底机制。如果现场网络或模型服务不可用，后端会自动切换到本地 fallback 脚本，保证前端会议流程和事件管道仍然完整可演示。
```

---

## 5. 演示前检查

### 5.1 检查 backend

```powershell
curl.exe http://127.0.0.1:8000/health
```

预期：

```text
200 OK
```

### 5.2 检查 SSE

```powershell
curl.exe -N "http://127.0.0.1:8000/api/meetings/mock-stream?scenario=llm&topic=AI%E4%BC%9A%E4%B8%8D%E4%BC%9A%E5%8F%96%E4%BB%A3%E4%BA%A7%E5%93%81%E7%BB%8F%E7%90%86&pace=4.0"
```

预期能看到：

```text
meeting_started
speech
summary
meeting_done
```

### 5.3 检查 frontend

打开：

```text
http://localhost:3000
```

确认：

- 页面不崩
- 圆桌能播放
- 内容包含“AI会不会取代产品经理”

---

## 6. 明天演示话术

### 简短版

```text
这里展示的是一个真实大模型驱动的 AI 圆桌会议原型。用户给出议题后，后端会调用大模型生成多角色圆桌讨论，并转换成标准会议事件，通过 SSE 推送给前端播放。当前演示版为了稳定，采用先生成完整会议脚本，再事件流播放的方式。
```

### 稍完整版本

```text
这个 Demo 验证的是从“议题输入”到“AI 圆桌会议播放”的端到端链路。

前端只负责播放标准会议事件，不关心内容来自 mock、fallback，还是真实大模型。
后端根据 scenario=llm 读取议题，调用 OpenAI-compatible 大模型生成结构化会议脚本。
生成结果会被转换为现有 MeetingEvent/SSE 事件，再由前端缓冲并播放。

为了明天演示稳定，目前不是 token 级实时生成，而是先生成完整会议内容，再按事件节奏播放。
这保证了即使模型服务短暂波动，系统也可以通过 fallback 完成演示。
```

### 如果被问是不是多 Agent

```text
当前演示版还不是完整多 Agent 编排，而是一次 LLM 调用生成多角色会议脚本。它主要验证产品体验、事件协议和前后端链路。后续会把这个生成逻辑拆成真正的多 Agent 流程。
```

### 如果被问为什么不是边生成边播

```text
这是稳定性取舍。为了保证演示不受网络和模型延迟影响，当前先生成完整会议脚本，然后通过 SSE 播放。下一阶段会升级成边生成边播放。
```

---

## 7. 可用演示议题

推荐主议题：

```text
AI会不会取代产品经理
```

备用议题：

```text
创业公司应该先追求增长还是利润
远程办公是否会降低团队创造力
AI 圆桌会议能不能提升团队决策质量
AI 是否会改变软件团队的组织方式
```

修改议题时，需要重启 frontend，因为 `NEXT_PUBLIC_*` 环境变量在 dev server 启动时读取。

---

## 8. 后续可以怎么优化

### Phase 2.4：真实多 Agent 编排

把当前“一次 LLM 生成完整会议脚本”升级为：

```text
Moderator Agent
Strategy Agent
Execution Agent
Experience Agent
Risk Agent
Summary Agent
```

每个 Agent 独立生成观点，并由 Moderator 控制轮次。

可优化点：

- 每个角色独立 prompt
- 支持多轮互相引用
- 支持追问与反驳
- 支持会议状态记忆
- 支持可配置角色列表

---

### Phase 2.5：边生成边播放

把当前：

```text
完整脚本生成完成 → SSE 播放
```

升级为：

```text
LLM 流式生成 → 增量解析 → SSE 实时推送 → 前端边收边播
```

可优化点：

- token streaming
- sentence-level event emission
- 前端实时追加消息
- 播放器不再等待 `meeting_done`
- 支持中途取消会议
- 支持“正在思考中”状态

---

### Phase 2.6：统一事件协议

当前为了演示，部分事件映射为 `speech`。

后续可以统一成正式协议：

```text
meeting_started
agent_joined
topic_introduced
message
reaction
summary
meeting_done
error
```

可优化点：

- 前端直接理解所有事件类型
- 每种事件有明确 schema
- 增加 protocolVersion 校验
- 增加错误事件和降级事件
- 增加 eventId / sequence / timestamp

---

### Phase 2.7：角色系统和 UI 对齐

当前 UI 仍复用四专家槽位。

后续可以：

- 显示 Twilight / Rainbow / Rarity / Fluttershy
- 支持角色头像
- 支持角色个性化语气
- 支持角色入场动画
- 支持说话状态动画
- 支持角色观点颜色标识

---

### Phase 2.8：演示与生产配置分离

当前 Demo 通过 env 控制。

后续可以：

- 增加前端议题输入框
- 增加 scenario 选择器
- 增加模型选择
- 增加“真实 LLM / fallback / mock”标识
- 增加后台日志面板
- 增加演示安全模式

---

### Phase 2.9：可观测性和稳定性

可增加：

- LLM 请求耗时日志
- fallback 触发原因
- SSE 连接状态
- 事件数量统计
- meetingId
- traceId
- API 超时配置
- 重试策略
- 请求取消
- 前端错误提示

---

## 9. 当前风险和注意事项

### API Key

不要把真实 API Key 提交进仓库。

只在本地终端设置：

```powershell
$env:OPENAI_API_KEY="你的 key"
```

### backend 端口

如果出现：

```text
Unknown scenario 'llm'
```

通常说明 8000 端口上跑的是旧 backend。

处理方式：

```powershell
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

然后重新启动 backend。

### frontend env

修改这些变量后要重启前端：

```text
NEXT_PUBLIC_MEETING_SOURCE
NEXT_PUBLIC_MEETING_SCENARIO
NEXT_PUBLIC_MEETING_TOPIC
NEXT_PUBLIC_MEETING_PACE
```

### fallback

无 key 时 fallback 是正常行为，不是错误。

### 当前真实 LLM 未一定实测

当前 fallback 已验证。
真实 LLM 需要明天用实际 key 再测一次。

---

## 10. 提交信息

当前功能提交：

```text
57c75ac feat(demo): add LLM-generated meeting script over SSE
```

建议新增本文档提交：

```text
docs: add Phase 2.3 demo LLM handoff
```

可选 tag：

```powershell
git tag phase-2.3-demo-llm
git push origin phase-2.3-demo-llm
```
