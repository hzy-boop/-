import { defineStore } from 'pinia'
import { ref } from 'vue'
import { streamChat } from '../services/chat'
import type { ChatMessage } from '../types/chat'

export const useChatStore = defineStore('chat', () => {
  const conversationId = ref<string | null>(null)
  const messages = ref<ChatMessage[]>([])
  const isStreaming = ref(false)
  const error = ref('')

  async function sendMessage(value: string) {
    const text = value.trim()
    if (!text || isStreaming.value) return

    error.value = ''
    isStreaming.value = true
    messages.value.push({ id: crypto.randomUUID(), role: 'user', content: text })
    const answer: ChatMessage = {
      id: crypto.randomUUID(),
      role: 'assistant',
      content: '',
    }
    messages.value.push(answer)

    try {
      await streamChat(conversationId.value, text, {
        onToken: (token) => { answer.content += token },
        onDone: (id) => { conversationId.value = id },
      })
    } catch (cause) {
      error.value = cause instanceof Error ? cause.message : '暂时无法连接客服，请稍后重试。'
      if (!answer.content) messages.value.pop()
    } finally {
      isStreaming.value = false
    }
  }

  function startNewConversation() {
    if (isStreaming.value) return
    conversationId.value = null
    messages.value = []
    error.value = ''
  }

  return { conversationId, messages, isStreaming, error, sendMessage, startNewConversation }
})
