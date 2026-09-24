# 电商智能客服 · 第一章：纯对话

本章包含 FastAPI + LangChain 后端和 Vue 3 + TypeScript + Pinia 聊天页面。客服不调用工具或订单系统；会话历史保存在后端进程内，服务重启后会清空。跨提供商 token 预算使用 `tiktoken` `cl100k_base` 近似计数，不等同于 Claude、DeepSeek 或 Ollama 的精确 tokenizer。

## 启动

在仓库根目录打开 PowerShell。

```powershell
cd backend
py -3.12 -m venv .venv
\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
# 编辑 .env，设置 LLM_BASE_URL、LLM_MODEL、LLM_API_KEY
python -m uvicorn app.main:app --reload --port 8000
```

另开 PowerShell 窗口启动前端：

```powershell
cd frontend
npm install
npm run dev
```

打开 Vite 显示的本地地址（默认 `http://localhost:5173`）。开发代理会把 `/api` 转发到 `http://localhost:8000`。真实密钥只放在 `backend/.env`，该文件已加入 `.gitignore`。

DeepSeek V4 Pro 示例：

```dotenv
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-v4-pro
LLM_API_KEY=你的密钥
```

## 演示命令

在 PowerShell 中执行。第一轮展示 `token` 流和 `done` 会话 ID：

```powershell
$first = curl.exe -sS -N -H "Content-Type: application/json" -d '{"conversation_id":null,"message":"我的订单 A123 还没收到，想了解进度。"}' http://localhost:8000/api/chat/stream
$first
```

从 `done` 的 JSON 复制 `conversation_id`，替换下面的值，验证第二轮能引用第一轮订单号：

```powershell
curl.exe -sS -N -H "Content-Type: application/json" -d '{"conversation_id":"粘贴会话ID","message":"我刚才的订单号是什么？"}' http://localhost:8000/api/chat/stream
```

售后描述结构化提取（字段缺失时为 `null`）：

```powershell
curl.exe -sS -H "Content-Type: application/json" -d '{"description":"订单 A123 的商品破损了，希望退款。"}' http://localhost:8000/api/after-sales/extract
```

## 验证

```powershell
cd backend
python -m pytest -p no:cacheprovider tests -q
python -m tests.test_prompts_eval
python -m tests.test_after_sales_eval
cd ..\frontend
npm run build
```

两个 `test_*_eval` 命令会调用 `.env` 配置的真实上游模型；它们是人工核对实际输出与标注标准的评估脚本。自动化后端测试不需要调用模型。
