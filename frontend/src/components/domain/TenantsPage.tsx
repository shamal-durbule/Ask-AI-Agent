import { useEffect, useState } from 'react'
import { Users, Mail, Phone, Home } from 'lucide-react'
import { api } from '../../services/api'
import type { Tenant } from '../../types'

export default function TenantsPage() {
  const [tenants, setTenants] = useState<Tenant[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api
      .listTenants()
      .then(setTenants)
      .catch((e) => setError(e instanceof Error ? e.message : 'Failed to load'))
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-full text-red-500">
        {error}
      </div>
    )
  }

  return (
    <div className="h-full overflow-y-auto">
      <header className="border-b border-slate-200 px-6 py-4 bg-white sticky top-0 z-10">
        <h2 className="text-lg font-semibold text-slate-800 flex items-center gap-2">
          <Users size={20} className="text-blue-500" />
          Tenants
        </h2>
        <p className="text-sm text-slate-500 mt-0.5">
          {tenants.length} tenants, {tenants.filter((t) => t.active_lease).length} with active leases
        </p>
      </header>

      <div className="p-6">
        <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-sm">
          <table className="w-full">
            <thead>
              <tr className="border-b border-slate-100 bg-slate-50">
                <th className="text-left px-5 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Tenant</th>
                <th className="text-left px-5 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Contact</th>
                <th className="text-left px-5 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Unit</th>
                <th className="text-left px-5 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Rent</th>
                <th className="text-left px-5 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Lease Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {tenants.map((tenant) => (
                <tr key={tenant.id} className="hover:bg-slate-50 transition-colors">
                  <td className="px-5 py-3.5">
                    <p className="font-medium text-sm text-slate-800">{tenant.name}</p>
                  </td>
                  <td className="px-5 py-3.5">
                    <div className="text-sm text-slate-600 space-y-0.5">
                      <p className="flex items-center gap-1.5">
                        <Mail size={12} className="text-slate-400" />
                        {tenant.email}
                      </p>
                      <p className="flex items-center gap-1.5">
                        <Phone size={12} className="text-slate-400" />
                        {tenant.phone}
                      </p>
                    </div>
                  </td>
                  <td className="px-5 py-3.5">
                    {tenant.active_lease ? (
                      <div className="text-sm">
                        <p className="flex items-center gap-1.5 text-slate-800">
                          <Home size={12} className="text-slate-400" />
                          {tenant.active_lease.unit_label}
                        </p>
                        <p className="text-xs text-slate-500">{tenant.active_lease.property_name}</p>
                      </div>
                    ) : (
                      <span className="text-sm text-slate-400">No active lease</span>
                    )}
                  </td>
                  <td className="px-5 py-3.5">
                    {tenant.active_lease ? (
                      <span className="text-sm font-medium text-slate-800">
                        ${tenant.active_lease.rent_amount.toLocaleString()}
                      </span>
                    ) : (
                      <span className="text-sm text-slate-400">-</span>
                    )}
                  </td>
                  <td className="px-5 py-3.5">
                    {tenant.active_lease ? (
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-700">
                        Active
                      </span>
                    ) : (
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-500">
                        None
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
