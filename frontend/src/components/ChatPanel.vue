<script setup lang="ts">
import { nextTick, ref, watch } from 'vue'
import type { ChatMessage } from '../types/chat'

const props = defineProps<{ messages: ChatMessage[]; isStreaming: boolean }>()
const panel = ref<HTMLElement | null>(null)

watch(() => props.messages.map((message) => message.content).join('').length, async () => {
  await nextTick()
  panel.value?.scrollTo({ top: panel.value.scrollHeight, behavior: 'smooth' })
})
</script>

<template>
  <div ref="panel" class="message-list" aria-live="polite">
    <div class="date-divider"><span></span><small>今天 · 与小简的对话</small><span></span></div>
    <article v-for="message in messages" :key="message.id" class="message-row" :class="message.role">
      <div v-if="message.role === 'assistant'" class="message-avatar"><span class="service-mark">简</span></div>
      <div class="message-body">
        <div class="message-name">{{ message.role === 'assistant' ? '小简' : '我' }}</div>
        <div class="message-bubble" :class="{ typing: message.role === 'assistant' && isStreaming && !message.content }">
          <template v-if="message.content">{{ message.content }}<span v-if="message.role === 'assistant' && isStreaming" class="stream-cursor"></span></template>
          <span v-else-if="message.role === 'assistant' && isStreaming" class="typing-dots"><i></i><i></i><i></i></span>
        </div>
      </div>
    </article>
  </div>
</template>
