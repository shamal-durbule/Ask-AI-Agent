import { useEffect, useRef } from 'react'
import { useParams } from 'react-router-dom'
import { useChat } from '../../hooks/useChat'
import { Bot, Sparkles } from 'lucide-react'
import MessageBubble from './MessageBubble'
import ChatInput from './ChatInput'
import ToolIndicator from './ToolIndicator'

const SUGGESTIONS = [
  'How much rent is outstanding this month?',
  'Which tenants are overdue?',
  'What is our occupancy rate?',
  'Show me all available units',
]

export default function ChatPage() {
  const { sessionId: routeSessionId } = useParams()
  const {
    messages,
    isStreaming,
    activeTool,
    pendingApproval,
    sendMessage,
    handleApproval,
    loadSession,
    startNewChat,
  } = useChat()

  const scrollRef = useRef<HTMLDivElement>(null)
  const userScrolledUp = useRef(false)

  useEffect(() => {
    if (routeSessionId) {
      loadSession(routeSessionId)
    } else {
      startNewChat()
    }
  }, [routeSessionId, loadSession, startNewChat])

  useEffect(() => {
    if (!userScrolledUp.current && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages, activeTool])

  const handleScroll = () => {
    if (!scrollRef.current) return
    const { scrollTop, scrollHeight, clientHeight } = scrollRef.current
    userScrolledUp.current = scrollHeight - scrollTop - clientHeight > 100
  }

  const isEmpty = messages.length === 0

  return (
    <div className="flex flex-col h-full bg-white">
      {/* Header */}
      <header className="border-b border-slate-200 px-6 py-3 flex items-center gap-2 bg-white shrink-0">
        <Bot size={20} className="text-blue-500" />
        <h2 className="font-semibold text-slate-800">Property Management Assistant</h2>
      </header>

      {/* Messages area */}
      <div
        ref={scrollRef}
        onScroll={handleScroll}
        className="flex-1 overflow-y-auto px-4 py-6"
      >
        {isEmpty ? (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <div className="w-16 h-16 rounded-2xl bg-blue-50 flex items-center justify-center mb-4">
              <Sparkles size={28} className="text-blue-500" />
            </div>
            <h3 className="text-xl font-semibold text-slate-800 mb-2">
              Property Management Assistant
            </h3>
            <p className="text-slate-500 mb-8 max-w-md">
              Ask questions about your properties, tenants, and finances. I can also
              send messages and apply credits with your approval.
            </p>
            <div className="grid grid-cols-2 gap-3 max-w-lg">
              {SUGGESTIONS.map((s) => (
                <button
                  key={s}
                  onClick={() => sendMessage(s)}
                  className="text-left px-4 py-3 rounded-xl border border-slate-200 text-sm text-slate-600 hover:bg-slate-50 hover:border-slate-300 transition-colors"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="max-w-3xl mx-auto space-y-4">
            {messages.map((msg) => (
              <MessageBubble
                key={msg.id}
                message={msg}
                onApprove={() => handleApproval('approve')}
                onReject={() => handleApproval('reject')}
                onEdit={(params) => handleApproval('edit', params)}
              />
            ))}
            {activeTool && <ToolIndicator toolName={activeTool} />}
          </div>
        )}
      </div>

      {/* Input */}
      <ChatInput
        onSend={sendMessage}
        disabled={isStreaming}
        hasPendingApproval={!!pendingApproval}
      />
    </div>
  )
}
