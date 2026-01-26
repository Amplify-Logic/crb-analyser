import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Logo } from '../components/Logo'

const INDUSTRIES = [
  {
    slug: 'professional-services',
    name: 'Professional Services',
    description: 'Accountants, lawyers, consultants, financial advisors',
    painPoints: ['Client onboarding taking 3-5 hours', 'Time tracking leakage', 'Document chaos'],
    icon: (
      <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
      </svg>
    ),
    color: 'primary',
    ready: true,
  },
  {
    slug: 'dental',
    name: 'Dental Practices',
    description: 'Solo practices, group practices, DSOs',
    painPoints: ['Patient no-shows', 'Insurance verification delays', 'Treatment acceptance rates'],
    icon: (
      <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
      </svg>
    ),
    color: 'emerald',
    ready: true,
  },
  {
    slug: 'ecommerce',
    name: 'E-commerce',
    description: 'DTC brands, marketplace sellers, B2B wholesale',
    painPoints: ['Support ticket overload', 'Inventory forecasting', 'Returns processing'],
    icon: (
      <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" />
      </svg>
    ),
    color: 'amber',
    ready: true,
  },
]

const colorClasses = {
  primary: {
    bg: 'bg-primary-50',
    border: 'border-primary-200 hover:border-primary-400',
    icon: 'bg-primary-100 text-primary-600',
    badge: 'bg-primary-100 text-primary-700',
  },
  emerald: {
    bg: 'bg-emerald-50',
    border: 'border-emerald-200 hover:border-emerald-400',
    icon: 'bg-emerald-100 text-emerald-600',
    badge: 'bg-emerald-100 text-emerald-700',
  },
  amber: {
    bg: 'bg-amber-50',
    border: 'border-amber-200 hover:border-amber-400',
    icon: 'bg-amber-100 text-amber-600',
    badge: 'bg-amber-100 text-amber-700',
  },
}

export default function LandingHome() {
  return (
    <div className="min-h-screen bg-white">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-md border-b border-gray-100">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 py-4 flex justify-between items-center">
          <Logo size="sm" />
          <div className="flex items-center gap-4">
            <Link to="/login" className="text-sm font-medium text-gray-600 hover:text-gray-900 transition">
              Sign In
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="pt-32 pb-16 px-4">
        <div className="max-w-4xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <h1 className="text-4xl sm:text-5xl font-bold text-gray-900 mb-6 leading-tight">
              Should you invest in AI?
              <br />
              <span className="text-primary-600">We'll tell you.</span>
            </h1>

            <p className="text-xl text-gray-600 mb-4 max-w-2xl mx-auto">
              Get a report that tells you exactly which AI tools make sense for your business—and which ones to skip.
            </p>

            <p className="text-lg text-gray-500 mb-12">
              Real prices. Real ROI. Week-by-week implementation plan.
            </p>
          </motion.div>
        </div>
      </section>

      {/* Industry Selector */}
      <section className="pb-20 px-4">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-center text-lg font-semibold text-gray-900 mb-8">
            Select your industry to get started
          </h2>

          <div className="grid md:grid-cols-3 gap-6">
            {INDUSTRIES.map((industry, index) => {
              const colors = colorClasses[industry.color as keyof typeof colorClasses]

              return (
                <motion.div
                  key={industry.slug}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.5, delay: index * 0.1 }}
                >
                  <Link
                    to={`/${industry.slug}`}
                    className={`block h-full p-6 rounded-2xl border-2 ${colors.border} ${colors.bg} transition-all duration-300 hover:shadow-lg hover:-translate-y-1`}
                  >
                    <div className={`inline-flex items-center justify-center w-14 h-14 rounded-xl ${colors.icon} mb-4`}>
                      {industry.icon}
                    </div>

                    <h3 className="text-xl font-bold text-gray-900 mb-2">
                      {industry.name}
                    </h3>

                    <p className="text-sm text-gray-600 mb-4">
                      {industry.description}
                    </p>

                    <div className="space-y-2">
                      <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">
                        Common pain points:
                      </p>
                      <ul className="space-y-1">
                        {industry.painPoints.map((point, i) => (
                          <li key={i} className="text-sm text-gray-700 flex items-start gap-2">
                            <span className="text-gray-400 mt-1">•</span>
                            {point}
                          </li>
                        ))}
                      </ul>
                    </div>

                    <div className="mt-6 flex items-center justify-between">
                      <span className={`text-xs font-medium px-2 py-1 rounded-full ${colors.badge}`}>
                        {industry.ready ? 'Available' : 'Coming Soon'}
                      </span>
                      <span className="text-sm font-medium text-gray-900 flex items-center gap-1">
                        Learn more
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                        </svg>
                      </span>
                    </div>
                  </Link>
                </motion.div>
              )
            })}
          </div>
        </div>
      </section>

      {/* How It Works - Simplified */}
      <section className="py-16 px-4 bg-gray-50 border-y border-gray-100">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-2xl font-bold text-gray-900 text-center mb-12">
            How it works
          </h2>

          <div className="grid md:grid-cols-4 gap-8">
            {[
              { step: '1', title: 'Quick Quiz', desc: '5 minutes', detail: 'Get your AI readiness score' },
              { step: '2', title: 'Deep Dive', desc: '90 minutes', detail: 'AI workshop maps your workflows' },
              { step: '3', title: 'Analysis', desc: '24-48 hours', detail: 'We crunch the numbers' },
              { step: '4', title: 'Report', desc: 'Delivered', detail: 'Clear verdicts + action plan' },
            ].map((item, index) => (
              <motion.div
                key={item.step}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                className="text-center"
              >
                <div className="inline-flex items-center justify-center w-10 h-10 bg-gray-900 text-white rounded-full text-lg font-bold mb-3">
                  {item.step}
                </div>
                <h3 className="font-bold text-gray-900 mb-1">{item.title}</h3>
                <p className="text-sm text-primary-600 font-medium mb-1">{item.desc}</p>
                <p className="text-sm text-gray-500">{item.detail}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing - Simple */}
      <section className="py-16 px-4">
        <div className="max-w-2xl mx-auto text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">
            Simple pricing
          </h2>
          <p className="text-gray-600 mb-8">
            Expert consultants typically charge €2,000-5,000 for similar analysis.
          </p>

          <div className="bg-white rounded-2xl border-2 border-gray-200 p-8 inline-block">
            <div className="text-5xl font-bold text-gray-900 mb-2">€147</div>
            <p className="text-gray-500 mb-6">one-time payment</p>

            <ul className="text-left space-y-3 mb-6">
              {[
                '10-15 AI opportunities analyzed',
                'Clear verdict on each: Proceed, Wait, or Skip',
                '3 options per recommendation with real pricing',
                'Week-by-week implementation playbook',
                'Interactive report you can share with your team',
              ].map((item, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-gray-700">
                  <svg className="w-5 h-5 text-emerald-500 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  {item}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 px-4 border-t border-gray-100">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row justify-between items-center gap-4">
          <Logo size="sm" showIcon={false} linkToHome={false} />
          <p className="text-sm text-gray-500">© 2026 ReadyPath. No BS, just clarity.</p>
          <div className="flex gap-6 text-sm text-gray-500">
            <Link to="/privacy" className="hover:text-gray-900 transition">Privacy</Link>
            <Link to="/terms" className="hover:text-gray-900 transition">Terms</Link>
          </div>
        </div>
      </footer>
    </div>
  )
}
