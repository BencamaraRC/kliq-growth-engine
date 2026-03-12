import api from './client'

export interface OnboardingProgress {
  prospect_id: number
  password_set: boolean
  store_explored: boolean
  content_reviewed: boolean
  stripe_connected: boolean
  first_share: boolean
  progress_pct: number
  started_at: string | null
  completed_at: string | null
}

export const fetchOnboarding = (prospectId: number) =>
  api.get<OnboardingProgress>(`/onboarding/${prospectId}`).then((r) => r.data)

export const completeOnboardingStep = (prospectId: number, step: string) =>
  api.post<OnboardingProgress>(`/onboarding/${prospectId}/complete-step`, { step }).then((r) => r.data)
