import { useEffect, useState } from 'react'
import { Building2, Home } from 'lucide-react'
import { api } from '../../services/api'
import type { Property } from '../../types'

export default function PropertiesPage() {
  const [properties, setProperties] = useState<Property[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api
      .listProperties()
      .then(setProperties)
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
          <Building2 size={20} className="text-blue-500" />
          Properties
        </h2>
        <p className="text-sm text-slate-500 mt-0.5">
          {properties.length} properties, {properties.reduce((s, p) => s + p.total_units, 0)} total units
        </p>
      </header>

      <div className="p-6 grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {properties.map((property) => {
          const occupancy = property.total_units > 0
            ? Math.round((property.occupied_units / property.total_units) * 100)
            : 0

          return (
            <div key={property.id} className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-sm hover:shadow-md transition-shadow">
              <div className="p-5">
                <h3 className="font-semibold text-slate-800">{property.name}</h3>
                <p className="text-sm text-slate-500 mt-0.5">{property.address}</p>

                <div className="flex gap-4 mt-4">
                  <div>
                    <p className="text-2xl font-bold text-slate-800">{property.total_units}</p>
                    <p className="text-xs text-slate-500">Total Units</p>
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-green-600">{property.occupied_units}</p>
                    <p className="text-xs text-slate-500">Occupied</p>
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-amber-600">{property.total_units - property.occupied_units}</p>
                    <p className="text-xs text-slate-500">Available</p>
                  </div>
                </div>

                {/* Occupancy bar */}
                <div className="mt-4">
                  <div className="flex justify-between text-xs text-slate-500 mb-1">
                    <span>Occupancy</span>
                    <span>{occupancy}%</span>
                  </div>
                  <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all ${
                        occupancy >= 80 ? 'bg-green-500' : occupancy >= 50 ? 'bg-amber-500' : 'bg-red-500'
                      }`}
                      style={{ width: `${occupancy}%` }}
                    />
                  </div>
                </div>
              </div>

              {/* Units list */}
              <div className="border-t border-slate-100 px-5 py-3 bg-slate-50">
                <p className="text-xs font-medium text-slate-500 mb-2">Units</p>
                <div className="flex flex-wrap gap-1.5">
                  {property.units.map((unit) => (
                    <span
                      key={unit.id}
                      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs ${
                        unit.status === 'leased'
                          ? 'bg-green-100 text-green-700'
                          : 'bg-slate-200 text-slate-600'
                      }`}
                    >
                      <Home size={10} />
                      {unit.label} ({unit.bedrooms}BR - ${unit.monthly_rent.toLocaleString()})
                    </span>
                  ))}
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
