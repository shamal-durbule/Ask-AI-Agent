import { useCallback, useRef, useState } from 'react'
import { api } from '../services/api'
import type { PendingApproval, SSEEvent, UIMessage } from '../types'

let msgCounter = 0
function genId(): string {
  return `msg-${Date.now()}-${++msgCounter}`
}

export function useChat() {
  const [messages, setMessages] = useState<UIMessage[]>([])
  const [isStreaming, setIsStreaming] = useState(false)
  const [sessionId, setSessionId] = useState<string | undefined>()
  const [pendingApproval, setPendingApproval] = useState<PendingApproval | null>(null)
  const [activeTool, setActiveTool] = useState<string | null>(null)

  const abortRef = useRef<AbortController | null>(null)

  const processSSEEvents = useCallback(
    async (events: AsyncGenerator<SSEEvent>, assistantMsgId: string) => {
      for await (const event of events) {
        switch (event.type) {
          case 'text':
            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantMsgId
                  ? { ...m, content: m.content + (event.content ?? ''), isStreaming: true }
                  : m,
              ),
            )
            break

          case 'tool_start':
            setActiveTool(event.tool ?? null)
            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantMsgId ? { ...m, toolName: event.tool } : m,
              ),
            )
            break

          case 'tool_end':
            setActiveTool(null)
            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantMsgId ? { ...m, toolName: undefined } : m,
              ),
            )
            break

          case 'approval_required':
            if (event.interrupt_id) {
              const approval: PendingApproval = {
                interrupt_id: event.interrupt_id,
                action: event.action ?? '',
                params: event.params ?? {},
                preview: event.preview ?? '',
                session_id: event.session_id ?? sessionId ?? '',
              }
              setPendingApproval(approval)
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === assistantMsgId
                    ? { ...m, approval, approvalStatus: 'pending' as const, isStreaming: false }
                    : m,
                ),
              )
            }
            break

          case 'done':
            if (event.session_id) {
              setSessionId(event.session_id)
            }
            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantMsgId ? { ...m, isStreaming: false } : m,
              ),
            )
            break

          case 'error':
            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantMsgId
                  ? { ...m, content: m.content + `\n\nError: ${event.message ?? 'Unknown error'}`, isStreaming: false }
                  : m,
              ),
            )
            break
        }
      }
    },
    [sessionId],
  )

  const sendMessage = useCallback(
    async (content: string) => {
      if (isStreaming) return

      const userMsg: UIMessage = {
        id: genId(),
        role: 'user',
        content,
        timestamp: new Date(),
      }

      const assistantMsgId = genId()
      const assistantMsg: UIMessage = {
        id: assistantMsgId,
        role: 'assistant',
        content: '',
        isStreaming: true,
        timestamp: new Date(),
      }

      setMessages((prev) => [...prev, userMsg, assistantMsg])
      setIsStreaming(true)
      setPendingApproval(null)

      try {
        const events = api.streamChat(content, sessionId)
        await processSSEEvents(events, assistantMsgId)
      } catch (err) {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantMsgId
              ? { ...m, content: `Error: ${err instanceof Error ? err.message : 'Connection failed'}`, isStreaming: false }
              : m,
          ),
        )
      } finally {
        setIsStreaming(false)
        setActiveTool(null)
      }
    },
    [isStreaming, sessionId, processSSEEvents],
  )

  const handleApproval = useCallback(
    async (decision: 'approve' | 'reject' | 'edit', editedParams?: Record<string, unknown>) => {
      if (!pendingApproval) return

      // Update approval status on the message
      setMessages((prev) =>
        prev.map((m) =>
          m.approval?.interrupt_id === pendingApproval.interrupt_id
            ? { ...m, approvalStatus: decision === 'reject' ? 'rejected' as const : 'approved' as const }
            : m,
        ),
      )

      const assistantMsgId = genId()
      const assistantMsg: UIMessage = {
        id: assistantMsgId,
        role: 'assistant',
        content: '',
        isStreaming: true,
        timestamp: new Date(),
      }

      setMessages((prev) => [...prev, assistantMsg])
      setIsStreaming(true)

      try {
        const events = api.streamApproval(
          pendingApproval.session_id,
          pendingApproval.interrupt_id,
          decision,
          editedParams,
        )
        await processSSEEvents(events, assistantMsgId)
      } catch (err) {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantMsgId
              ? { ...m, content: `Error: ${err instanceof Error ? err.message : 'Unknown'}`, isStreaming: false }
              : m,
          ),
        )
      } finally {
        setIsStreaming(false)
        setPendingApproval(null)
      }
    },
    [pendingApproval, processSSEEvents],
  )

  const startNewChat = useCallback(() => {
    setMessages([])
    setSessionId(undefined)
    setPendingApproval(null)
    setActiveTool(null)
  }, [])

  const loadSession = useCallback(async (id: string) => {
    try {
      const apiMessages = await api.getMessages(id)
      const uiMessages: UIMessage[] = apiMessages
        .filter((m) => m.role === 'user' || m.role === 'assistant')
        .map((m) => ({
          id: m.id,
          role: m.role as 'user' | 'assistant',
          content: m.content,
          timestamp: new Date(m.created_at),
        }))
      setMessages(uiMessages)
      setSessionId(id)
      setPendingApproval(null)
    } catch {
      // Session may have no messages yet
      setMessages([])
      setSessionId(id)
    }
  }, [])

  return {
    messages,
    isStreaming,
    sessionId,
    pendingApproval,
    activeTool,
    sendMessage,
    handleApproval,
    startNewChat,
    loadSession,
  }
}
