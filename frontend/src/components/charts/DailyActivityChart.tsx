import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'
import { CHART_COLORS } from '@/lib/constants'
import type { DailyActivityItem } from '@/types/analytics'

export function DailyActivityChart({ data }: { data: DailyActivityItem[] }) {
  return (
    <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm">
      <h3 className="text-sm font-semibold text-gray-900 mb-4">Daily Activity (30 days)</h3>
      <ResponsiveContainer width="100%" height={300}>
        <AreaChart data={data} margin={{ left: 0, right: 0 }}>
          <XAxis
            dataKey="date"
            tick={{ fontSize: 11, fill: '#667085' }}
            tickFormatter={(v) => new Date(v).toLocaleDateString('en-GB', { day: 'numeric', month: 'short' })}
          />
          <YAxis tick={{ fontSize: 11, fill: '#667085' }} />
          <Tooltip
            contentStyle={{ borderRadius: 8, border: '1px solid #EAECF0', fontSize: 13 }}
            labelFormatter={(v) => new Date(v).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })}
          />
          <Area
            type="monotone"
            dataKey="discovered"
            name="Discovered"
            stackId="1"
            stroke={CHART_COLORS[0]}
            fill={CHART_COLORS[0]}
            fillOpacity={0.3}
          />
          <Area
            type="monotone"
            dataKey="stores_created"
            name="Stores Created"
            stackId="1"
            stroke={CHART_COLORS[1]}
            fill={CHART_COLORS[1]}
            fillOpacity={0.3}
          />
          <Area
            type="monotone"
            dataKey="claimed"
            name="Claimed"
            stackId="1"
            stroke={CHART_COLORS[2]}
            fill={CHART_COLORS[2]}
            fillOpacity={0.3}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}
