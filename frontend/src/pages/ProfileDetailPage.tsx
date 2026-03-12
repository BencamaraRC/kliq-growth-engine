import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { fetchProspectDetail, rejectProspect } from '@/api/prospects'
import { StatusBadge } from '@/components/ui/StatusBadge'
import { PlatformBadge } from '@/components/ui/PlatformBadge'
import { LoadingSpinner } from '@/components/ui/LoadingSpinner'
import { useState } from 'react'

const STEP_NAMES: Record<number, string> = {
  1: 'Store Ready',
  2: 'Reminder 1',
  3: 'Reminder 2',
  4: 'Claimed Confirmation',
}

export function ProfileDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [activeTab, setActiveTab] = useState('scraped')

  const { data: p, isLoading } = useQuery({
    queryKey: ['prospect-detail', id],
    queryFn: () => fetchProspectDetail(Number(id)),
    enabled: !!id,
  })

  const rejectMut = useMutation({
    mutationFn: () => rejectProspect(Number(id)),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['prospect-detail', id] })
    },
  })

  if (!id) {
    return (
      <div className="space-y-4">
        <h1 className="text-2xl font-bold text-gray-900 tracking-tight">Profile Detail</h1>
        <p className="text-gray-500">Select a prospect from the Profiles page, or navigate to /profile/:id</p>
      </div>
    )
  }

  if (isLoading) return <LoadingSpinner />
  if (!p) return <p className="text-gray-500">Prospect not found.</p>

  const tabs = [
    { key: 'scraped', label: 'Scraped Content', count: p.scraped_content.length },
    { key: 'generated', label: 'AI Content', count: p.generated_content.length },
    { key: 'pricing', label: 'Pricing', count: p.scraped_pricing.length },
    { key: 'profiles', label: 'Platforms', count: p.platform_profiles.length },
    { key: 'emails', label: 'Emails', count: p.campaign_events.length },
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <button
          onClick={() => navigate(-1)}
          className="text-sm text-gray-500 hover:text-gray-700"
        >
          &larr; Back
        </button>
      </div>

      {/* Header */}
      <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
        <div className="flex gap-6">
          {/* Avatar */}
          <div className="flex-shrink-0">
            {p.profile_image_url ? (
              <img
                src={p.profile_image_url}
                alt={p.name}
                className="h-20 w-20 rounded-full object-cover"
              />
            ) : (
              <div className="h-20 w-20 rounded-full bg-gray-200 flex items-center justify-center text-2xl font-bold text-gray-400">
                {p.name?.[0]}
              </div>
            )}
          </div>

          {/* Info */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-3 mb-2">
              <h2 className="text-xl font-bold text-gray-900">{p.name}</h2>
              <StatusBadge status={p.status} />
              <PlatformBadge platform={p.primary_platform} />
            </div>
            {p.email && <p className="text-sm text-gray-500">{p.email}</p>}
            {p.bio && (
              <p className="text-sm text-gray-600 mt-2 line-clamp-3">{p.bio}</p>
            )}
            {p.niche_tags?.length ? (
              <div className="flex gap-1 flex-wrap mt-3">
                {p.niche_tags.map((t) => (
                  <span
                    key={t}
                    className="px-2 py-0.5 text-xs font-medium text-teal-900 bg-teal-50 border border-teal-100 rounded-full"
                  >
                    {t}
                  </span>
                ))}
              </div>
            ) : null}
          </div>

          {/* Metrics */}
          <div className="flex-shrink-0 grid grid-cols-2 gap-4 text-center">
            <div>
              <p className="text-2xl font-bold text-gray-900">{p.follower_count.toLocaleString()}</p>
              <p className="text-xs text-gray-500">Followers</p>
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900">{p.subscriber_count.toLocaleString()}</p>
              <p className="text-xs text-gray-500">Subscribers</p>
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900">{p.content_count}</p>
              <p className="text-xs text-gray-500">Content</p>
            </div>
            <div>
              {p.brand_colors?.length ? (
                <div className="flex gap-1 justify-center">
                  {p.brand_colors.slice(0, 4).map((c, i) => (
                    <span
                      key={i}
                      className="w-6 h-6 rounded inline-block border border-gray-200"
                      style={{ backgroundColor: c.startsWith('#') ? c : `#${c}` }}
                      title={c}
                    />
                  ))}
                </div>
              ) : (
                <p className="text-sm text-gray-400">-</p>
              )}
              <p className="text-xs text-gray-500 mt-1">Colors</p>
            </div>
          </div>
        </div>

        {/* Links row */}
        <div className="flex gap-4 mt-4 text-sm">
          {p.primary_platform_url && (
            <a href={p.primary_platform_url} target="_blank" rel="noopener" className="text-teal-700 hover:underline">
              Platform Profile
            </a>
          )}
          {p.website_url && (
            <a href={p.website_url} target="_blank" rel="noopener" className="text-teal-700 hover:underline">
              Website
            </a>
          )}
          {p.linkedin_url && (
            <a href={p.linkedin_url} target="_blank" rel="noopener" className="text-teal-700 hover:underline">
              LinkedIn
            </a>
          )}
          {p.kliq_store_url && (
            <a href={p.kliq_store_url} target="_blank" rel="noopener" className="text-teal-700 hover:underline">
              KLIQ Store
            </a>
          )}
          {p.status !== 'REJECTED' && (
            <button
              onClick={() => {
                if (confirm('Reject this prospect?')) rejectMut.mutate()
              }}
              className="text-red-600 hover:underline ml-auto"
            >
              Reject
            </button>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <div className="flex gap-0">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`px-5 py-3 text-sm font-medium border-b-2 transition-colors ${
                activeTab === tab.key
                  ? 'border-kliq-green text-kliq-green'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              {tab.label} ({tab.count})
            </button>
          ))}
        </div>
      </div>

      {/* Tab Content */}
      <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
        {activeTab === 'scraped' && (
          <div className="space-y-4">
            {p.scraped_content.length === 0 ? (
              <p className="text-gray-400">No scraped content</p>
            ) : (
              p.scraped_content.slice(0, 20).map((item, i) => (
                <div key={i} className="border border-gray-100 rounded-lg p-4">
                  <div className="flex items-start justify-between">
                    <div>
                      <span className="text-xs font-medium text-gray-400 uppercase">
                        {String(item.content_type ?? '')}
                      </span>
                      <h4 className="font-medium text-gray-900 mt-1">
                        {String(item.title ?? 'Untitled')}
                      </h4>
                    </div>
                    {item.view_count ? (
                      <span className="text-sm text-gray-500">
                        {Number(item.view_count).toLocaleString()} views
                      </span>
                    ) : null}
                  </div>
                  {item.description && (
                    <p className="text-sm text-gray-600 mt-2 line-clamp-2">
                      {String(item.description)}
                    </p>
                  )}
                  {item.url && (
                    <a
                      href={String(item.url)}
                      target="_blank"
                      rel="noopener"
                      className="text-xs text-teal-700 hover:underline mt-2 inline-block"
                    >
                      View source
                    </a>
                  )}
                </div>
              ))
            )}
          </div>
        )}

        {activeTab === 'generated' && (
          <div className="space-y-4">
            {p.generated_content.length === 0 ? (
              <p className="text-gray-400">No AI-generated content</p>
            ) : (
              p.generated_content.map((item, i) => (
                <div key={i} className="border border-gray-100 rounded-lg p-4">
                  <span className="text-xs font-medium text-gray-400 uppercase">
                    {String(item.content_type ?? '')}
                  </span>
                  {item.title && (
                    <h4 className="font-medium text-gray-900 mt-1">{String(item.title)}</h4>
                  )}
                  {item.body && (
                    <p className="text-sm text-gray-600 mt-2 whitespace-pre-wrap line-clamp-6">
                      {String(item.body)}
                    </p>
                  )}
                </div>
              ))
            )}
          </div>
        )}

        {activeTab === 'pricing' && (
          <div className="space-y-3">
            {p.scraped_pricing.length === 0 ? (
              <p className="text-gray-400">No pricing data</p>
            ) : (
              p.scraped_pricing.map((item, i) => (
                <div key={i} className="border border-gray-100 rounded-lg p-4 flex items-center justify-between">
                  <div>
                    <h4 className="font-medium text-gray-900">{String(item.tier_name ?? '')}</h4>
                    {item.description && (
                      <p className="text-sm text-gray-500 mt-1">{String(item.description)}</p>
                    )}
                    {item.member_count ? (
                      <p className="text-xs text-gray-400 mt-1">
                        {Number(item.member_count).toLocaleString()} members
                      </p>
                    ) : null}
                  </div>
                  <div className="text-right">
                    <p className="text-lg font-bold text-gray-900">
                      {String(item.currency ?? '$')}{Number(item.price_amount ?? 0).toFixed(2)}
                    </p>
                    <p className="text-xs text-gray-400">/{String(item.interval ?? 'month')}</p>
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {activeTab === 'profiles' && (
          <div className="space-y-3">
            {p.platform_profiles.length === 0 ? (
              <p className="text-gray-400">No platform profiles</p>
            ) : (
              p.platform_profiles.map((item, i) => (
                <div key={i} className="border border-gray-100 rounded-lg p-4">
                  <div className="flex items-center gap-3">
                    <PlatformBadge platform={String(item.platform ?? '')} />
                    <span className="text-sm text-gray-600">{String(item.platform_id ?? '')}</span>
                    {item.platform_url && (
                      <a
                        href={String(item.platform_url)}
                        target="_blank"
                        rel="noopener"
                        className="text-xs text-teal-700 hover:underline ml-auto"
                      >
                        View
                      </a>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {activeTab === 'emails' && (
          <div className="space-y-3">
            {p.campaign_events.length === 0 ? (
              <p className="text-gray-400">No email history</p>
            ) : (
              p.campaign_events.map((item, i) => (
                <div key={i} className="border border-gray-100 rounded-lg p-4 flex items-center justify-between">
                  <div>
                    <span className="text-sm font-medium text-gray-900">
                      {STEP_NAMES[Number(item.step)] ?? `Step ${item.step}`}
                    </span>
                    <p className="text-xs text-gray-400 mt-1">
                      {item.sent_at ? new Date(String(item.sent_at)).toLocaleString() : 'Not sent'}
                    </p>
                  </div>
                  <StatusBadge status={String(item.email_status ?? '')} />
                </div>
              ))
            )}
          </div>
        )}
      </div>
    </div>
  )
}
