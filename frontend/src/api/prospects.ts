import api from './client'
import type { ProspectListResponse, ProspectDetail, OperationsProspect } from '@/types/prospect'

interface ProspectFilters {
  status?: string
  platform?: string
  niche?: string
  search?: string
  limit?: number
  offset?: number
}

export const fetchProspects = (filters: ProspectFilters = {}) =>
  api.get<ProspectListResponse>('/prospects/', { params: filters }).then((r) => r.data)

export const fetchProspectDetail = (id: number) =>
  api.get<ProspectDetail>(`/prospects/${id}/detail`).then((r) => r.data)

export const fetchFilterPlatforms = () =>
  api.get<string[]>('/prospects/filters/platforms').then((r) => r.data)

export const fetchFilterNiches = () =>
  api.get<string[]>('/prospects/filters/niches').then((r) => r.data)

export const rejectProspect = (id: number) =>
  api.patch(`/prospects/${id}/reject`).then((r) => r.data)

export const fetchOperationsProspects = (filters: {
  status?: string
  platform?: string
  search?: string
  limit?: number
}) =>
  api.get<OperationsProspect[]>('/prospects/operations/list', { params: filters }).then((r) => r.data)
