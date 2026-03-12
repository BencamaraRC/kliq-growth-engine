import api from './client'

export interface ClaimValidation {
  prospect_id: number
  name: string
  email: string
  store_url: string | null
  profile_image_url: string | null
}

export interface ClaimResult {
  access_token: string
  store_url: string
  application_id: number
}

export const validateClaim = (token: string) =>
  api.get<ClaimValidation>(`/claim/validate?token=${token}`).then((r) => r.data)

export const submitClaim = (token: string, password: string) =>
  api.post<ClaimResult>('/claim/submit', { token, password }).then((r) => r.data)
