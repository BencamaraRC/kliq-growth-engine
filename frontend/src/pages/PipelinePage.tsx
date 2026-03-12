import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { fetchFunnel, fetchPlatforms, fetchDailyActivity } from '@/api/analytics'
import { fetchProspects } from '@/api/prospects'
import { FunnelChart } from '@/components/charts/FunnelChart'
import { PlatformPieChart } from '@/components/charts/PlatformPieChart'
import { DailyActivityChart } from '@/components/charts/DailyActivityChart'
import { DataTable } from '@/components/ui/DataTable'
import { StatusBadge } from '@/components/ui/StatusBadge'
import { PlatformBadge } from '@/components/ui/PlatformBadge'
import { LoadingSpinner } from '@/components/ui/LoadingSpinner'
import { STATUS_ORDER } from '@/lib/constants'
import type { Prospect } from '@/types/prospect'

export function PipelinePage() {
  const [statusFilter, setStatusFilter] = useState('')
  const [days, setDays] = useState(30)

  const funnel = useQuery({ queryKey: ['funnel'], queryFn: fetchFunnel })
  const platforms = useQuery({ queryKey: ['platforms'], queryFn: fetchPlatforms })
  const daily = useQuery({
    queryKey: ['daily-activity', days],
    queryFn: () => fetchDailyActivity(days),
  })
  const prospects = useQuery({
    queryKey: ['pipeline-prospects', statusFilter],
    queryFn: () =>
      fetchProspects({
        status: statusFilter || undefined,
        limit: 50,
      }),
  })

  if (funnel.isLoading) return <LoadingSpinner />

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-bold text-gray-900 tracking-tight">Pipeline</h1>

      <div className="grid grid-cols-2 gap-6">
        {funnel.data && <FunnelChart data={funnel.data} />}
        {platforms.data && <PlatformPieChart data={platforms.data} />}
      </div>

      <div className="flex items-center gap-3">
        <label className="text-sm font-medium text-gray-600">Time range:</label>
        {[7, 14, 30, 60, 90].map((d) => (
          <button
            key={d}
            onClick={() => setDays(d)}
            className={`px-3 py-1 text-xs rounded-lg font-medium transition-colors ${
              days === d
                ? 'bg-kliq-green text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            {d}d
          </button>
        ))}
      </div>

      {daily.data && <DailyActivityChart data={daily.data} />}

      <div>
        <div className="flex items-center gap-3 mb-4">
          <h3 className="text-sm font-semibold text-gray-900">Recent Prospects</h3>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500"
          >
            <option value="">All Statuses</option>
            {STATUS_ORDER.map((s) => (
              <option key={s} value={s}>
                {s.replace(/_/g, ' ')}
              </option>
            ))}
          </select>
        </div>

        <DataTable<Prospect & Record<string, unknown>>
          columns={[
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
              key: 'discovered_at',
              header: 'Discovered',
              render: (row) =>
                row.discovered_at
                  ? new Date(row.discovered_at).toLocaleDateString()
                  : '',
            },
          ]}
          data={(prospects.data?.prospects ?? []) as (Prospect & Record<string, unknown>)[]}
          emptyMessage="No prospects found"
        />
      </div>
    </div>
  )
}
