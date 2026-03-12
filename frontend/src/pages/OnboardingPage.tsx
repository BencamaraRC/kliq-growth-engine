import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { StepProgress } from '@/components/ui/StepProgress'

const STEPS = ['Welcome', 'Explore Store', 'Review Content', 'Share']

export function OnboardingPage() {
  const [currentStep, setCurrentStep] = useState(0)
  const navigate = useNavigate()

  const nextStep = () => {
    if (currentStep < STEPS.length - 1) {
      setCurrentStep((s) => s + 1)
    } else {
      navigate('/', { replace: true })
    }
  }

  return (
    <div className="min-h-screen bg-ivory flex flex-col">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-3xl mx-auto px-6 py-4">
          <span className="text-xl font-bold text-kliq-green tracking-tight">KLIQ</span>
        </div>
      </header>

      {/* Progress */}
      <div className="max-w-3xl mx-auto w-full px-6 pt-10 pb-6">
        <StepProgress steps={STEPS} current={currentStep} />
      </div>

      {/* Step content */}
      <div className="flex-1 flex items-start justify-center px-6 pb-16">
        <div className="bg-white rounded-2xl shadow-lg border border-gray-200 p-8 w-full max-w-lg">
          {currentStep === 0 && <WelcomeStep onNext={nextStep} />}
          {currentStep === 1 && <ExploreStoreStep onNext={nextStep} />}
          {currentStep === 2 && <ReviewContentStep onNext={nextStep} />}
          {currentStep === 3 && <ShareStep onNext={nextStep} />}
        </div>
      </div>
    </div>
  )
}

function WelcomeStep({ onNext }: { onNext: () => void }) {
  return (
    <div className="text-center">
      <div className="w-16 h-16 rounded-full bg-kliq-green-light flex items-center justify-center mx-auto mb-6">
        <svg className="w-8 h-8 text-kliq-green" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.5}
            d="M9 12.75L11.25 15 15 9.75M21 12c0 1.268-.63 2.39-1.593 3.068a3.745 3.745 0 01-1.043 3.296 3.745 3.745 0 01-3.296 1.043A3.745 3.745 0 0112 21c-1.268 0-2.39-.63-3.068-1.593a3.746 3.746 0 01-3.296-1.043 3.745 3.745 0 01-1.043-3.296A3.745 3.745 0 013 12c0-1.268.63-2.39 1.593-3.068a3.745 3.745 0 011.043-3.296 3.746 3.746 0 013.296-1.043A3.746 3.746 0 0112 3c1.268 0 2.39.63 3.068 1.593a3.746 3.746 0 013.296 1.043 3.746 3.746 0 011.043 3.296A3.745 3.745 0 0121 12z"
          />
        </svg>
      </div>
      <h2 className="text-2xl font-bold text-gray-900 mb-2">Welcome to KLIQ!</h2>
      <p className="text-gray-600 mb-8">
        Your store is ready. Let's walk through a few quick steps to get you set up for success.
      </p>
      <button
        onClick={onNext}
        className="bg-kliq-green text-white font-semibold px-8 py-3 rounded-xl hover:bg-kliq-green-hover transition-colors"
      >
        Let's Get Started
      </button>
    </div>
  )
}

function ExploreStoreStep({ onNext }: { onNext: () => void }) {
  return (
    <div className="text-center">
      <div className="w-16 h-16 rounded-full bg-kliq-green-light flex items-center justify-center mx-auto mb-6">
        <svg className="w-8 h-8 text-kliq-green" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.5}
            d="M13.5 21v-7.5a.75.75 0 01.75-.75h3a.75.75 0 01.75.75V21m-4.5 0H2.36m11.14 0H18m0 0h3.64m-1.39 0V9.349m-16.5 11.65V9.35m0 0a3.001 3.001 0 003.75-.615A2.993 2.993 0 009.75 9.75c.896 0 1.7-.393 2.25-1.016a2.993 2.993 0 002.25 1.016c.896 0 1.7-.393 2.25-1.016A3.001 3.001 0 0021 9.349m-18 0a2.99 2.99 0 00.621-1.098L5.25 3h13.5l1.629 5.251A2.99 2.99 0 0021 9.35"
          />
        </svg>
      </div>
      <h2 className="text-2xl font-bold text-gray-900 mb-2">Explore Your Store</h2>
      <p className="text-gray-600 mb-6">
        Your branded webstore has been pre-built with AI-generated content tailored to your brand.
        Take a look around and customize anything you'd like.
      </p>
      <div className="bg-gray-50 rounded-xl p-4 mb-6 text-left">
        <h3 className="text-sm font-semibold text-gray-900 mb-2">Your store includes:</h3>
        <ul className="text-sm text-gray-600 space-y-1.5">
          <li className="flex items-center gap-2">
            <span className="text-kliq-green">&#10003;</span> Branded homepage with your bio
          </li>
          <li className="flex items-center gap-2">
            <span className="text-kliq-green">&#10003;</span> Programs and product listings
          </li>
          <li className="flex items-center gap-2">
            <span className="text-kliq-green">&#10003;</span> Blog posts from your content
          </li>
          <li className="flex items-center gap-2">
            <span className="text-kliq-green">&#10003;</span> SEO-optimized pages
          </li>
        </ul>
      </div>
      <button
        onClick={onNext}
        className="bg-kliq-green text-white font-semibold px-8 py-3 rounded-xl hover:bg-kliq-green-hover transition-colors"
      >
        I've Explored My Store
      </button>
    </div>
  )
}

function ReviewContentStep({ onNext }: { onNext: () => void }) {
  return (
    <div className="text-center">
      <div className="w-16 h-16 rounded-full bg-kliq-green-light flex items-center justify-center mx-auto mb-6">
        <svg className="w-8 h-8 text-kliq-green" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.5}
            d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z"
          />
        </svg>
      </div>
      <h2 className="text-2xl font-bold text-gray-900 mb-2">Review Your Content</h2>
      <p className="text-gray-600 mb-6">
        We've generated blog posts, product descriptions, and marketing copy based on your existing
        content. Review it and make any edits you'd like.
      </p>
      <div className="grid grid-cols-2 gap-4 mb-6">
        <div className="bg-gray-50 rounded-xl p-4">
          <div className="text-2xl font-bold text-kliq-green">5+</div>
          <div className="text-xs text-gray-500 mt-1">Blog Posts</div>
        </div>
        <div className="bg-gray-50 rounded-xl p-4">
          <div className="text-2xl font-bold text-kliq-green">3+</div>
          <div className="text-xs text-gray-500 mt-1">Products</div>
        </div>
      </div>
      <button
        onClick={onNext}
        className="bg-kliq-green text-white font-semibold px-8 py-3 rounded-xl hover:bg-kliq-green-hover transition-colors"
      >
        Content Looks Good
      </button>
    </div>
  )
}

function ShareStep({ onNext }: { onNext: () => void }) {
  const [copied, setCopied] = useState(false)
  const storeUrl = 'https://your-store.kliq.app'

  const copyLink = () => {
    navigator.clipboard.writeText(storeUrl)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="text-center">
      <div className="w-16 h-16 rounded-full bg-kliq-green-light flex items-center justify-center mx-auto mb-6">
        <svg className="w-8 h-8 text-kliq-green" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.5}
            d="M7.217 10.907a2.25 2.25 0 100 2.186m0-2.186c.18.324.283.696.283 1.093s-.103.77-.283 1.093m0-2.186l9.566-5.314m-9.566 7.5l9.566 5.314m0 0a2.25 2.25 0 103.935 2.186 2.25 2.25 0 00-3.935-2.186zm0-12.814a2.25 2.25 0 103.933-2.185 2.25 2.25 0 00-3.933 2.185z"
          />
        </svg>
      </div>
      <h2 className="text-2xl font-bold text-gray-900 mb-2">Share Your Store</h2>
      <p className="text-gray-600 mb-6">
        You're all set! Share your store with your audience and start growing your coaching business.
      </p>

      {/* Copy link */}
      <div className="flex items-center gap-2 bg-gray-50 rounded-lg p-3 mb-6">
        <input
          type="text"
          readOnly
          value={storeUrl}
          className="flex-1 bg-transparent text-sm text-gray-700 outline-none"
        />
        <button
          onClick={copyLink}
          className="text-xs font-semibold text-kliq-green hover:text-kliq-green-hover px-3 py-1.5 rounded-md bg-white border border-gray-200 transition-colors"
        >
          {copied ? 'Copied!' : 'Copy'}
        </button>
      </div>

      {/* Social share buttons */}
      <div className="flex justify-center gap-3 mb-8">
        <a
          href={`https://twitter.com/intent/tweet?url=${encodeURIComponent(storeUrl)}&text=${encodeURIComponent('Check out my new coaching store on KLIQ!')}`}
          target="_blank"
          rel="noopener noreferrer"
          className="w-10 h-10 rounded-full bg-gray-100 flex items-center justify-center text-gray-600 hover:bg-kliq-green hover:text-white transition-all"
          title="Share on Twitter"
        >
          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
            <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
          </svg>
        </a>
        <a
          href={`https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(storeUrl)}`}
          target="_blank"
          rel="noopener noreferrer"
          className="w-10 h-10 rounded-full bg-gray-100 flex items-center justify-center text-gray-600 hover:bg-kliq-green hover:text-white transition-all"
          title="Share on Facebook"
        >
          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
            <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z" />
          </svg>
        </a>
        <a
          href={`https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(storeUrl)}`}
          target="_blank"
          rel="noopener noreferrer"
          className="w-10 h-10 rounded-full bg-gray-100 flex items-center justify-center text-gray-600 hover:bg-kliq-green hover:text-white transition-all"
          title="Share on LinkedIn"
        >
          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
            <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z" />
          </svg>
        </a>
      </div>

      <button
        onClick={onNext}
        className="bg-kliq-green text-white font-semibold px-8 py-3 rounded-xl hover:bg-kliq-green-hover transition-colors"
      >
        Go to Dashboard
      </button>
    </div>
  )
}
