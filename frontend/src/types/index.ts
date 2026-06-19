export interface ChatSession {
  id: string
  title: string
  created_at: string
  updated_at: string
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant' | 'system' | 'tool'
  content: string
  metadata_json?: string | null
  created_at: string
}

export type SSEEventType = 'text' | 'tool_start' | 'tool_end' | 'approval_required' | 'done' | 'error'

export interface SSEEvent {
  type: SSEEventType
  content?: string
  tool?: string
  input?: Record<string, unknown>
  interrupt_id?: string
  action?: string
  params?: Record<string, unknown>
  preview?: string
  session_id?: string
  stop_reason?: string
  message?: string
}

export interface PendingApproval {
  interrupt_id: string
  action: string
  params: Record<string, unknown>
  preview: string
  session_id: string
}

export interface UIMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  isStreaming?: boolean
  toolName?: string
  approval?: PendingApproval
  approvalStatus?: 'pending' | 'approved' | 'rejected'
  timestamp: Date
}

export interface PropertyUnit {
  id: number
  label: string
  bedrooms: number
  monthly_rent: number
  status: string
}

export interface Property {
  id: number
  name: string
  address: string
  units: PropertyUnit[]
  total_units: number
  occupied_units: number
}

export interface TenantLease {
  id: number
  unit_label: string
  property_name: string
  tenant_name: string
  rent_amount: number
  start_date: string
  end_date: string
  status: string
}

export interface Tenant {
  id: number
  name: string
  email: string
  phone: string
  active_lease: TenantLease | null
}
