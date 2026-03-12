import { useQuery } from '@tanstack/react-query'
import {
  fetchKPISummary,
  fetchFunnel,
  fetchPlatforms,
  fetchDailyActivity,
  fetchNiches,
} from '@/api/analytics'
import { KPICard } from '@/components/ui/KPICard'
import { LoadingSpinner } from '@/components/ui/LoadingSpinner'
import { FunnelChart } from '@/components/charts/FunnelChart'
import { PlatformPieChart } from '@/components/charts/PlatformPieChart'
import { DailyActivityChart } from '@/components/charts/DailyActivityChart'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'
import { CHART_COLORS } from '@/lib/constants'

export function DashboardPage() {
  const kpi = useQuery({ queryKey: ['kpi-summary'], queryFn: fetchKPISummary })
  const funnel = useQuery({ queryKey: ['funnel'], queryFn: fetchFunnel })
  const platforms = useQuery({ queryKey: ['platforms'], queryFn: fetchPlatforms })
  const daily = useQuery({ queryKey: ['daily-activity'], queryFn: () => fetchDailyActivity(30) })
  const niches = useQuery({ queryKey: ['niches'], queryFn: fetchNiches })

  if (kpi.isLoading) return <LoadingSpinner />

  const k = kpi.data

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-bold text-gray-900 tracking-tight">Dashboard</h1>

      {/* KPI Cards */}
      <div className="grid grid-cols-5 gap-4">
        <KPICard label="Total Prospects" value={k?.total_prospects ?? 0} />
        <KPICard label="Stores Created" value={k?.stores_created ?? 0} />
        <KPICard label="Emails Sent" value={k?.emails_sent ?? 0} />
        <KPICard label="Claimed" value={k?.claimed ?? 0} />
        <KPICard
          label="Claim Rate"
          value={`${k?.claim_rate ?? 0}%`}
          sublabel={`Open rate: ${k?.open_rate ?? 0}%`}
        />
      </div>

      {/* Charts Row 1 */}
      <div className="grid grid-cols-2 gap-6">
        {funnel.data && <FunnelChart data={funnel.data} />}
        {platforms.data && <PlatformPieChart data={platforms.data} />}
      </div>

      {/* Charts Row 2 */}
      <div className="grid grid-cols-2 gap-6">
        {daily.data && <DailyActivityChart data={daily.data} />}

        {/* Niche Distribution */}
        {niches.data && (
          <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm">
            <h3 className="text-sm font-semibold text-gray-900 mb-4">Top Niches</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart
                data={niches.data.slice(0, 10)}
                layout="vertical"
                margin={{ left: 10, right: 20 }}
              >
                <XAxis type="number" tick={{ fontSize: 12, fill: '#667085' }} />
                <YAxis
                  type="category"
                  dataKey="niche"
                  width={120}
                  tick={{ fontSize: 11, fill: '#667085' }}
                />
                <Tooltip
                  contentStyle={{
                    borderRadius: 8,
                    border: '1px solid #EAECF0',
                    fontSize: 13,
                  }}
                />
                <Bar dataKey="count" fill={CHART_COLORS[1]} radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>
    </div>
  )
}
