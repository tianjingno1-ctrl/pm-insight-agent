# PM Insight Agent：产品经理需求洞察助手

> 面向产品经理的 AI 分析工具。粘贴会议记录、微信聊天、用户反馈或 OCR 文字，自动输出会议纪要、痛点分析、需求洞察、方案建议、PRD 初稿与待办事项。

---

## 你能用它做什么？

| 输入 | 输出 |
|------|------|
| 会议记录 | 会议纪要 |
| 微信聊天记录 | 用户痛点分析 |
| 用户反馈 | 需求洞察 |
| 截图 OCR 文字 | 产品方案建议 |
| 你的产品想法 | PRD 初稿 + 待办事项 |

**第一版 MVP**：在命令行粘贴文字即可（暂不支持图片上传与 OCR，后续可扩展）。

---

## 环境要求

- **Python 3.10 ~ 3.13**（见下方「要不要升级 Python」）
- **DeepSeek API Key**（推荐，从 [DeepSeek 控制台](https://platform.deepseek.com/api_keys) 获取）
- 或 **OpenAI API Key**（在 `.env` 里切换 `LLM_PROVIDER=openai`）

### 要不要升级 Python？

| 情况 | 建议 |
|------|------|
| 你已经在用项目里的 `.venv` | **不用升级**，里面已是 Python 3.12 |
| 系统默认 `python` 是 3.8 | **不用卸载 3.8**，运行时用 `py -3.12` 或激活 `.venv` 即可 |
| 还没装 3.10+ | 从 [python.org](https://www.python.org/downloads/) 安装 3.12，安装时勾选「Add to PATH」 |

CrewAI **不支持 Python 3.8**，必须用 3.10～3.13。

---

## 快速开始（3 步）

### 第 1 步：进入项目目录

```powershell
cd C:\Users\22877\Projects\pm-insight-agent
```

### 第 2 步：安装依赖

```powershell
# 用 Python 3.12 创建虚拟环境（推荐）
py -3.12 -m venv .venv

# 激活虚拟环境
.\.venv\Scripts\Activate.ps1

# 安装依赖（首次约 1～3 分钟）
pip install -r requirements.txt
```

若 PowerShell 提示「无法加载脚本」，先执行：

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

### 第 3 步：配置 DeepSeek API Key 并运行

```powershell
# 复制环境变量模板
copy .env.example .env

# 用记事本编辑 .env，把 DEEPSEEK_API_KEY 改成你的真实 Key
notepad .env

# 运行程序
python main.py
```

启动后会显示：`[配置] 使用 deepseek 模型：deepseek-chat`

**改用 OpenAI**：在 `.env` 里设置 `LLM_PROVIDER=openai` 并填写 `OPENAI_API_KEY`。

---

## 如何使用

1. 运行 `python main.py` 后，按提示**粘贴**你的文本（可多段混合）。
2. 粘贴完成后，**单独输入一行** `END`（必须大写或小写均可，程序会识别）。
3. 等待 1～3 分钟，AI 会依次由 5 个「虚拟同事」完成分析。
4. 终端会打印完整报告，同时保存到 `output/pm_insight_report_时间戳.md`。

### 输入示例

```
【会议记录 2024-05-20】
参会：张三（销售）、李四（客服）、王五（PM）
讨论：客户抱怨导出 Excel 太慢，每次要 5 分钟...
王五：建议先做异步导出，MVP 只支持 CSV。

【微信用户反馈】
用户A：能不能加个 dark mode，晚上看太刺眼
用户B：希望有批量删除功能

我的想法：下个版本优先做导出优化，dark mode 可以放到 v2
END
```

---

## 项目结构

```
pm-insight-agent/
├── main.py           # 主程序：读输入、跑 Crew、保存报告
├── requirements.txt  # Python 依赖
├── .env.example      # API Key 配置模板
├── .env              # 你的真实配置（勿提交到 Git）
├── output/           # 自动生成的分析报告（.md）
└── README.md         # 本说明文档
```

---

## 5 个 AI Agent 分工

| Agent | 职责 |
|-------|------|
| 信息整理员 | 清洗文本、区分来源、提取人物/场景/问题 |
| 用户洞察分析师 | 痛点、显性/隐性需求、情绪与动机 |
| 产品经理 | 需求拆解、优先级、MVP、风险 |
| 方案设计师 | 用户流程、功能、页面、交互、验收标准 |
| 文档编辑 | 汇总为完整中文 Markdown 报告 |

---

## 常见问题

### 1. 提示「未找到有效的 DEEPSEEK_API_KEY」

- 确认已创建 `.env` 文件（不是只有 `.env.example`）
- 确认 `LLM_PROVIDER=deepseek` 且 `DEEPSEEK_API_KEY` 已填写
- Key 在 [DeepSeek 平台](https://platform.deepseek.com/api_keys) 创建，不要有多余空格

### 2. `python` 版本不对 / 安装 crewai 失败

本机默认可能是 Python 3.8，请始终用 3.12：

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

### 3. 分析很慢或超时

- 输入文本越长，耗时越久；可先粘贴核心段落试跑
- 检查网络是否能访问 OpenAI API

### 4. 报告保存在哪？

每次运行会在 `output/` 下生成带时间戳的 `.md` 文件，可用 Typora、VS Code 或 Cursor 打开编辑。

---

## 后续扩展（路线图）

- [ ] 截图上传 + OCR 自动识别
- [ ] 支持导出 Word / PDF
- [ ] 接入飞书 / 钉钉 webhook

---

## 许可证

MIT — 自由使用与修改。
