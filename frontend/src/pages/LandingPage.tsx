import { Link } from 'react-router-dom'

const features = [
  {
    title: 'AI-Powered Content',
    description:
      'Automatically generate blogs, product listings, and SEO-optimized content from your existing social media presence.',
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 00-2.455 2.456z" />
      </svg>
    ),
  },
  {
    title: 'Instant Store Builder',
    description:
      'Get a fully branded, white-label app and webstore ready to sell — no design or coding skills needed.',
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13.5 21v-7.5a.75.75 0 01.75-.75h3a.75.75 0 01.75.75V21m-4.5 0H2.36m11.14 0H18m0 0h3.64m-1.39 0V9.349m-16.5 11.65V9.35m0 0a3.001 3.001 0 003.75-.615A2.993 2.993 0 009.75 9.75c.896 0 1.7-.393 2.25-1.016a2.993 2.993 0 002.25 1.016c.896 0 1.7-.393 2.25-1.016A3.001 3.001 0 0021 9.349m-18 0a2.99 2.99 0 00.621-1.098L5.25 3h13.5l1.629 5.251A2.99 2.99 0 0021 9.35" />
      </svg>
    ),
  },
  {
    title: 'Dispute Protection',
    description:
      'Built-in chargeback prevention and payment dispute tools to protect your revenue and reputation.',
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
      </svg>
    ),
  },
  {
    title: 'Growth Tools',
    description:
      'Analytics, email campaigns, and outreach automation to help you find and retain more paying clients.',
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M2.25 18L9 11.25l4.306 4.307a11.95 11.95 0 015.814-5.519l2.74-1.22m0 0l-5.94-2.28m5.94 2.28l-2.28 5.941" />
      </svg>
    ),
  },
]

const stats = [
  { value: '500+', label: 'Coaches Onboarded' },
  { value: '10K+', label: 'Content Pieces Generated' },
  { value: '95%', label: 'Setup Time Saved' },
]

export function LandingPage() {
  return (
    <div>
      {/* Hero */}
      <section className="py-20 px-6">
        <div className="max-w-4xl mx-auto text-center">
          <h1 className="text-5xl md:text-6xl font-bold text-gray-900 tracking-tight leading-tight">
            Your coaching business,
            <br />
            <span className="text-kliq-green">launched in minutes</span>
          </h1>
          <p className="mt-6 text-lg text-gray-600 max-w-2xl mx-auto leading-relaxed">
            KLIQ gives fitness and wellness creators everything they need — a branded app, webstore,
            AI-generated content, and growth tools — all set up and ready to go.
          </p>
          <div className="mt-10 flex items-center justify-center gap-4">
            <Link
              to="/signup"
              className="bg-kliq-green text-white font-semibold px-8 py-3.5 rounded-xl hover:bg-kliq-green-hover transition-colors text-base"
            >
              Get Started Free
            </Link>
            <Link
              to="/blog"
              className="bg-white text-kliq-green font-semibold px-8 py-3.5 rounded-xl border-2 border-kliq-green hover:bg-kliq-green-light transition-colors text-base"
            >
              Read Our Blog
            </Link>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-20 px-6 bg-white">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-gray-900">Everything you need to succeed</h2>
            <p className="mt-3 text-gray-600 max-w-xl mx-auto">
              From content creation to payment processing, KLIQ handles the tech so you can focus on
              coaching.
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {features.map((feature) => (
              <div
                key={feature.title}
                className="p-6 rounded-xl border border-gray-200 hover:border-kliq-green/30 hover:shadow-md transition-all"
              >
                <div className="w-12 h-12 rounded-lg bg-kliq-green-light flex items-center justify-center text-kliq-green mb-4">
                  {feature.icon}
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">{feature.title}</h3>
                <p className="text-sm text-gray-600 leading-relaxed">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Stats / Social Proof */}
      <section className="py-20 px-6">
        <div className="max-w-4xl mx-auto">
          <div className="bg-kliq-green rounded-2xl p-12 text-center">
            <h2 className="text-2xl font-bold text-white mb-10">Trusted by coaches worldwide</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              {stats.map((stat) => (
                <div key={stat.label}>
                  <div className="text-4xl font-bold text-tangerine">{stat.value}</div>
                  <div className="mt-2 text-sm text-gray-300">{stat.label}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 px-6 bg-white">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="text-3xl font-bold text-gray-900">Ready to grow your coaching business?</h2>
          <p className="mt-4 text-gray-600">
            Join hundreds of coaches who've already launched their branded store with KLIQ.
          </p>
          <Link
            to="/signup"
            className="inline-block mt-8 bg-kliq-green text-white font-semibold px-10 py-4 rounded-xl hover:bg-kliq-green-hover transition-colors text-base"
          >
            Get Started Free
          </Link>
        </div>
      </section>
    </div>
  )
}
