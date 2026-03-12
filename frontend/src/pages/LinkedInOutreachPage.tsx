import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  fetchLinkedInQueue,
  fetchLinkedInStats,
  copyConnectionNote,
  updateLinkedInStatus,
} from '@/api/linkedin'
import { KPICard } from '@/components/ui/KPICard'
import { StatusBadge } from '@/components/ui/StatusBadge'
import { LoadingSpinner } from '@/components/ui/LoadingSpinner'
import { ClipboardDocumentIcon, ArrowTopRightOnSquareIcon } from '@heroicons/react/24/outline'
import type { LinkedInQueueItem } from '@/types/linkedin'

export function LinkedInOutreachPage() {
  const queryClient = useQueryClient()
  const [statusFilter, setStatusFilter] = useState('')
  const [search, setSearch] = useState('')
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [note, setNote] = useState('')
  const [copyFeedback, setCopyFeedback] = useState('')

  const stats = useQuery({ queryKey: ['linkedin-stats'], queryFn: fetchLinkedInStats })
  const queue = useQuery({
    queryKey: ['linkedin-queue', statusFilter, search],
    queryFn: () =>
      fetchLinkedInQueue({
        status: statusFilter || undefined,
        search: search || undefined,
        limit: 100,
      }),
  })

  const genNote = useMutation({
    mutationFn: copyConnectionNote,
    onSuccess: (data) => {
      setNote(data.connection_note)
      queryClient.invalidateQueries({ queryKey: ['linkedin-queue'] })
    },
  })

  const statusMut = useMutation({
    mutationFn: ({ id, status }: { id: number; status: string }) =>
      updateLinkedInStatus(id, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['linkedin-queue'] })
      queryClient.invalidateQueries({ queryKey: ['linkedin-stats'] })
    },
  })

  const handleCopyNote = async () => {
    if (note) {
      await navigator.clipboard.writeText(note)
      setCopyFeedback('Copied!')
      setTimeout(() => setCopyFeedback(''), 2000)
    }
  }

  const handleOpenLinkedIn = (url: string) => {
    window.open(url, '_blank', 'noopener,noreferrer')
  }

  const s = stats.data
  const queueData = (queue.data ?? []) as LinkedInQueueItem[]

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900 tracking-tight">LinkedIn Outreach</h1>

      {/* Stats */}
      {s && (
        <div className="grid grid-cols-4 gap-4">
          <KPICard label="Queued" value={s.queued} />
          <KPICard label="Sent" value={s.sent} />
          <KPICard label="Accepted" value={s.accepted} />
          <KPICard
            label="Accept Rate"
            value={`${s.accept_rate}%`}
            sublabel={`${s.declined} declined, ${s.no_response} no response`}
          />
        </div>
      )}

      {/* Filters */}
      <div className="flex gap-3">
        <input
          type="text"
          placeholder="Search name or email..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="px-3 py-2 text-sm border border-gray-300 rounded-lg w-64 focus:ring-2 focus:ring-teal-500 focus:border-teal-500"
        />
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500"
        >
          <option value="">All Statuses</option>
          {['QUEUED', 'COPIED', 'SENT', 'ACCEPTED', 'DECLINED', 'NO_RESPONSE'].map((s) => (
            <option key={s} value={s}>{s.replace(/_/g, ' ')}</option>
          ))}
        </select>
      </div>

      <div className="grid grid-cols-3 gap-6">
        {/* Queue List */}
        <div className="col-span-2 space-y-2">
          {queue.isLoading ? (
            <LoadingSpinner />
          ) : (
            queueData.map((p) => (
              <div
                key={p.id}
                onClick={() => {
                  setSelectedId(p.id)
                  setNote(p.connection_note ?? '')
                }}
                className={`bg-white border rounded-xl p-4 cursor-pointer transition-colors ${
                  selectedId === p.id
                    ? 'border-teal-500 ring-1 ring-teal-500'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-gray-900">{p.name}</p>
                    <p className="text-sm text-gray-500">{p.email}</p>
                    {p.niche && (
                      <span className="text-xs px-2 py-0.5 bg-teal-50 text-teal-900 rounded-full mt-1 inline-block">
                        {p.niche}
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-3">
                    <StatusBadge status={p.status} />
                    {p.linkedin_url && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          handleOpenLinkedIn(p.linkedin_url!)
                        }}
                        className="p-1.5 text-gray-400 hover:text-teal-700 rounded-lg hover:bg-gray-100"
                        title="Open LinkedIn"
                      >
                        <ArrowTopRightOnSquareIcon className="h-4 w-4" />
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Note Panel */}
        <div className="space-y-4">
          <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm sticky top-8">
            <h3 className="text-sm font-semibold text-gray-900 mb-3">Connection Note</h3>

            {selectedId ? (
              <>
                <button
                  onClick={() => genNote.mutate(selectedId)}
                  disabled={genNote.isPending}
                  className="w-full mb-3 px-4 py-2 text-sm font-semibold bg-kliq-green text-white rounded-lg hover:bg-kliq-green-hover disabled:opacity-50"
                >
                  {genNote.isPending ? 'Generating...' : 'Generate Note'}
                </button>

                {note && (
                  <>
                    <textarea
                      value={note}
                      onChange={(e) => setNote(e.target.value)}
                      className="w-full h-32 p-3 text-sm border border-gray-300 rounded-lg resize-none focus:ring-2 focus:ring-teal-500"
                    />
                    <div className="flex gap-2 mt-3">
                      <button
                        onClick={handleCopyNote}
                        className="flex-1 flex items-center justify-center gap-2 px-3 py-2 text-sm font-medium border border-gray-300 rounded-lg hover:bg-gray-50"
                      >
                        <ClipboardDocumentIcon className="h-4 w-4" />
                        {copyFeedback || 'Copy Note'}
                      </button>
                      <button
                        onClick={() =>
                          statusMut.mutate({ id: selectedId, status: 'SENT' })
                        }
                        className="flex-1 px-3 py-2 text-sm font-medium bg-kliq-green text-white rounded-lg hover:bg-kliq-green-hover"
                      >
                        Mark Sent
                      </button>
                    </div>
                    <div className="flex gap-2 mt-2">
                      <button
                        onClick={() =>
                          statusMut.mutate({ id: selectedId, status: 'ACCEPTED' })
                        }
                        className="flex-1 px-3 py-2 text-sm font-medium text-green-700 bg-green-50 rounded-lg hover:bg-green-100"
                      >
                        Accepted
                      </button>
                      <button
                        onClick={() =>
                          statusMut.mutate({ id: selectedId, status: 'DECLINED' })
                        }
                        className="flex-1 px-3 py-2 text-sm font-medium text-red-700 bg-red-50 rounded-lg hover:bg-red-100"
                      >
                        Declined
                      </button>
                    </div>
                  </>
                )}
              </>
            ) : (
              <p className="text-sm text-gray-400">Select a prospect to view/generate note</p>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
