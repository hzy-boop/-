# 电商智能客服纯对话实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现一个可运行的纯对话客服闭环，支持 SSE 多轮对话、模板化 Prompt、售后描述结构化提取，以及 Vue 聊天页面。

**Architecture:** FastAPI 后端提供 SSE 对话和售后信息提取接口；LangChain 负责模板、模型流式生成及结构化输出；进程内存保存会话，并在调用上游前按 token 预算裁剪历史。Vue 3 页面通过 SSE 消费后端流，Pinia 管理当前会话和消息状态。

**Tech Stack:** Python、FastAPI、LangChain、OpenAI 协议兼容上游、Vue 3、TypeScript、Pinia。

**Spec:** `docs/superpowers/specs/2026-09-24-ecommerce-customer-support-design.md`

## Global Constraints

- 本章不加入工具调用、Agent 循环、订单查询或其他外部业务动作。
- 本章会话存储使用进程内存储，以便跑通多轮闭环；重启后会话丢失属于已知限制。
- 字段缺失时使用 JSON `null`。
- SSE 事件名为 `token`、`done`、`error`；`done` 携带会话标识。
- 模型由 `.env` 配置 OpenAI 兼容的 base URL、模型名、API key；应用侧支持 GPT、Claude、DeepSeek、Ollama，不在代码中硬编码密钥。
- 纯 Prompt 和结构化提取使用标注样例/小型评估集验证；聊天页面按用户指定采用 vibe coding，不套 TDD 和 code review 流程。
- 在使用 FastAPI、LangChain、Vue、Pinia 及 SSE/模型客户端相关 API 前，必须先用 Context7 查对应官方文档和接口定义；记录实际选用版本。若固定技术选型与官方 API 或上游兼容性冲突，暂停并询问用户，不自行换方案。

## Review Focus

- 空白或仅空格的聊天输入：应拒绝并返回清楚的客户端错误，不调用模型。
- 未知或失效的 conversation_id：应按新会话处理或返回明确错误，行为需在 Task 2 固定并测试；推荐按新会话处理。
- 当前用户输入超过可用上下文预算：应返回可理解的输入过长错误，不静默截断当前输入。
- 上游生成中断且 SSE 已开始：应发送 `error` 事件并关闭流，不发送成功 `done`。
- 售后描述缺少全部字段：仍返回三个键，值均为 JSON `null`。

---

## 文件结构

- `backend/requirements.txt`：后端直接依赖及已查证、实测通过的精确版本。
- `backend/.env.example`：模型端点、模型名、密钥占位符及上下文预算示例；不含真实密钥。
- `backend/app/main.py`：FastAPI 应用和路由注册。
- `backend/app/config.py`：环境配置读取与启动校验。
- `backend/app/schemas.py`：请求、响应及结构化提取数据模型。
- `backend/app/prompts.py`：聊天与售后提取 PromptTemplate。
- `backend/app/memory.py`：进程内会话及历史裁剪/token 预算。
- `backend/app/llm.py`：OpenAI 协议模型客户端构造与能力边界。
- `backend/app/services/chat.py`：对话编排及流式生成。
- `backend/app/services/after_sales.py`：售后字段结构化提取。
- `backend/tests/`：后端单元、API 和评估样例。
- `frontend/package.json`、`frontend/vite.config.ts`、`frontend/tsconfig.json`：Vue/TypeScript 工程配置。
- `frontend/src/main.ts`、`frontend/src/App.vue`：应用入口和单页聊天界面。
- `frontend/src/types/chat.ts`：前后端共享的聊天/SSE 类型。
- `frontend/src/stores/chat.ts`：Pinia 会话、消息、发送和错误状态。
- `frontend/src/services/chat.ts`：聊天请求与 SSE 解析。
- `frontend/src/components/ChatPanel.vue`：消息列表和输入交互。
- `frontend/src/style.css`：聊天页面基础样式。
- `dev-notes/ch01.md`：按阶段追加过程、评审、返工和验收记录。

## Task 1: 建立后端骨架、配置和文档核验基线

**Files:**
- Create: `.gitignore`
- Create: `backend/requirements.txt`
- Create: `backend/.env.example`
- Create: `backend/app/main.py`
- Create: `backend/app/config.py`
- Create: `backend/tests/test_config.py`
- Modify: `README.md`
- Modify: `dev-notes/ch01.md`

**Interfaces:**
- Produces: `Settings` 配置对象，字段包括 `base_url`、`model_name`、`api_key`、`context_token_budget` 和 `max_output_tokens`；具体环境变量名称固定为 `LLM_BASE_URL`、`LLM_MODEL`、`LLM_API_KEY`、`CONTEXT_TOKEN_BUDGET`、`MAX_OUTPUT_TOKENS`。
- Produces: 可由 `uvicorn app.main:app` 启动的 FastAPI 应用。

- [ ] 查 Context7 官方文档：FastAPI 应用启动/配置和 LangChain OpenAI 兼容 Chat 模型的当前接口；确认所用依赖版本、初始化参数与 SSE response 类型支持。把查证结果和版本写入本任务提交说明及 `dev-notes/ch01.md`。
- [ ] 建立项目级 `.gitignore` 排除 `backend/.venv/`、`backend/.env`、`frontend/node_modules/`、`frontend/dist/`、Python cache 和 pytest cache；在 `backend/` 建立虚拟环境并安装 requirements，避免依赖写入仓库外的全局 Python 环境。
- [ ] 写配置测试，覆盖必需配置缺失、完整配置读取、预算非法值。
- [ ] 在 `backend/` 目录运行 `python -m pytest tests/test_config.py -q`，确认缺失实现时失败。
- [ ] 编写 settings 和最小 FastAPI app；requirements 只加入本章直接依赖。
- [ ] 在 `backend/` 目录运行 `python -m pytest tests/test_config.py -q`，确认配置测试通过。
- [ ] 在 README 写启动环境、复制 `.env.example`、启动服务的命令。
- [ ] 在仓库根目录运行 `python -m compileall backend/app`；预期无语法错误。

## Task 2: 对话 Prompt、会话上下文和 token 预算

**Files:**
- Create: `backend/app/schemas.py`
- Create: `backend/app/prompts.py`
- Create: `backend/app/memory.py`
- Create: `backend/app/llm.py`
- Create: `backend/tests/test_memory.py`
- Create: `backend/tests/test_prompts_eval.py`
- Modify: `dev-notes/ch01.md`

**Interfaces:**
- Consumes: Task 1 的 `Settings`。
- Produces: `ChatRequest(conversation_id: str | None, message: str)`；`get_or_create_conversation(conversation_id) -> str`；`get_history(conversation_id) -> list[BaseMessage]`；`append_turn(conversation_id, user_message, assistant_message) -> None`；`trim_history(messages, token_budget, max_output_tokens, token_counter) -> list[BaseMessage]`。
- Produces: `build_chat_prompt() -> ChatPromptTemplate`；`build_chat_model(settings, streaming: bool)`。

- [ ] 查 Context7 官方文档：LangChain PromptTemplate/ChatPromptTemplate、消息历史对象、模型 token 计数 API、OpenAI-compatible Chat model 初始化及流式参数。按文档确定 token counter 的实际调用。若任一固定上游不支持所需通用协议能力，停止并询问用户。
- [ ] 写 `test_memory.py`：新会话创建、两轮消息保存及读取、只从最旧完整轮次裁剪、保留 system 与当前 user 消息、超长当前输入抛出专用异常、未知 ID 创建新会话。
- [ ] 在 `backend/` 目录运行 `python -m pytest tests/test_memory.py -q`，确认失败。
- [ ] 实现内存会话和裁剪器。预算定义为输入可用预算 `context_token_budget - max_output_tokens`；逐轮从最旧历史移除，System Prompt 和当前消息必留；当前消息单独超预算则抛出 `InputTooLongError`。
- [ ] 在 `backend/` 目录运行 `python -m pytest tests/test_memory.py -q`，确认通过。
- [ ] 建立标注 Prompt 评估样例，至少含正常售后咨询、信息不足需追问、要求编造退款进度、缺失订单号四类；记录输入、预期行为与实际输出判定准则。
- [ ] 实现客服 System Prompt：礼貌简洁、仅依据对话信息、不臆造状态/政策、必要时逐项追问、不声称已执行外部操作。以 LangChain 模板注入历史和当前输入。
- [ ] 用可重复的小评估脚本或手工评估记录跑上述样例；确保约束样例无编造且信息不足时追问；失败时调整 Prompt 后重跑并在开发日志记录返工。

## Task 3: SSE 对话 API 和售后结构化提取 API

**Files:**
- Create: `backend/app/services/chat.py`
- Create: `backend/app/services/after_sales.py`
- Modify: `backend/app/main.py`
- Modify: `backend/app/schemas.py`
- Create: `backend/tests/test_chat_api.py`
- Create: `backend/tests/test_after_sales_eval.py`
- Modify: `dev-notes/ch01.md`

**Interfaces:**
- Consumes: Task 1 `Settings`、Task 2 的 prompt/model/memory 接口。
- Produces: `POST /api/chat/stream`，请求 `ChatRequest`，以 `text/event-stream` 返回 `event: token`（`data` 是文本片段）、`event: done`（`data` 是 `{"conversation_id":"..."}`）或 `event: error`（稳定错误码和可读信息）。
- Produces: `POST /api/after-sales/extract`，请求 `{"description":"..."}`，响应 `{"order_id": string|null, "request_type": string|null, "preferred_resolution": string|null}`。

- [ ] 查 Context7 官方文档：FastAPI StreamingResponse/SSE 相关响应行为；LangChain 流式事件/异步流 API、`with_structured_output` 的 schema 约束和解析错误行为。选定 API 前确认与 Task 1 版本一致。
- [ ] 写 API 测试，用 fake model 验证 token 顺序、done 事件含 conversation_id、上游异常变为 error 且不发送 done、空消息返回 422、两轮请求复用上下文。
- [ ] 在 `backend/` 目录运行 `python -m pytest tests/test_chat_api.py -q`，确认失败。
- [ ] 实现流式服务和 SSE 路由；只有完整生成成功后才追加用户/助手轮次；若上游中断，发 error 并确保不提交半轮历史。
- [ ] 在 `backend/` 目录运行 `python -m pytest tests/test_chat_api.py -q`，确认通过。
- [ ] 写售后评估样例，至少包括三字段齐全、仅订单号缺失、多个诉求描述不明、三个字段全缺失；期望所有响应字段齐全、缺失字段为 null、不得补造订单号。
- [ ] 实现售后 Prompt 和 Pydantic schema，通过 `with_structured_output` 返回 schema 实例并序列化为 JSON；解析失败返回明确服务错误。
- [ ] 使用标注样例运行评估，记录每个字段正确性；调整 Prompt 后重跑，保存实际结果摘要。
- [ ] 在 `backend/` 目录运行 `python -m pytest tests -q`；预期全部后端测试通过。

## Task 4: Vue 聊天页面（vibe coding）

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/tsconfig.json`
- Create: `frontend/src/main.ts`
- Create: `frontend/src/App.vue`
- Create: `frontend/src/types/chat.ts`
- Create: `frontend/src/stores/chat.ts`
- Create: `frontend/src/services/chat.ts`
- Create: `frontend/src/components/ChatPanel.vue`
- Create: `frontend/src/style.css`
- Modify: `dev-notes/ch01.md`

**Interfaces:**
- Consumes: Task 3 的 `POST /api/chat/stream` 契约与 SSE 事件格式。
- Produces: Pinia chat store 管理 `conversationId`、`messages`、`isStreaming`、`error`；`sendMessage(text)` 负责追加 user 消息并接收 SSE token 增量。

- [ ] 查 Context7 官方文档：Vue 3 Composition API、Pinia store、Vite TypeScript 工程当前用法；SSE 使用 `fetch` 流读取以支持 POST JSON 请求，并按文档确认 `ReadableStream`/TextDecoder 分块处理方式。
- [ ] 配置 Vite 开发服务器将 `/api` 代理到 `http://localhost:8000`，前端请求使用同源 `/api` 路径，支持本地开发联调。
- [ ] 直接按用户指定 vibe coding 实现聊天页面：消息列表、输入框、发送按钮、流式消息逐段追加、发送中状态、错误提示、完成后保留 conversation_id；保持页面聚焦纯对话。
- [ ] 启动前端开发服务器并人工验证：连续发两条消息、流式内容不断追加、发送中禁用重复提交、错误可见、空白输入不发送。
- [ ] 运行 `npm run build`；预期 TypeScript 检查与 Vite 构建成功。

## Task 5: 端到端验收、交付命令和最终评审

**Files:**
- Modify: `README.md`
- Modify: `dev-notes/ch01.md`
- Optionally modify only files identified by review findings.

**Interfaces:**
- Consumes: Task 1–4 完整服务和前端。
- Produces: 可复制的启动和 curl 演示命令、验收结果、已知限制记录。

- [ ] 在 `backend/` 配置未纳入版本控制的 `.env`，运行 `uvicorn app.main:app --reload --port 8000`；在 `frontend/` 运行 `npm run dev`。
- [ ] 在 PowerShell 运行 `curl.exe -N -H "Content-Type: application/json" -d '{"conversation_id":null,"message":"我的订单 A123 还没收到，想了解进度。"}' http://localhost:8000/api/chat/stream`；观察 `event: token`，从 `event: done` 的 JSON 复制 `conversation_id`。
- [ ] 将上一步复制的 ID 填入第二条命令的 `conversation_id`，并提问“我刚才的订单号是什么？”：`curl.exe -N -H "Content-Type: application/json" -d '{"conversation_id":"复制的会话ID","message":"我刚才的订单号是什么？"}' http://localhost:8000/api/chat/stream`；验证回答能引用 A123。
- [ ] 运行售后字段提取：`curl.exe -s -H "Content-Type: application/json" -d '{"description":"订单 A123 的商品破损了，希望退款。"}' http://localhost:8000/api/after-sales/extract`；确认 JSON 含三个固定字段。再用 `{"description":"商品有问题"}` 检查缺失字段为 null。
- [ ] 在 `backend/` 目录运行 `python -m pytest tests -q`，在 `frontend/` 目录运行 `npm run build`，保存命令和结果。
- [ ] 检查日志及仓库差异，确认无密钥、无工具/Agent/外部订单调用。
- [ ] 完成独立 code review；修复 Critical/Important 问题并重新验证，Minor 留痕供用户决定。
- [ ] 更新 README 演示命令和限制；在 `dev-notes/ch01.md` 记录验收、评审结论及必要返工。
