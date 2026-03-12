export const COLORS = {
  kliqGreen: '#1C3838',
  kliqGreenHover: '#0E2325',
  tangerine: '#FF9F88',
  lime: '#DEFE9C',
  alpine: '#9CF0FF',
  ivory: '#FFFDF9',
  textPrimary: '#101828',
  textSecondary: '#667085',
  textTertiary: '#9DA4AE',
  border: '#EAECF0',
  positive: '#039855',
  negative: '#D92D20',
  warning: '#F79009',
} as const

export const CHART_COLORS = [
  '#1C3838',
  '#39938F',
  '#FF9F88',
  '#DEFE9C',
  '#9CF0FF',
  '#F79009',
  '#7ECAC3',
]

export const STATUS_COLORS: Record<string, { text: string; bg: string }> = {
  DISCOVERED: { text: '#344054', bg: '#F2F4F7' },
  SCRAPED: { text: '#1C3838', bg: '#E0F7FA' },
  CONTENT_GENERATED: { text: '#B54708', bg: '#FFFAEB' },
  STORE_CREATED: { text: '#1C3838', bg: '#F0FFF4' },
  EMAIL_SENT: { text: '#B42318', bg: '#FFF1ED' },
  CLAIMED: { text: '#039855', bg: '#ECFDF3' },
  REJECTED: { text: '#D92D20', bg: '#FEE4E2' },
}

export const PLATFORM_COLORS: Record<string, { text: string; bg: string }> = {
  YOUTUBE: { text: '#CC0000', bg: '#FEE2E2' },
  SKOOL: { text: '#1D4ED8', bg: '#DBEAFE' },
  PATREON: { text: '#FF424D', bg: '#FFE4E6' },
  WEBSITE: { text: '#4D5761', bg: '#F3F4F6' },
  TIKTOK: { text: '#000000', bg: '#F3F4F6' },
  INSTAGRAM: { text: '#C13584', bg: '#FCE7F3' },
  ONLYFANS: { text: '#00AFF0', bg: '#E0F2FE' },
  KAJABI: { text: '#6D28D9', bg: '#EDE9FE' },
  STAN: { text: '#F59E0B', bg: '#FEF3C7' },
}

export const STATUS_ORDER = [
  'DISCOVERED',
  'SCRAPED',
  'CONTENT_GENERATED',
  'STORE_CREATED',
  'EMAIL_SENT',
  'CLAIMED',
  'REJECTED',
]
