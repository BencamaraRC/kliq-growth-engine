import { STATUS_COLORS } from '@/lib/constants'

export function StatusBadge({ status }: { status: string }) {
  const key = status?.toUpperCase() ?? ''
  const colors = STATUS_COLORS[key] ?? { text: '#344054', bg: '#F2F4F7' }
  const label = status?.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase()) ?? ''

  return (
    <span
      className="inline-block px-2.5 py-0.5 rounded-full text-xs font-medium whitespace-nowrap"
      style={{ color: colors.text, backgroundColor: colors.bg }}
    >
      {label}
    </span>
  )
}
