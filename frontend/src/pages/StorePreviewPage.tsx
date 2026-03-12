import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { fetchOperationsProspects } from '@/api/prospects'
import { LoadingSpinner } from '@/components/ui/LoadingSpinner'

export function StorePreviewPage() {
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [search, setSearch] = useState('')

  const prospects = useQuery({
    queryKey: ['store-preview-prospects', search],
    queryFn: () =>
      fetchOperationsProspects({
        status: 'STORE_CREATED',
        search: search || undefined,
        limit: 100,
      }),
  })

  const selectedProspect = prospects.data?.find((p) => p.id === selectedId)
  const previewUrl = selectedProspect?.claim_token
    ? `/preview?token=${selectedProspect.claim_token}`
    : null

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900 tracking-tight">Store Preview</h1>

      <div className="flex gap-3 items-end">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Search</label>
          <input
            type="text"
            placeholder="Filter by name..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="px-3 py-2 text-sm border border-gray-300 rounded-lg w-64 focus:ring-2 focus:ring-teal-500"
          />
        </div>
        <div className="flex-1">
          <label className="block text-sm font-medium text-gray-700 mb-1">Select Prospect</label>
          {prospects.isLoading ? (
            <p className="text-sm text-gray-400 py-2">Loading...</p>
          ) : (
            <select
              value={selectedId ?? ''}
              onChange={(e) => setSelectedId(e.target.value ? Number(e.target.value) : null)}
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500"
            >
              <option value="">Choose a prospect...</option>
              {(prospects.data ?? []).map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name} ({p.platform}) — {p.email ?? 'No email'}
                </option>
              ))}
            </select>
          )}
        </div>
      </div>

      {previewUrl ? (
        <div className="bg-white border border-gray-200 rounded-xl shadow-sm overflow-hidden">
          <iframe
            src={previewUrl}
            className="w-full border-0"
            style={{ height: '3200px' }}
            title="Store Preview"
          />
        </div>
      ) : selectedId ? (
        <div className="bg-white border border-gray-200 rounded-xl p-8 text-center">
          <p className="text-gray-400">
            No preview available — prospect may not have a claim token yet.
          </p>
        </div>
      ) : (
        <div className="bg-white border border-gray-200 rounded-xl p-8 text-center">
          <p className="text-gray-400">Select a prospect above to preview their store.</p>
        </div>
      )}
    </div>
  )
}
