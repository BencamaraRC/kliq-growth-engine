import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  fetchKPISummary,
  fetchEmailStats,
  fetchEmailTimeline,
  fetchRecentClaims,
} from '@/api/analytics'
import { KPICard } from '@/components/ui/KPICard'
import { DataTable } from '@/components/ui/DataTable'
import { LoadingSpinner } from '@/components/ui/LoadingSpinner'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts'
import { CHART_COLORS } from '@/lib/constants'
import type { RecentClaimItem } from '@/types/analytics'

export function CampaignsPage() {
  const [days, setDays] = useState(30)

  const kpi = useQuery({ queryKey: ['kpi-summary'], queryFn: fetchKPISummary })
  const emailStats = useQuery({ queryKey: ['email-stats'], queryFn: fetchEmailStats })
  const timeline = useQuery({
    queryKey: ['email-timeline', days],
    queryFn: () => fetchEmailTimeline(days),
  })
  const claims = useQuery({
    queryKey: ['recent-claims'],
    queryFn: () => fetchRecentClaims(20),
  })

  if (kpi.isLoading) return <LoadingSpinner />

  const k = kpi.data

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-bold text-gray-900 tracking-tight">Campaigns</h1>

      {/* KPIs */}
      <div className="grid grid-cols-4 gap-4">
        <KPICard label="Emails Sent" value={k?.emails_sent ?? 0} />
        <KPICard label="Open Rate" value={`${k?.open_rate ?? 0}%`} />
        <KPICard label="Claimed" value={k?.claimed ?? 0} />
        <KPICard label="Claim Rate" value={`${k?.claim_rate ?? 0}%`} />
      </div>

      {/* Email Performance by Step */}
      {emailStats.data?.steps && (
        <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm">
          <h3 className="text-sm font-semibold text-gray-900 mb-4">Email Performance by Step</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={emailStats.data.steps}>
              <XAxis dataKey="step" tick={{ fontSize: 12, fill: '#667085' }} />
              <YAxis tick={{ fontSize: 12, fill: '#667085' }} />
              <Tooltip
                contentStyle={{ borderRadius: 8, border: '1px solid #EAECF0', fontSize: 13 }}
              />
              <Legend />
              <Bar dataKey="sent" name="Sent" fill={CHART_COLORS[0]} radius={[4, 4, 0, 0]} />
              <Bar dataKey="opened" name="Opened" fill={CHART_COLORS[1]} radius={[4, 4, 0, 0]} />
              <Bar dataKey="clicked" name="Clicked" fill={CHART_COLORS[2]} radius={[4, 4, 0, 0]} />
              <Bar dataKey="bounced" name="Bounced" fill={CHART_COLORS[5]} radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>

          {/* Step stats table */}
          <div className="mt-4 overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-2 px-3 text-xs font-medium text-gray-500">Step</th>
                  <th className="text-right py-2 px-3 text-xs font-medium text-gray-500">Sent</th>
                  <th className="text-right py-2 px-3 text-xs font-medium text-gray-500">Opened</th>
                  <th className="text-right py-2 px-3 text-xs font-medium text-gray-500">Clicked</th>
                  <th className="text-right py-2 px-3 text-xs font-medium text-gray-500">Bounced</th>
                  <th className="text-right py-2 px-3 text-xs font-medium text-gray-500">Open Rate</th>
                  <th className="text-right py-2 px-3 text-xs font-medium text-gray-500">Click Rate</th>
                </tr>
              </thead>
              <tbody>
                {emailStats.data.steps.map((s) => (
                  <tr key={s.step_num} className="border-b border-gray-100">
                    <td className="py-2 px-3 font-medium">{s.step}</td>
                    <td className="py-2 px-3 text-right">{s.sent}</td>
                    <td className="py-2 px-3 text-right">{s.opened}</td>
                    <td className="py-2 px-3 text-right">{s.clicked}</td>
                    <td className="py-2 px-3 text-right">{s.bounced}</td>
                    <td className="py-2 px-3 text-right">{s.open_rate}%</td>
                    <td className="py-2 px-3 text-right">{s.click_rate}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Conversion Funnel */}
      {emailStats.data?.steps && (() => {
        const totals = emailStats.data.steps.reduce(
          (acc, s) => ({
            sent: acc.sent + s.sent,
            opened: acc.opened + s.opened,
            clicked: acc.clicked + s.clicked,
          }),
          { sent: 0, opened: 0, clicked: 0 }
        )
        const funnelData = [
          { stage: 'Sent', count: totals.sent },
          { stage: 'Opened', count: totals.opened },
          { stage: 'Clicked', count: totals.clicked },
          { stage: 'Claimed', count: k?.claimed ?? 0 },
        ]
        return (
          <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm">
            <h3 className="text-sm font-semibold text-gray-900 mb-4">Conversion Funnel</h3>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={funnelData} layout="vertical" margin={{ left: 10, right: 20 }}>
                <XAxis type="number" tick={{ fontSize: 12, fill: '#667085' }} />
                <YAxis type="category" dataKey="stage" width={80} tick={{ fontSize: 12, fill: '#667085' }} />
                <Tooltip contentStyle={{ borderRadius: 8, border: '1px solid #EAECF0', fontSize: 13 }} />
                <Bar dataKey="count" fill={CHART_COLORS[0]} radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )
      })()}

      {/* Email Timeline */}
      <div>
        <div className="flex items-center gap-3 mb-4">
          <h3 className="text-sm font-semibold text-gray-900">Email Send Timeline</h3>
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
        {timeline.data && timeline.data.length > 0 && (
          <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm">
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={timeline.data}>
                <XAxis
                  dataKey="date"
                  tick={{ fontSize: 11, fill: '#667085' }}
                  tickFormatter={(v) =>
                    new Date(v).toLocaleDateString('en-GB', { day: 'numeric', month: 'short' })
                  }
                />
                <YAxis tick={{ fontSize: 11, fill: '#667085' }} />
                <Tooltip contentStyle={{ borderRadius: 8, border: '1px solid #EAECF0', fontSize: 13 }} />
                <Bar dataKey="count" fill={CHART_COLORS[1]} radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      {/* Recent Claims */}
      {claims.data && claims.data.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold text-gray-900 mb-4">Recent Claims</h3>
          <DataTable<RecentClaimItem & Record<string, unknown>>
            columns={[
              { key: 'name', header: 'Name' },
              { key: 'email', header: 'Email' },
              { key: 'platform', header: 'Platform' },
              {
                key: 'store_url',
                header: 'Store',
                render: (row) =>
                  row.store_url ? (
                    <a href={row.store_url} target="_blank" rel="noopener" className="text-teal-700 hover:underline text-xs">
                      View Store
                    </a>
                  ) : '-',
              },
              {
                key: 'claimed_at',
                header: 'Claimed',
                render: (row) =>
                  row.claimed_at ? new Date(row.claimed_at).toLocaleDateString() : '',
              },
            ]}
            data={claims.data as (RecentClaimItem & Record<string, unknown>)[]}
          />
        </div>
      )}
    </div>
  )
}
