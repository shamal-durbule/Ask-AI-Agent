import { useState } from 'react'
import { Check, Edit3, X, AlertTriangle } from 'lucide-react'
import type { PendingApproval } from '../../types'

interface Props {
  approval: PendingApproval
  status: 'pending' | 'approved' | 'rejected'
  onApprove: () => void
  onReject: () => void
  onEdit: (params: Record<string, unknown>) => void
}

export default function ApprovalCard({ approval, status, onApprove, onReject, onEdit }: Props) {
  const [isEditing, setIsEditing] = useState(false)
  const [editedParams, setEditedParams] = useState<Record<string, unknown>>(
    approval.params,
  )

  const handleParamChange = (key: string, value: string) => {
    setEditedParams((prev) => ({ ...prev, [key]: value }))
  }

  const handleEditSubmit = () => {
    onEdit(editedParams)
    setIsEditing(false)
  }

  const actionLabel = {
    send_message: 'Send Message',
    schedule_message: 'Schedule Message',
    apply_credit: 'Apply Credit',
  }[approval.action] ?? approval.action

  if (status === 'approved') {
    return (
      <div className="border border-green-200 bg-green-50 rounded-xl p-4">
        <div className="flex items-center gap-2 text-green-700 text-sm font-medium">
          <Check size={16} />
          {actionLabel} - Approved
        </div>
        <p className="text-green-600 text-xs mt-1">{approval.preview}</p>
      </div>
    )
  }

  if (status === 'rejected') {
    return (
      <div className="border border-red-200 bg-red-50 rounded-xl p-4">
        <div className="flex items-center gap-2 text-red-700 text-sm font-medium">
          <X size={16} />
          {actionLabel} - Rejected
        </div>
        <p className="text-red-600 text-xs mt-1">No changes were made.</p>
      </div>
    )
  }

  return (
    <div className="border border-amber-200 bg-amber-50 rounded-xl p-4 space-y-3">
      {/* Header */}
      <div className="flex items-center gap-2 text-amber-800">
        <AlertTriangle size={16} />
        <span className="text-sm font-semibold">Approval Required: {actionLabel}</span>
      </div>

      {/* Preview */}
      <div className="bg-white rounded-lg p-3 border border-amber-100">
        <p className="text-sm text-slate-700">{approval.preview}</p>
      </div>

      {/* Editable params */}
      {isEditing && (
        <div className="bg-white rounded-lg p-3 border border-blue-200 space-y-2">
          {Object.entries(editedParams).map(([key, value]) => (
            <div key={key}>
              <label className="text-xs font-medium text-slate-500 block mb-1">
                {key}
              </label>
              <input
                type="text"
                value={String(value ?? '')}
                onChange={(e) => handleParamChange(key, e.target.value)}
                className="w-full px-3 py-1.5 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400"
              />
            </div>
          ))}
        </div>
      )}

      {/* Action buttons */}
      <div className="flex gap-2">
        {isEditing ? (
          <>
            <button
              onClick={handleEditSubmit}
              className="flex items-center gap-1.5 px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-500 transition-colors"
            >
              <Check size={14} />
              Approve with Changes
            </button>
            <button
              onClick={() => {
                setIsEditing(false)
                setEditedParams(approval.params)
              }}
              className="px-4 py-2 text-sm text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"
            >
              Cancel
            </button>
          </>
        ) : (
          <>
            <button
              onClick={onApprove}
              className="flex items-center gap-1.5 px-4 py-2 bg-green-600 text-white text-sm rounded-lg hover:bg-green-500 transition-colors"
            >
              <Check size={14} />
              Approve
            </button>
            <button
              onClick={onReject}
              className="flex items-center gap-1.5 px-4 py-2 bg-red-500 text-white text-sm rounded-lg hover:bg-red-400 transition-colors"
            >
              <X size={14} />
              Reject
            </button>
            <button
              onClick={() => setIsEditing(true)}
              className="flex items-center gap-1.5 px-4 py-2 border border-slate-300 text-slate-600 text-sm rounded-lg hover:bg-slate-50 transition-colors"
            >
              <Edit3 size={14} />
              Edit
            </button>
          </>
        )}
      </div>
    </div>
  )
}
