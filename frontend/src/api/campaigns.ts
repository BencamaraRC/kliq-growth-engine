import api from './client'

export const fetchCampaigns = () =>
  api.get('/campaigns/').then((r) => r.data)

export const createCampaign = (data: { name: string; platform_filter?: string; niche_filter?: string[] }) =>
  api.post('/campaigns/', data).then((r) => r.data)

export const activateCampaign = (id: number) =>
  api.post(`/campaigns/${id}/activate`).then((r) => r.data)

export const pauseCampaign = (id: number) =>
  api.post(`/campaigns/${id}/pause`).then((r) => r.data)
