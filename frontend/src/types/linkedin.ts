export interface LinkedInQueueItem {
  id: number
  name: string
  email: string | null
  niche: string
  linkedin_url: string | null
  follower_count: number
  status: string
  connection_note: string | null
  sent_at: string | null
  accepted_at: string | null
}

export interface LinkedInStats {
  total_with_linkedin: number
  queued: number
  copied: number
  sent: number
  accepted: number
  declined: number
  no_response: number
  accept_rate: number
}
