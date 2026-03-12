interface KPICardProps {
  label: string
  value: string | number
  sublabel?: string
}

export function KPICard({ label, value, sublabel }: KPICardProps) {
  return (
    <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm">
      <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">{label}</p>
      <p className="text-3xl font-bold text-gray-900 mt-1">{value}</p>
      {sublabel && <p className="text-sm text-gray-400 mt-1">{sublabel}</p>}
    </div>
  )
}
