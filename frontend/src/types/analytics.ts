export interface KPISummary {
  total_prospects: number
  discovered: number
  scraped: number
  content_generated: number
  stores_created: number
  emails_sent: number
  claimed: number
  rejected: number
  open_rate: number
  claim_rate: number
}

export interface FunnelItem {
  status: string
  count: number
}

export interface PlatformItem {
  platform: string
  count: number
}

export interface NicheItem {
  niche: string
  count: number
}

export interface DailyActivityItem {
  date: string
  discovered: number
  stores_created: number
  claimed: number
}

export interface StatusCountItem {
  status: string
  count: number
}

export interface EmailStepStats {
  step: string
  step_num: number
  total: number
  sent: number
  opened: number
  clicked: number
  bounced: number
  unsubscribed: number
  open_rate: number
  click_rate: number
}

export interface EmailTimelineItem {
  date: string
  step: number
  count: number
}

export interface RecentClaimItem {
  id: number
  name: string
  email: string | null
  platform: string
  app_id: number | null
  store_url: string | null
  claimed_at: string | null
}

export interface RecentActivityItem {
  id: number
  name: string
  status: string
  platform: string
  updated_at: string | null
}
