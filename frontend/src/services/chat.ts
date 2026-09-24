import type { StreamHandlers } from '../types/chat'

interface SseFrame {
  event: string
  data: string
}

function parseFrame(frame: string): SseFrame | null {
  let event = 'message'
  const data: string[] = []
  for (const line of frame.split(/\r?\n/)) {
    if (line.startsWith('event:')) event = line.slice(6).trim()
    if (line.startsWith('data:')) data.push(line.slice(5).replace(/^ /, ''))
  }
  return data.length ? { event, data: data.join('\n') } : null
}

export async function streamChat(
  conversationId: string | null,
  message: string,
  handlers: StreamHandlers,
): Promise<void> {
  const response = await fetch('/api/chat/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ conversation_id: conversationId, message }),
  })

  if (!response.ok) {
    const detail = await response.text()
    const message = response.status >= 500
      ? '客服服务暂时不可用，请稍后重试。'
      : detail || `请求失败（${response.status}）`
    throw new Error(message)
  }
  if (!response.body) throw new Error('浏览器未能建立流式连接')

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let pending = ''
  let completed = false

  const handle = (rawFrame: string) => {
    const frame = parseFrame(rawFrame)
    if (!frame) return
    if (frame.event === 'token') handlers.onToken(frame.data)
    if (frame.event === 'done') {
      const payload = JSON.parse(frame.data) as { conversation_id: string }
      handlers.onDone(payload.conversation_id)
      completed = true
    }
    if (frame.event === 'error') {
      const payload = JSON.parse(frame.data) as { message?: string }
      throw new Error(payload.message || '对话暂时中断，请重试')
    }
  }

  try {
    while (true) {
      const { value, done } = await reader.read()
      pending += decoder.decode(value, { stream: !done })
      const frames = pending.split(/\r?\n\r?\n/)
      pending = frames.pop() ?? ''
      for (const frame of frames) handle(frame)
      if (done) break
    }
    if (pending.trim()) handle(pending)
    if (!completed) throw new Error('连接提前结束，请重试')
  } finally {
    reader.releaseLock()
  }
}
