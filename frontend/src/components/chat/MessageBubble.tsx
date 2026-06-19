import { Bot, User } from 'lucide-react'
import type { UIMessage } from '../../types'
import ApprovalCard from './ApprovalCard'

interface Props {
  message: UIMessage
  onApprove: () => void
  onReject: () => void
  onEdit: (params: Record<string, unknown>) => void
}

export default function MessageBubble({ message, onApprove, onReject, onEdit }: Props) {
  const isUser = message.role === 'user'

  if (isUser) {
    return (
      <div className="flex justify-end">
        <div className="flex items-start gap-2 max-w-[75%]">
          <div className="bg-blue-600 text-white px-4 py-2.5 rounded-2xl rounded-tr-sm text-sm leading-relaxed">
            {message.content}
          </div>
          <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center shrink-0">
            <User size={16} className="text-blue-600" />
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="flex justify-start">
      <div className="flex items-start gap-2 max-w-[85%]">
        <div className="w-8 h-8 rounded-full bg-slate-100 flex items-center justify-center shrink-0 mt-0.5">
          <Bot size={16} className="text-slate-600" />
        </div>
        <div className="space-y-2">
          {message.content && (
            <div
              className={`bg-slate-100 px-4 py-2.5 rounded-2xl rounded-tl-sm text-sm leading-relaxed text-slate-800 ${
                message.isStreaming ? 'typing-cursor' : ''
              }`}
            >
              <MessageContent content={message.content} />
            </div>
          )}
          {message.approval && (
            <ApprovalCard
              approval={message.approval}
              status={message.approvalStatus ?? 'pending'}
              onApprove={onApprove}
              onReject={onReject}
              onEdit={onEdit}
            />
          )}
        </div>
      </div>
    </div>
  )
}

function MessageContent({ content }: { content: string }) {
  // Simple markdown-like rendering for tables and code
  const lines = content.split('\n')
  const elements: JSX.Element[] = []
  let inCodeBlock = false
  let codeLines: string[] = []

  lines.forEach((line, i) => {
    if (line.startsWith('```')) {
      if (inCodeBlock) {
        elements.push(
          <pre key={`code-${i}`} className="bg-slate-800 text-slate-200 rounded-lg p-3 text-xs font-mono overflow-x-auto my-2">
            {codeLines.join('\n')}
          </pre>
        )
        codeLines = []
      }
      inCodeBlock = !inCodeBlock
      return
    }

    if (inCodeBlock) {
      codeLines.push(line)
      return
    }

    if (line.startsWith('|') && line.endsWith('|')) {
      elements.push(
        <span key={i} className="font-mono text-xs block">
          {line}
        </span>
      )
      return
    }

    // Bold
    const formatted = line.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    if (formatted !== line) {
      elements.push(
        <span key={i} dangerouslySetInnerHTML={{ __html: formatted }} />
      )
    } else {
      elements.push(<span key={i}>{line}{i < lines.length - 1 ? '\n' : ''}</span>)
    }
  })

  return <span className="whitespace-pre-wrap">{elements}</span>
}
