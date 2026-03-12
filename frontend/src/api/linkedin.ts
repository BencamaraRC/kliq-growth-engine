import api from './client'
import type { LinkedInStats } from '@/types/linkedin'

export const fetchLinkedInQueue = (params?: {
  status?: string
  search?: string
  limit?: number
}) => api.get('/linkedin/queue', { params }).then((r) => r.data)

export const fetchLinkedInStats = () =>
  api.get<LinkedInStats>('/linkedin/stats').then((r) => r.data)

export const copyConnectionNote = (prospectId: number) =>
  api.post<{
    prospect_id: number
    prospect_name: string
    connection_note: string
    linkedin_url: string
    status: string
  }>(`/linkedin/${prospectId}/copy`).then((r) => r.data)

export const updateLinkedInStatus = (prospectId: number, status: string) =>
  api.patch(`/linkedin/${prospectId}/status`, { status }).then((r) => r.data)

export const updateLinkedInUrl = (prospectId: number, linkedinUrl: string) =>
  api.patch(`/linkedin/${prospectId}/url`, { linkedin_url: linkedinUrl }).then((r) => r.data)
