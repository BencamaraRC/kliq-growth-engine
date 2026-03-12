import api from './client'
import type {
  KPISummary,
  FunnelItem,
  PlatformItem,
  NicheItem,
  DailyActivityItem,
  StatusCountItem,
  EmailStepStats,
  EmailTimelineItem,
  RecentClaimItem,
  RecentActivityItem,
} from '@/types/analytics'

export const fetchKPISummary = () =>
  api.get<KPISummary>('/analytics/kpi-summary').then((r) => r.data)

export const fetchFunnel = () =>
  api.get<FunnelItem[]>('/analytics/funnel').then((r) => r.data)

export const fetchPlatforms = () =>
  api.get<PlatformItem[]>('/analytics/platforms').then((r) => r.data)

export const fetchNiches = () =>
  api.get<NicheItem[]>('/analytics/niches').then((r) => r.data)

export const fetchDailyActivity = (days = 30) =>
  api.get<DailyActivityItem[]>('/analytics/daily-activity', { params: { days } }).then((r) => r.data)

export const fetchStatusCounts = () =>
  api.get<StatusCountItem[]>('/analytics/status-counts').then((r) => r.data)

export const fetchEmailStats = () =>
  api.get<{ steps: EmailStepStats[] }>('/analytics/email-stats').then((r) => r.data)

export const fetchEmailTimeline = (days = 30) =>
  api.get<EmailTimelineItem[]>('/analytics/email-timeline', { params: { days } }).then((r) => r.data)

export const fetchRecentClaims = (limit = 20) =>
  api.get<RecentClaimItem[]>('/analytics/recent-claims', { params: { limit } }).then((r) => r.data)

export const fetchRecentActivity = (limit = 10) =>
  api.get<RecentActivityItem[]>('/analytics/recent-activity', { params: { limit } }).then((r) => r.data)
