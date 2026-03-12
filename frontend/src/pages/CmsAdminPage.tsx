import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { fetchProspectDetail, fetchOperationsProspects } from '@/api/prospects'
import { LoadingSpinner } from '@/components/ui/LoadingSpinner'
import { StatusBadge } from '@/components/ui/StatusBadge'

export function CmsAdminPage() {
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [activeTab, setActiveTab] = useState('application')

  const prospects = useQuery({
    queryKey: ['cms-prospects'],
    queryFn: () => fetchOperationsProspects({ status: 'STORE_CREATED', limit: 200 }),
  })

  const detail = useQuery({
    queryKey: ['prospect-detail', selectedId],
    queryFn: () => fetchProspectDetail(selectedId!),
    enabled: !!selectedId,
  })

  const p = detail.data

  const tabs = [
    'application',
    'settings',
    'brand-colors',
    'coach-user',
    'products',
    'pages',
    'features',
  ]

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900 tracking-tight">CMS Admin</h1>

      {/* Prospect Selector */}
      <div className="flex gap-3 items-end">
        <div className="flex-1">
          <label className="block text-sm font-medium text-gray-700 mb-1">Select Prospect</label>
          <select
            value={selectedId ?? ''}
            onChange={(e) => {
              setSelectedId(e.target.value ? Number(e.target.value) : null)
              setActiveTab('application')
            }}
            className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500"
          >
            <option value="">Choose a prospect...</option>
            {(prospects.data ?? []).map((p) => (
              <option key={p.id} value={p.id}>
                {p.name} ({p.platform}) — {p.status}
              </option>
            ))}
          </select>
        </div>
        {p?.kliq_application_id && (
          <a
            href={`https://admin.joinkliq.io/applications/${p.kliq_application_id}`}
            target="_blank"
            rel="noopener"
            className="px-4 py-2 text-sm font-semibold border border-gray-300 rounded-lg text-kliq-green hover:bg-kliq-green-light"
          >
            Open in CMS Admin
          </a>
        )}
      </div>

      {!selectedId ? (
        <div className="bg-white border border-gray-200 rounded-xl p-8 text-center">
          <p className="text-gray-400">Select a prospect to view CMS data mapping.</p>
        </div>
      ) : detail.isLoading ? (
        <LoadingSpinner />
      ) : !p ? (
        <p className="text-gray-500">Prospect not found.</p>
      ) : (
        <>
          {/* Tabs */}
          <div className="border-b border-gray-200">
            <div className="flex gap-0">
              {tabs.map((tab) => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={`px-5 py-3 text-sm font-medium border-b-2 transition-colors capitalize ${
                    activeTab === tab
                      ? 'border-kliq-green text-kliq-green'
                      : 'border-transparent text-gray-500 hover:text-gray-700'
                  }`}
                >
                  {tab.replace(/-/g, ' ')}
                </button>
              ))}
            </div>
          </div>

          {/* Tab Content */}
          <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
            {activeTab === 'application' && (
              <div className="space-y-3">
                <h3 className="font-semibold text-gray-900">Application Record</h3>
                <FieldRow label="ID" value={p.kliq_application_id} />
                <FieldRow label="Name" value={p.name} />
                <FieldRow label="Email" value={p.email} />
                <FieldRow label="Status" value={<StatusBadge status={p.status} />} />
                <FieldRow label="Store URL" value={p.kliq_store_url} link />
                <FieldRow label="Claim Token" value={p.claim_token} />
                <FieldRow label="Store Created" value={p.store_created_at} />
                <FieldRow label="Claimed At" value={p.claimed_at} />
              </div>
            )}

            {activeTab === 'settings' && (
              <div className="space-y-3">
                <h3 className="font-semibold text-gray-900">Store Settings</h3>
                <FieldRow label="App Name" value={p.name} />
                <FieldRow label="Platform" value={p.primary_platform} />
                {p.generated_content.filter((c) => c.content_type === 'seo').map((seo, i) => (
                  <div key={i} className="mt-4 border-t border-gray-100 pt-4">
                    <h4 className="text-sm font-medium text-gray-700 mb-2">SEO Metadata</h4>
                    <FieldRow label="Title" value={seo.title} />
                    {seo.content_metadata && typeof seo.content_metadata === 'object' && (
                      <>
                        <FieldRow
                          label="Meta Description"
                          value={(seo.content_metadata as Record<string, string>).meta_description}
                        />
                        <FieldRow
                          label="Keywords"
                          value={JSON.stringify(
                            (seo.content_metadata as Record<string, string>).keywords
                          )}
                        />
                      </>
                    )}
                  </div>
                ))}
              </div>
            )}

            {activeTab === 'brand-colors' && (
              <div className="space-y-3">
                <h3 className="font-semibold text-gray-900">Brand Colors</h3>
                {p.brand_colors?.length ? (
                  <div className="flex gap-3 flex-wrap">
                    {p.brand_colors.map((c, i) => (
                      <div key={i} className="flex items-center gap-2">
                        <span
                          className="w-8 h-8 rounded-lg border border-gray-200"
                          style={{ backgroundColor: c.startsWith('#') ? c : `#${c}` }}
                        />
                        <span className="text-sm text-gray-600 font-mono">{c}</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-gray-400">No brand colors extracted</p>
                )}
                {p.generated_content
                  .filter((c) => c.content_type === 'color')
                  .map((color, i) => (
                    <div key={i} className="mt-4 border-t border-gray-100 pt-4">
                      <h4 className="text-sm font-medium text-gray-700 mb-2">
                        AI Color Analysis
                      </h4>
                      <pre className="text-xs text-gray-600 bg-gray-50 rounded-lg p-3 overflow-auto">
                        {JSON.stringify(color.content_metadata, null, 2)}
                      </pre>
                    </div>
                  ))}
              </div>
            )}

            {activeTab === 'coach-user' && (
              <div className="space-y-3">
                <h3 className="font-semibold text-gray-900">Coach User</h3>
                <FieldRow label="First Name" value={p.first_name} />
                <FieldRow label="Last Name" value={p.last_name} />
                <FieldRow label="Email" value={p.email} />
                <FieldRow label="Profile Image" value={p.profile_image_url} link />
                <FieldRow label="Banner Image" value={p.banner_image_url} link />
              </div>
            )}

            {activeTab === 'products' && (
              <div className="space-y-4">
                <h3 className="font-semibold text-gray-900">Products & Pricing</h3>
                {p.scraped_pricing.length === 0 ? (
                  <p className="text-gray-400">No pricing data</p>
                ) : (
                  p.scraped_pricing.map((item, i) => (
                    <div key={i} className="border border-gray-100 rounded-lg p-4">
                      <div className="flex justify-between">
                        <div>
                          <h4 className="font-medium text-gray-900">
                            {String(item.tier_name ?? '')}
                          </h4>
                          <p className="text-sm text-gray-500">
                            {String(item.platform ?? '')} — {String(item.interval ?? 'month')}
                          </p>
                        </div>
                        <p className="text-lg font-bold text-gray-900">
                          ${Number(item.price_amount ?? 0).toFixed(2)}
                        </p>
                      </div>
                      {item.benefits && (
                        <ul className="mt-2 text-sm text-gray-600 list-disc list-inside">
                          {(item.benefits as string[]).map((b, j) => (
                            <li key={j}>{b}</li>
                          ))}
                        </ul>
                      )}
                    </div>
                  ))
                )}
              </div>
            )}

            {activeTab === 'pages' && (
              <div className="space-y-4">
                <h3 className="font-semibold text-gray-900">Generated Pages</h3>
                {p.generated_content
                  .filter((c) => c.content_type === 'bio' || c.content_type === 'blog')
                  .map((item, i) => (
                    <div key={i} className="border border-gray-100 rounded-lg p-4">
                      <span className="text-xs font-medium text-gray-400 uppercase">
                        {String(item.content_type)}
                      </span>
                      {item.title && (
                        <h4 className="font-medium text-gray-900 mt-1">{String(item.title)}</h4>
                      )}
                      {item.body && (
                        <p className="text-sm text-gray-600 mt-2 whitespace-pre-wrap line-clamp-8">
                          {String(item.body)}
                        </p>
                      )}
                    </div>
                  ))}
              </div>
            )}

            {activeTab === 'features' && (
              <div className="space-y-3">
                <h3 className="font-semibold text-gray-900">Feature Flags</h3>
                <p className="text-sm text-gray-500">
                  Features configured when the store was created in the CMS.
                </p>
                <div className="grid grid-cols-2 gap-3 mt-4">
                  {[
                    'Authentication',
                    'Programs',
                    'Education',
                    'Live Streams',
                    'Community',
                    'Payments',
                    'Push Notifications',
                    'Analytics',
                  ].map((feat) => (
                    <div
                      key={feat}
                      className="flex items-center gap-2 border border-gray-100 rounded-lg p-3"
                    >
                      <span className="w-2 h-2 rounded-full bg-green-500" />
                      <span className="text-sm text-gray-700">{feat}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  )
}

function FieldRow({
  label,
  value,
  link,
}: {
  label: string
  value: React.ReactNode | unknown
  link?: boolean
}) {
  const isReactNode =
    typeof value === 'string' ||
    typeof value === 'number' ||
    typeof value === 'boolean' ||
    value === null ||
    value === undefined ||
    (typeof value === 'object' && '$$typeof' in (value as object))

  const display = value === null || value === undefined ? '-' : String(value)
  return (
    <div className="flex gap-4 py-1.5 border-b border-gray-50">
      <span className="text-sm font-medium text-gray-500 w-40 flex-shrink-0">{label}</span>
      {link && display !== '-' ? (
        <a
          href={display}
          target="_blank"
          rel="noopener"
          className="text-sm text-teal-700 hover:underline break-all"
        >
          {display}
        </a>
      ) : isReactNode && typeof value === 'object' && value !== null ? (
        <>{value as React.ReactNode}</>
      ) : (
        <span className="text-sm text-gray-900 break-all">{display}</span>
      )}
    </div>
  )
}
