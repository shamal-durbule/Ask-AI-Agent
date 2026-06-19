import { Database, Loader2 } from 'lucide-react'

const TOOL_LABELS: Record<string, string> = {
  get_properties: 'Looking up properties...',
  get_tenants: 'Looking up tenants...',
  get_leases: 'Checking leases...',
  get_overdue_charges: 'Checking overdue charges...',
  get_database_schema: 'Reading database schema...',
  execute_readonly_query: 'Querying database...',
  send_message: 'Sending message...',
  schedule_message: 'Scheduling message...',
  apply_credit: 'Applying credit...',
}

interface Props {
  toolName: string
}

export default function ToolIndicator({ toolName }: Props) {
  const label = TOOL_LABELS[toolName] ?? `Using ${toolName}...`

  return (
    <div className="flex justify-start pl-10">
      <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-blue-50 text-blue-600 rounded-full text-xs font-medium">
        <Loader2 size={12} className="animate-spin" />
        <Database size={12} />
        {label}
      </div>
    </div>
  )
}
