import { Building2, MessageSquarePlus, MessagesSquare, Users } from 'lucide-react'
import { NavLink, useNavigate } from 'react-router-dom'
import { useSessions } from '../../hooks/useSessions'

export default function Sidebar() {
  const { sessions } = useSessions()
  const navigate = useNavigate()

  return (
    <aside className="w-72 bg-slate-900 text-slate-200 flex flex-col h-full border-r border-slate-800">
      {/* Header */}
      <div className="px-4 py-5 border-b border-slate-800">
        <h1 className="text-lg font-bold text-white flex items-center gap-2">
          <Building2 size={22} className="text-blue-400" />
          Ask AI Agent
        </h1>
        <p className="text-xs text-slate-400 mt-1">Property Management Assistant</p>
      </div>

      {/* New Chat */}
      <div className="px-3 py-3">
        <button
          onClick={() => navigate('/')}
          className="w-full flex items-center gap-2 px-3 py-2.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium transition-colors"
        >
          <MessageSquarePlus size={16} />
          New Chat
        </button>
      </div>

      {/* Navigation */}
      <nav className="px-3 space-y-1">
        <NavLink
          to="/properties"
          className={({ isActive }) =>
            `flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors ${
              isActive ? 'bg-slate-800 text-white' : 'text-slate-400 hover:bg-slate-800 hover:text-white'
            }`
          }
        >
          <Building2 size={16} />
          Properties
        </NavLink>
        <NavLink
          to="/tenants"
          className={({ isActive }) =>
            `flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors ${
              isActive ? 'bg-slate-800 text-white' : 'text-slate-400 hover:bg-slate-800 hover:text-white'
            }`
          }
        >
          <Users size={16} />
          Tenants
        </NavLink>
      </nav>

      {/* Session History */}
      <div className="mt-4 px-3 flex-1 overflow-y-auto">
        <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider px-3 mb-2">
          Recent Chats
        </h3>
        <div className="space-y-0.5">
          {sessions.map((session) => (
            <NavLink
              key={session.id}
              to={`/chat/${session.id}`}
              className={({ isActive }) =>
                `flex items-center gap-2 px-3 py-2 rounded-lg text-sm truncate transition-colors ${
                  isActive ? 'bg-slate-800 text-white' : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'
                }`
              }
            >
              <MessagesSquare size={14} className="shrink-0" />
              <span className="truncate">{session.title}</span>
            </NavLink>
          ))}
          {sessions.length === 0 && (
            <p className="text-xs text-slate-600 px-3 py-2">No conversations yet</p>
          )}
        </div>
      </div>
    </aside>
  )
}
