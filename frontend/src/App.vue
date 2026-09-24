<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
import ChatPanel from './components/ChatPanel.vue'
import { useChatStore } from './stores/chat'

const chat = useChatStore()
const draft = ref('')
const transcript = ref<HTMLElement | null>(null)
const hasMessages = computed(() => chat.messages.length > 0)

watch(() => chat.messages.map((message) => message.content).join('').length, async () => {
  await nextTick()
  transcript.value?.scrollTo({ top: transcript.value.scrollHeight, behavior: 'smooth' })
})

async function send() {
  const message = draft.value.trim()
  if (!message || chat.isStreaming) return
  draft.value = ''
  await chat.sendMessage(message)
}

function useSuggestion(value: string) {
  draft.value = value
}
</script>

<template>
  <div class="app-shell">
    <aside class="sidebar">
      <a class="brand" href="#" aria-label="简购客服首页">
        <span class="brand-mark">简</span>
        <span class="brand-name">简购<span>JIAN GOU</span></span>
      </a>

      <button class="new-chat" type="button" @click="chat.startNewConversation">
        <span class="plus-icon">＋</span> 开始新对话
      </button>

      <div class="side-label">工作台</div>
      <button class="nav-item active" type="button">
        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 5.75A2.75 2.75 0 0 1 6.75 3h10.5A2.75 2.75 0 0 1 20 5.75v7.5A2.75 2.75 0 0 1 17.25 16H10l-4.75 4v-4.25A2.75 2.75 0 0 1 4 13.25z" /></svg>
        <span>智能客服</span><span class="nav-dot"></span>
      </button>
      <button class="nav-item muted" type="button" title="本章暂不包含工单功能">
        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 4.5h14v15H5zM8 8h8M8 12h8M8 16h5" /></svg>
        <span>服务记录</span><span class="soon-label">即将推出</span>
      </button>

      <div class="sidebar-bottom">
        <div class="help-card">
          <div class="help-icon">i</div>
          <div><strong>需要更多帮助？</strong><p>服务时间 9:00 — 21:00</p></div>
          <span class="help-arrow">↗</span>
        </div>
        <button class="profile" type="button">
          <span class="profile-avatar">林</span>
          <span class="profile-copy"><strong>林同学</strong><small>个人账户</small></span>
          <span class="profile-menu">···</span>
        </button>
      </div>
    </aside>

    <main class="main-area">
      <header class="topbar">
        <div class="breadcrumb"><span>工作台</span><b>/</b><strong>智能客服</strong></div>
        <div class="topbar-right"><span class="secure-label"><span class="secure-dot"></span> 对话安全加密</span><button class="icon-button" aria-label="帮助" type="button">?</button></div>
      </header>

      <section class="chat-layout">
        <div class="chat-column">
          <div class="support-header">
            <div class="support-avatar"><span class="service-mark">简</span></div>
            <div class="support-details"><div class="support-title">小简 <span class="ai-badge">AI 客服</span></div><div class="support-status"><span></span> 在线为你服务</div></div>
            <button class="more-button" type="button" aria-label="更多选项">···</button>
          </div>

          <div ref="transcript" class="transcript" :class="{ 'transcript-empty': !hasMessages }">
            <div v-if="!hasMessages" class="welcome-state">
              <div class="welcome-sparkle">✳</div>
              <div class="eyebrow">JIANGOU SERVICE · ALWAYS HERE</div>
              <h1>你好，我是小简。<br /><span>有什么可以帮你？</span></h1>
              <p class="welcome-copy">无论是商品问题还是售后咨询，都可以告诉我。<br />我会认真听，也会尽力帮你理清下一步。</p>
              <div class="suggestions-label">你可以试着问我</div>
              <div class="suggestions">
                <button type="button" @click="useSuggestion('我的订单还没收到，想了解一下物流情况。')"><span>◷</span> 订单物流一直没更新</button>
                <button type="button" @click="useSuggestion('收到的商品有破损，我想申请退货退款。')"><span>◇</span> 商品有问题，想申请售后</button>
                <button type="button" @click="useSuggestion('我想咨询退货流程，需要准备什么？')"><span>↗</span> 了解退换货流程</button>
              </div>
            </div>
            <ChatPanel v-else :messages="chat.messages" :is-streaming="chat.isStreaming" />
          </div>

          <div class="composer-area">
            <div v-if="chat.error" class="error-banner" role="alert"><span>!</span>{{ chat.error }}<button type="button" @click="chat.error = ''" aria-label="关闭错误">×</button></div>
            <form class="composer" @submit.prevent="send">
              <textarea v-model="draft" rows="1" :disabled="chat.isStreaming" placeholder="描述你遇到的问题，或直接向小简提问…" aria-label="输入消息" @keydown.enter.exact.prevent="send" />
              <div class="composer-footer"><span class="composer-hint"><kbd>Enter</kbd> 发送 <i></i> <kbd>Shift + Enter</kbd> 换行</span><button class="send-button" type="submit" :disabled="!draft.trim() || chat.isStreaming" aria-label="发送消息"><svg viewBox="0 0 24 24"><path d="M5 12h14M13 6l6 6-6 6" /></svg></button></div>
            </form>
            <div class="disclaimer"><span>✦</span> 小简的回答由 AI 生成，请结合实际情况判断。</div>
          </div>
        </div>
      </section>
    </main>
  </div>
</template>
