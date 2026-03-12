import { useState, useEffect, useCallback } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { fetchOperationsProspects } from '@/api/prospects'
import { fetchStatusCounts } from '@/api/analytics'
import {
  triggerDiscover,
  triggerFullPipeline,
  triggerScrape,
  triggerBatchPipeline,
  getTaskStatus,
} from '@/api/pipeline'
import { KPICard } from '@/components/ui/KPICard'
import { StatusBadge } from '@/components/ui/StatusBadge'
import { PlatformBadge } from '@/components/ui/PlatformBadge'
import { LoadingSpinner } from '@/components/ui/LoadingSpinner'

interface TrackedTask {
  id: string
  label: string
  status: string
  result?: string
}

export function OperationsPage() {
  const [statusFilter, setStatusFilter] = useState('')
  const [search, setSearch] = useState('')
  const [tasks, setTasks] = useState<TrackedTask[]>([])

  const statusCounts = useQuery({
    queryKey: ['status-counts'],
    queryFn: fetchStatusCounts,
  })
  const prospects = useQuery({
    queryKey: ['ops-prospects', statusFilter, search],
    queryFn: () =>
      fetchOperationsProspects({
        status: statusFilter || undefined,
        search: search || undefined,
        limit: 100,
      }),
  })

  const discoverMut = useMutation({
    mutationFn: triggerDiscover,
    onSuccess: (data) => {
      if (data.task_id) {
        setTasks((t) => [...t, { id: data.task_id, label: 'Discovery', status: 'PENDING' }])
      }
    },
  })

  const pipelineMut = useMutation({
    mutationFn: triggerFullPipeline,
    onSuccess: (data) => {
      if (data.task_id) {
        setTasks((t) => [...t, { id: data.task_id, label: 'Full Pipeline', status: 'PENDING' }])
      }
    },
  })

  const scrapeMut = useMutation({
    mutationFn: triggerScrape,
    onSuccess: (data) => {
      if (data.task_id) {
        setTasks((t) => [...t, { id: data.task_id, label: 'Scrape', status: 'PENDING' }])
      }
    },
  })

  const batchMut = useMutation({
    mutationFn: triggerBatchPipeline,
    onSuccess: (data) => {
      if (data.task_id) {
        setTasks((t) => [...t, { id: data.task_id, label: 'Batch Pipeline', status: 'PENDING' }])
      }
    },
  })

  // Poll running tasks
  const pollTasks = useCallback(async () => {
    const pending = tasks.filter((t) => t.status === 'PENDING' || t.status === 'STARTED')
    for (const task of pending) {
      try {
        const result = await getTaskStatus(task.id)
        setTasks((prev) =>
          prev.map((t) =>
            t.id === task.id
              ? { ...t, status: result.status, result: result.result }
              : t
          )
        )
      } catch {
        // ignore polling errors
      }
    }
  }, [tasks])

  useEffect(() => {
    const hasPending = tasks.some((t) => t.status === 'PENDING' || t.status === 'STARTED')
    if (!hasPending) return
    const interval = setInterval(pollTasks, 3000)
    return () => clearInterval(interval)
  }, [tasks, pollTasks])

  const countsMap = Object.fromEntries(
    (statusCounts.data ?? []).map((s) => [s.status, s.count])
  )

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-bold text-gray-900 tracking-tight">Operations</h1>

      {/* Quick Actions */}
      <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm">
        <h3 className="text-sm font-semibold text-gray-900 mb-4">Quick Actions</h3>
        <div className="flex gap-3">
          <button
            onClick={() => discoverMut.mutate({})}
            disabled={discoverMut.isPending}
            className="px-4 py-2 text-sm font-semibold bg-kliq-green text-white rounded-lg hover:bg-kliq-green-hover disabled:opacity-50"
          >
            {discoverMut.isPending ? 'Discovering...' : 'Run Discovery'}
          </button>
          <a
            href="/health/ready"
            target="_blank"
            rel="noopener"
            className="px-4 py-2 text-sm font-semibold border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
          >
            API Health Check
          </a>
        </div>
      </div>

      {/* Status Counts */}
      <div className="grid grid-cols-4 gap-4">
        <KPICard label="Discovered" value={countsMap['DISCOVERED'] ?? 0} />
        <KPICard label="Store Created" value={countsMap['STORE_CREATED'] ?? 0} />
        <KPICard label="Email Sent" value={countsMap['EMAIL_SENT'] ?? 0} />
        <KPICard label="Claimed" value={countsMap['CLAIMED'] ?? 0} />
      </div>

      {/* Batch Operations */}
      <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm">
        <h3 className="text-sm font-semibold text-gray-900 mb-4">Batch Pipeline</h3>
        <div className="flex gap-3 flex-wrap">
          {['DISCOVERED', 'SCRAPED', 'CONTENT_GENERATED'].map((s) => (
            <button
              key={s}
              onClick={() => batchMut.mutate(s)}
              disabled={batchMut.isPending}
              className="px-4 py-2 text-sm font-medium border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50"
            >
              Process {s.replace(/_/g, ' ')} ({countsMap[s] ?? 0})
            </button>
          ))}
        </div>
      </div>

      {/* Task Monitor */}
      {tasks.length > 0 && (
        <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm">
          <h3 className="text-sm font-semibold text-gray-900 mb-4">Task Monitor</h3>
          <div className="space-y-2">
            {tasks.map((task) => (
              <div
                key={task.id}
                className="flex items-center justify-between border border-gray-100 rounded-lg p-3"
              >
                <div>
                  <p className="text-sm font-medium text-gray-900">{task.label}</p>
                  <p className="text-xs text-gray-400 font-mono">{task.id}</p>
                </div>
                <StatusBadge status={task.status} />
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Prospect Operations */}
      <div>
        <div className="flex items-center gap-3 mb-4">
          <h3 className="text-sm font-semibold text-gray-900">Prospect Operations</h3>
          <input
            type="text"
            placeholder="Search..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg w-48 focus:ring-2 focus:ring-teal-500"
          />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500"
          >
            <option value="">All</option>
            {['DISCOVERED', 'SCRAPED', 'CONTENT_GENERATED', 'STORE_CREATED', 'EMAIL_SENT', 'CLAIMED'].map(
              (s) => (
                <option key={s} value={s}>{s.replace(/_/g, ' ')}</option>
              )
            )}
          </select>
        </div>

        {prospects.isLoading ? (
          <LoadingSpinner />
        ) : (
          <div className="space-y-2">
            {(prospects.data ?? []).map((p) => (
              <div
                key={p.id}
                className="bg-white border border-gray-200 rounded-xl p-4 flex items-center justify-between"
              >
                <div className="flex items-center gap-4">
                  <div>
                    <p className="font-medium text-gray-900">{p.name}</p>
                    <p className="text-sm text-gray-500">{p.email}</p>
                  </div>
                  <StatusBadge status={p.status} />
                  <PlatformBadge platform={p.platform} />
                  <span className="text-xs text-gray-400">
                    {p.followers.toLocaleString()} followers
                  </span>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => pipelineMut.mutate(p.id)}
                    disabled={pipelineMut.isPending}
                    className="px-3 py-1.5 text-xs font-medium bg-kliq-green text-white rounded-lg hover:bg-kliq-green-hover disabled:opacity-50"
                  >
                    Full Pipeline
                  </button>
                  <button
                    onClick={() => scrapeMut.mutate(p.id)}
                    disabled={scrapeMut.isPending}
                    className="px-3 py-1.5 text-xs font-medium border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50"
                  >
                    Re-scrape
                  </button>
                  {p.claim_token && (
                    <a
                      href={`/preview?token=${p.claim_token}`}
                      target="_blank"
                      rel="noopener"
                      className="px-3 py-1.5 text-xs font-medium border border-gray-300 rounded-lg hover:bg-gray-50"
                    >
                      Preview
                    </a>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
