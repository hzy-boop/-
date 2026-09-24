export type ChatRole = 'user' | 'assistant'

export interface ChatMessage {
  id: string
  role: ChatRole
  content: string
}

export interface StreamHandlers {
  onToken: (text: string) => void
  onDone: (conversationId: string) => void
}
