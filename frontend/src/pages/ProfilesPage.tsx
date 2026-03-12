import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { fetchProspects, fetchFilterPlatforms, fetchFilterNiches } from '@/api/prospects'
import { DataTable } from '@/components/ui/DataTable'
import { StatusBadge } from '@/components/ui/StatusBadge'
import { PlatformBadge } from '@/components/ui/PlatformBadge'
import { LoadingSpinner } from '@/components/ui/LoadingSpinner'
import { STATUS_ORDER } from '@/lib/constants'
import type { Prospect } from '@/types/prospect'

const PAGE_SIZE = 50

export function ProfilesPage() {
  const navigate = useNavigate()
  const [search, setSearch] = useState('')
  const [status, setStatus] = useState('')
  const [platform, setPlatform] = useState('')
  const [niche, setNiche] = useState('')
  const [page, setPage] = useState(0)

  const filters = {
    status: status || undefined,
    platform: platform || undefined,
    niche: niche || undefined,
    search: search || undefined,
    limit: PAGE_SIZE,
    offset: page * PAGE_SIZE,
  }

  const prospects = useQuery({
    queryKey: ['prospects', filters],
    queryFn: () => fetchProspects(filters),
  })
  const platformOptions = useQuery({
    queryKey: ['filter-platforms'],
    queryFn: fetchFilterPlatforms,
  })
  const nicheOptions = useQuery({
    queryKey: ['filter-niches'],
    queryFn: fetchFilterNiches,
  })

  const totalPages = Math.ceil((prospects.data?.total ?? 0) / PAGE_SIZE)

  const exportCSV = () => {
    if (!prospects.data?.prospects.length) return
    const headers = ['id', 'name', 'email', 'status', 'primary_platform', 'follower_count', 'subscriber_count']
    const rows = prospects.data.prospects.map((p) =>
      headers.map((h) => String(p[h] ?? '')).join(',')
    )
    const csv = [headers.join(','), ...rows].join('\n')
    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'prospects.csv'
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900 tracking-tight">Profiles</h1>
        <button
          onClick={exportCSV}
          className="px-4 py-2 text-sm font-semibold border border-gray-300 rounded-lg text-kliq-green hover:bg-kliq-green-light transition-colors"
        >
          Export CSV
        </button>
      </div>

      {/* Filters */}
      <div className="flex gap-3 flex-wrap">
        <input
          type="text"
          placeholder="Search name or email..."
          value={search}
          onChange={(e) => { setSearch(e.target.value); setPage(0) }}
          className="px-3 py-2 text-sm border border-gray-300 rounded-lg w-64 focus:ring-2 focus:ring-teal-500 focus:border-teal-500"
        />
        <select
          value={status}
          onChange={(e) => { setStatus(e.target.value); setPage(0) }}
          className="px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500"
        >
          <option value="">All Statuses</option>
          {STATUS_ORDER.map((s) => (
            <option key={s} value={s}>{s.replace(/_/g, ' ')}</option>
          ))}
        </select>
        <select
          value={platform}
          onChange={(e) => { setPlatform(e.target.value); setPage(0) }}
          className="px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500"
        >
          <option value="">All Platforms</option>
          {(platformOptions.data ?? []).map((p) => (
            <option key={p} value={p}>{p}</option>
          ))}
        </select>
        <select
          value={niche}
          onChange={(e) => { setNiche(e.target.value); setPage(0) }}
          className="px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500"
        >
          <option value="">All Niches</option>
          {(nicheOptions.data ?? []).map((n) => (
            <option key={n} value={n}>{n}</option>
          ))}
        </select>
      </div>

      {prospects.isLoading ? (
        <LoadingSpinner />
      ) : (
        <>
          <p className="text-sm text-gray-500">
            {prospects.data?.total ?? 0} prospects found
          </p>
          <DataTable<Prospect & Record<string, unknown>>
            columns={[
              {
                key: 'avatar',
                header: '',
                render: (row) =>
                  row.profile_image_url ? (
                    <img
                      src={row.profile_image_url}
                      alt=""
                      className="h-8 w-8 rounded-full object-cover"
                    />
                  ) : (
                    <div className="h-8 w-8 rounded-full bg-gray-200" />
                  ),
                className: 'w-10',
              },
              { key: 'name', header: 'Name' },
              { key: 'email', header: 'Email' },
              {
                key: 'status',
                header: 'Status',
                render: (row) => <StatusBadge status={row.status} />,
              },
              {
                key: 'primary_platform',
                header: 'Platform',
                render: (row) => <PlatformBadge platform={row.primary_platform} />,
              },
              { key: 'follower_count', header: 'Followers' },
              {
                key: 'niche_tags',
                header: 'Niches',
                render: (row) =>
                  row.niche_tags?.length ? (
                    <div className="flex gap-1 flex-wrap">
                      {row.niche_tags.slice(0, 3).map((t) => (
                        <span
                          key={t}
                          className="inline-block px-2 py-0.5 text-xs font-medium text-teal-900 bg-teal-50 border border-teal-100 rounded-full"
                        >
                          {t}
                        </span>
                      ))}
                      {row.niche_tags.length > 3 && (
                        <span className="text-xs text-gray-400">+{row.niche_tags.length - 3}</span>
                      )}
                    </div>
                  ) : (
                    <span className="text-xs text-gray-400">-</span>
                  ),
              },
            ]}
            data={(prospects.data?.prospects ?? []) as (Prospect & Record<string, unknown>)[]}
            onRowClick={(row) => navigate(`/profile/${row.id}`)}
            emptyMessage="No prospects match your filters"
          />

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-2">
              <button
                disabled={page === 0}
                onClick={() => setPage(page - 1)}
                className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg disabled:opacity-40"
              >
                Previous
              </button>
              <span className="text-sm text-gray-500">
                Page {page + 1} of {totalPages}
              </span>
              <button
                disabled={page >= totalPages - 1}
                onClick={() => setPage(page + 1)}
                className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg disabled:opacity-40"
              >
                Next
              </button>
            </div>
          )}
        </>
      )}
    </div>
  )
}
