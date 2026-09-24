# 电商智能客服系统第 1 章：纯对话设计

## 目标与范围

本章交付一个可运行的电商智能客服原型，先打通纯对话，不接工具调用或 Agent 循环。验收方式是用 curl 观察流式回复、连续两轮对话验证上下文，以及提交售后描述并取得结构化 JSON。

后端使用 Python、FastAPI 与 LangChain；前端使用 Vue 3、TypeScript 与 Pinia。模型通过 LangChain `ChatOpenAI` 统一调用采用 OpenAI 协议的上游服务。上游地址、模型名和密钥由 `.env` 配置，支持 GPT、Claude、DeepSeek 和 Ollama 的 OpenAI 兼容接口。

## 架构与数据流

- FastAPI 提供纯对话 SSE 接口及售后结构化抽取接口。
- LangChain `ChatOpenAI` 负责模型连接、流式聊天和结构化输出。
- 会话历史由服务进程内存按 `conversation_id` 保存；服务重启会清空历史，不保证多实例间共享。
- Vue 3 + TypeScript + Pinia 页面创建/持有会话 ID，提交消息并增量展示 SSE 文本。
- 配置由环境变量加载；仓库提供不含真实密钥的 `.env.example`。

## 对话接口与上下文

`POST /api/chat` 请求 JSON 包含 `conversation_id` 与本轮 `message`。响应类型为 `text/event-stream`，服务端转发模型流的文本片段，并以 SSE `done` 事件结束；失败通过 SSE `error` 事件表达。完成的用户消息和助手答复进入会话历史。

构造模型输入时始终保留 system prompt 和当前用户消息，从最近的历史轮次向前裁剪，直到估算 token 数不超过配置预算。预算还需给模型输出预留空间。模型输入只包含完整历史轮次，不截断单条消息。首轮允许客户端生成 UUID 作为会话 ID。

## Prompt 管理

客服 system prompt 使用 LangChain `PromptTemplate` 管理，并明确客服身份、准确清晰的表达、不得编造订单或政策信息、信息不足时追问，以及不得声称执行本章尚未接入的操作。

## 售后结构化抽取

`POST /api/after-sales/extract` 接收售后描述，使用 `with_structured_output` 解析为 JSON 对象，字段固定为：

- `order_number`: 订单号或 `null`
- `request_type`: 用户诉求类型短文本或 `null`
- `expected_resolution`: 用户期望方案或 `null`

原文未提供的字段必须返回 `null`，不推断或捏造。抽取错误使用明确的非 2xx HTTP 错误响应。

## 前端体验

聊天页包含消息列表、输入框、发送按钮、流式增量显示和生成中状态，并支持停止当前生成。停止通过取消前端请求中断 SSE；刷新页面不保证恢复历史。按用户要求，聊天页面采用 vibe coding 直接迭代，不套 brainstorming、TDD、code review 流程。

## 配置与错误处理

通过 `.env` 配置上游 `base_url`、`model`、`api_key`、温度、token 预算与输出预留量。缺少必要配置时应用启动失败并给出可操作错误；密钥不得回显或写入日志。对话上游错误通过 SSE `error` 表达并确保流关闭；结构化抽取错误返回非 2xx 响应。

## 验收与验证

1. curl 调用 `/api/chat` 可见逐片段 SSE 回复及终止事件。
2. 同一 `conversation_id` 连续提问第二轮可利用第一轮上下文。
3. 售后描述通过 `/api/after-sales/extract` 得到包含固定字段的 JSON。
4. 对可单测后端逻辑按 TDD 实施；纯 Prompt、数据类和结构化抽取使用标注样例/评估样例验证，不强求只写单元测试。
5. 具体库与 API 使用前，通过 Context7 查阅最新官方文档及接口定义。

## 明确不做

不做工具调用、Agent 循环、数据库持久化、多实例会话共享、订单系统/售后系统真实操作、鉴权与生产级部署。
