import type { ChatSession, ChatMessage, Property, Tenant, SSEEvent } from '../types'

const BASE_URL = '/api'

async function fetchJSON<T>(url: string): Promise<T> {
  const res = await fetch(`${BASE_URL}${url}`)
  if (!res.ok) {
    throw new Error(`API error: ${res.status} ${res.statusText}`)
  }
  return res.json() as Promise<T>
}

export const api = {
  // Chat sessions
  listSessions: () => fetchJSON<ChatSession[]>('/chat/sessions'),
  getMessages: (sessionId: string) => fetchJSON<ChatMessage[]>(`/chat/sessions/${sessionId}/messages`),

  // Domain
  listProperties: () => fetchJSON<Property[]>('/properties'),
  listTenants: () => fetchJSON<Tenant[]>('/tenants'),

  // Streaming chat (POST-based SSE)
  streamChat: async function* (
    message: string,
    sessionId?: string,
  ): AsyncGenerator<SSEEvent> {
    const res = await fetch(`${BASE_URL}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, session_id: sessionId }),
    })

    if (!res.ok || !res.body) {
      throw new Error(`Chat error: ${res.status}`)
    }

    yield* parseSSEStream(res.body)
  },

  // Approval
  streamApproval: async function* (
    sessionId: string,
    interruptId: string,
    decision: 'approve' | 'reject' | 'edit',
    editedParams?: Record<string, unknown>,
  ): AsyncGenerator<SSEEvent> {
    const res = await fetch(`${BASE_URL}/chat/sessions/${sessionId}/approve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        interrupt_id: interruptId,
        decision,
        edited_params: editedParams,
      }),
    })

    if (!res.ok || !res.body) {
      throw new Error(`Approval error: ${res.status}`)
    }

    yield* parseSSEStream(res.body)
  },
}

async function* parseSSEStream(body: ReadableStream<Uint8Array>): AsyncGenerator<SSEEvent> {
  const reader = body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() ?? ''

      let currentEventType = ''

      for (const line of lines) {
        if (line.startsWith('event: ')) {
          currentEventType = line.slice(7).trim()
        } else if (line.startsWith('data: ')) {
          const jsonStr = line.slice(6)
          try {
            const parsed = JSON.parse(jsonStr) as SSEEvent
            if (currentEventType && !parsed.type) {
              parsed.type = currentEventType as SSEEvent['type']
            }
            yield parsed
          } catch {
            // Skip malformed JSON
          }
          currentEventType = ''
        }
      }
    }
  } finally {
    reader.releaseLock()
  }
}
