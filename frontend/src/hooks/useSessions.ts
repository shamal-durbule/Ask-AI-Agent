import { useCallback, useEffect, useState } from 'react'
import { api } from '../services/api'
import type { ChatSession } from '../types'

export function useSessions() {
  const [sessions, setSessions] = useState<ChatSession[]>([])
  const [loading, setLoading] = useState(true)

  const refresh = useCallback(async () => {
    try {
      const data = await api.listSessions()
      setSessions(data)
    } catch {
      // Silently fail -- sessions are supplementary
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    refresh()
    const interval = setInterval(refresh, 10000)
    return () => clearInterval(interval)
  }, [refresh])

  return { sessions, loading, refresh }
}
