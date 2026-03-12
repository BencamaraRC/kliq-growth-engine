export interface Prospect {
  [key: string]: unknown
  id: number
  name: string
  email: string | null
  status: string
  primary_platform: string
  primary_platform_id: string
  profile_image_url: string | null
  website_url: string | null
  social_links: Record<string, string> | null
  primary_platform_url: string | null
  follower_count: number
  subscriber_count: number
  niche_tags: string[] | null
  kliq_application_id: number | null
  kliq_store_url: string | null
  discovered_at: string | null
  claimed_at: string | null
}

export interface ProspectListResponse {
  total: number
  prospects: Prospect[]
}

export interface ProspectDetail extends Prospect {
  first_name: string | null
  last_name: string | null
  bio: string | null
  banner_image_url: string | null
  linkedin_url: string | null
  linkedin_found: boolean
  location: string | null
  content_count: number
  brand_colors: string[] | null
  claim_token: string | null
  store_created_at: string | null
  created_at: string | null
  updated_at: string | null
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  platform_profiles: Record<string, any>[]
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  scraped_content: Record<string, any>[]
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  generated_content: Record<string, any>[]
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  campaign_events: Record<string, any>[]
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  scraped_pricing: Record<string, any>[]
}

export interface OperationsProspect {
  id: number
  name: string
  email: string | null
  status: string
  platform: string
  followers: number
  claim_token: string | null
  store_url: string | null
  discovered: string | null
}
