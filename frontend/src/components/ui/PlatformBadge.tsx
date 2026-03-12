import { PLATFORM_COLORS } from '@/lib/constants'

export function PlatformBadge({ platform }: { platform: string }) {
  const key = platform?.toUpperCase() ?? ''
  const colors = PLATFORM_COLORS[key] ?? { text: '#4D5761', bg: '#F3F4F6' }

  return (
    <span
      className="inline-block px-2.5 py-0.5 rounded-full text-xs font-medium whitespace-nowrap"
      style={{ color: colors.text, backgroundColor: colors.bg }}
    >
      {platform}
    </span>
  )
}
