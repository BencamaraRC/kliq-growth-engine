import api from './client'

export const triggerDiscover = (params?: Record<string, unknown>) =>
  api.post('/pipeline/discover', params).then((r) => r.data)

export const triggerScrape = (prospectId: number) =>
  api.post('/pipeline/scrape', { prospect_id: prospectId }).then((r) => r.data)

export const triggerFullPipeline = (prospectId: number) =>
  api.post(`/pipeline/run/${prospectId}`).then((r) => r.data)

export const triggerBatchPipeline = (status: string) =>
  api.post('/pipeline/batch', { status }).then((r) => r.data)

export const getTaskStatus = (taskId: string) =>
  api.get(`/pipeline/status/${taskId}`).then((r) => r.data)
