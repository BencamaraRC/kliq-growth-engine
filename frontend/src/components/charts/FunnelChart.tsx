import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import { CHART_COLORS } from '@/lib/constants'
import type { FunnelItem } from '@/types/analytics'

export function FunnelChart({ data }: { data: FunnelItem[] }) {
  const formatted = data.map((d) => ({
    ...d,
    label: d.status.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase()),
  }))

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm">
      <h3 className="text-sm font-semibold text-gray-900 mb-4">Pipeline Funnel</h3>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={formatted} layout="vertical" margin={{ left: 20, right: 20 }}>
          <XAxis type="number" tick={{ fontSize: 12, fill: '#667085' }} />
          <YAxis
            type="category"
            dataKey="label"
            width={130}
            tick={{ fontSize: 12, fill: '#667085' }}
          />
          <Tooltip
            contentStyle={{
              borderRadius: 8,
              border: '1px solid #EAECF0',
              fontSize: 13,
            }}
          />
          <Bar dataKey="count" radius={[0, 4, 4, 0]}>
            {formatted.map((_, i) => (
              <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
