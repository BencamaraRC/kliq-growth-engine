import { useState, useEffect } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { validateClaim, submitClaim, type ClaimValidation } from '@/api/claim'

export function ClaimPage() {
  const [searchParams] = useSearchParams()
  const token = searchParams.get('token')
  const navigate = useNavigate()

  const [prospect, setProspect] = useState<ClaimValidation | null>(null)
  const [validating, setValidating] = useState(true)
  const [validationError, setValidationError] = useState('')

  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    if (!token) {
      setValidationError('Invalid claim link. No token provided.')
      setValidating(false)
      return
    }

    validateClaim(token)
      .then((data) => {
        setProspect(data)
        setValidating(false)
      })
      .catch((err) => {
        const detail = err?.response?.data?.detail || 'This claim link is invalid or has already been used.'
        setValidationError(detail)
        setValidating(false)
      })
  }, [token])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    if (password !== confirmPassword) {
      setError('Passwords do not match')
      return
    }

    if (password.length < 8) {
      setError('Password must be at least 8 characters')
      return
    }

    setSubmitting(true)
    try {
      const result = await submitClaim(token!, password)
      if (result.access_token) {
        localStorage.setItem('kliq_token', result.access_token)
        localStorage.setItem(
          'kliq_user',
          JSON.stringify({ username: prospect?.email, name: prospect?.name })
        )
      }
      navigate('/onboarding', { replace: true })
    } catch (err: any) {
      const detail = err?.response?.data?.detail
      setError(detail || 'Failed to claim store. Please try again.')
    } finally {
      setSubmitting(false)
    }
  }

  if (validating) {
    return (
      <div className="min-h-screen bg-ivory flex items-center justify-center">
        <div className="text-center">
          <div className="w-8 h-8 border-2 border-kliq-green border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="mt-4 text-sm text-gray-500">Validating your claim link...</p>
        </div>
      </div>
    )
  }

  if (validationError) {
    return (
      <div className="min-h-screen bg-ivory flex items-center justify-center px-4">
        <div className="bg-white rounded-2xl shadow-lg border border-gray-200 p-8 w-full max-w-sm text-center">
          <div className="w-12 h-12 rounded-full bg-red-100 flex items-center justify-center mx-auto mb-4">
            <svg className="w-6 h-6 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </div>
          <h1 className="text-xl font-bold text-gray-900 mb-2">Invalid Link</h1>
          <p className="text-sm text-gray-600">{validationError}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-ivory flex items-center justify-center px-4">
      <div className="bg-white rounded-2xl shadow-lg border border-gray-200 p-8 w-full max-w-sm">
        {/* Store preview header */}
        <div className="text-center mb-6">
          {prospect?.profile_image_url ? (
            <img
              src={prospect.profile_image_url}
              alt={prospect.name}
              className="w-16 h-16 rounded-full mx-auto mb-3 object-cover"
            />
          ) : (
            <div className="w-16 h-16 rounded-full bg-kliq-green/10 flex items-center justify-center mx-auto mb-3">
              <span className="text-2xl font-bold text-kliq-green">
                {prospect?.name?.[0]?.toUpperCase()}
              </span>
            </div>
          )}
          <h1 className="text-2xl font-bold text-gray-900 tracking-tight">Claim Your Store</h1>
          <p className="text-sm text-gray-500 mt-1">
            Welcome, {prospect?.name}! Set a password to access your KLIQ store.
          </p>
          {prospect?.store_url && (
            <a
              href={prospect.store_url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-block mt-2 text-xs text-kliq-green hover:text-kliq-green-hover font-medium"
            >
              Preview your store &rarr;
            </a>
          )}
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
            <input
              type="email"
              value={prospect?.email || ''}
              disabled
              className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm bg-gray-50 text-gray-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Set Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-teal-500"
              placeholder="Min. 8 characters"
              autoFocus
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Confirm Password</label>
            <input
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-teal-500"
              required
            />
          </div>

          {error && (
            <p className="text-sm text-red-600 bg-red-50 rounded-lg px-3 py-2">{error}</p>
          )}

          <button
            type="submit"
            disabled={submitting}
            className="w-full bg-kliq-green text-white font-semibold py-2.5 rounded-lg hover:bg-kliq-green-hover transition-colors disabled:opacity-50"
          >
            {submitting ? 'Claiming your store...' : 'Claim My Store'}
          </button>
        </form>
      </div>
    </div>
  )
}
