import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

const PRICING_TIERS = [
  {
    id: 'free',
    name: 'Free Quiz',
    price: '€0',
    description: 'Find out if AI can help your business',
    cta: 'Take the Quiz',
    ctaLink: '/quiz',
    features: [
      'AI Readiness Score (0-100)',
      '3 opportunity previews',
      'Personalized next steps',
      '2 minutes to complete',
    ],
    highlighted: false,
  },
  {
    id: 'quick',
    name: 'Quick Report',
    price: '€47',
    description: 'Full analysis with actionable insights',
    cta: 'Get Your Report',
    ctaLink: '/quiz?upgrade=quick',
    features: [
      'Everything in Free, plus:',
      '10-15 detailed findings',
      'Top 3 vendor recommendations',
      'ROI calculations',
      'PDF download',
    ],
    highlighted: true,
    badge: 'Most Popular',
  },
  {
    id: 'full',
    name: 'Full Analysis',
    price: '€297',
    description: 'Complete CRB analysis with expert call',
    cta: 'Get Full Analysis',
    ctaLink: '/quiz?upgrade=full',
    features: [
      'Everything in Quick, plus:',
      'Detailed vendor comparisons',
      'Implementation roadmap',
      '30-min expert consultation',
      '90-day email support',
    ],
    highlighted: false,
  },
]

const HOW_IT_WORKS = [
  {
    step: 1,
    title: 'Take the Quiz',
    description: 'Answer 5 quick questions about your business. We research your company while you answer.',
    icon: (
      <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
      </svg>
    ),
  },
  {
    step: 2,
    title: 'Get Your Score',
    description: 'See your AI Readiness Score and preview the opportunities we found for your business.',
    icon: (
      <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
      </svg>
    ),
  },
  {
    step: 3,
    title: 'Unlock Insights',
    description: 'Get your full report with specific recommendations, ROI calculations, and vendor comparisons.',
    icon: (
      <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
      </svg>
    ),
  },
]

const TRUST_POINTS = [
  { label: 'Impartial', desc: 'Vendor-agnostic recommendations' },
  { label: 'Transparent', desc: 'All assumptions shown' },
  { label: 'Honest', desc: "We'll tell you if AI isn't right for you" },
]

export default function Landing() {
  const navigate = useNavigate()
  const [email, setEmail] = useState('')

  const handleQuizStart = () => {
    navigate('/quiz')
  }

  return (
    <div className="min-h-screen bg-white">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-md border-b border-gray-100">
        <div className="max-w-6xl mx-auto px-4 py-4 flex justify-between items-center">
          <Link to="/" className="text-xl font-bold text-gray-900">
            CRB<span className="text-primary-600">Analyser</span>
          </Link>
          <div className="flex items-center gap-4">
            <Link to="/login" className="text-gray-600 hover:text-gray-900 transition">
              Sign In
            </Link>
            <button
              onClick={handleQuizStart}
              className="px-4 py-2 bg-primary-600 text-white font-medium rounded-lg hover:bg-primary-700 transition"
            >
              Free Quiz
            </button>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-32 pb-20 px-4">
        <div className="max-w-4xl mx-auto text-center">
          <div className="inline-block px-4 py-1 bg-primary-50 text-primary-700 rounded-full text-sm font-medium mb-6">
            AI Readiness Assessment
          </div>
          <h1 className="text-4xl md:text-6xl font-bold text-gray-900 mb-6 leading-tight">
            Find out how much
            <span className="text-primary-600"> AI could save </span>
            your business
          </h1>
          <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
            Get a personalized Cost/Risk/Benefit analysis in minutes.
            We'll tell you exactly where AI makes sense—and where it doesn't.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-8">
            <button
              onClick={handleQuizStart}
              className="px-8 py-4 bg-primary-600 text-white font-semibold rounded-xl hover:bg-primary-700 transition shadow-lg shadow-primary-600/25 text-lg"
            >
              Take the Free Quiz
              <span className="ml-2">→</span>
            </button>
            <a
              href="#how-it-works"
              className="px-8 py-4 border-2 border-gray-200 text-gray-700 font-semibold rounded-xl hover:border-gray-300 transition text-lg"
            >
              See How It Works
            </a>
          </div>

          <p className="text-sm text-gray-500">
            No credit card required • 2 minutes • Instant results
          </p>
        </div>
      </section>

      {/* Trust Bar */}
      <section className="py-8 bg-gray-50 border-y border-gray-100">
        <div className="max-w-4xl mx-auto px-4">
          <div className="flex flex-wrap justify-center gap-8 md:gap-16">
            {TRUST_POINTS.map((point) => (
              <div key={point.label} className="text-center">
                <div className="text-lg font-semibold text-gray-900">{point.label}</div>
                <div className="text-sm text-gray-500">{point.desc}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Value Proposition */}
      <section className="py-20 px-4">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              Not another generic AI assessment
            </h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              We research YOUR company, analyze YOUR industry, and give you specific recommendations—not vague advice.
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-8">
            <div className="bg-red-50 rounded-2xl p-8 border border-red-100">
              <h3 className="text-xl font-semibold text-red-900 mb-4 flex items-center gap-2">
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
                Other AI Assessments
              </h3>
              <ul className="space-y-3 text-red-800">
                <li className="flex items-start gap-2">
                  <span className="mt-1">•</span>
                  Generic questionnaire, generic results
                </li>
                <li className="flex items-start gap-2">
                  <span className="mt-1">•</span>
                  "You should use AI" (thanks, very helpful)
                </li>
                <li className="flex items-start gap-2">
                  <span className="mt-1">•</span>
                  Pushing their own products
                </li>
                <li className="flex items-start gap-2">
                  <span className="mt-1">•</span>
                  Vague ROI claims without math
                </li>
              </ul>
            </div>

            <div className="bg-green-50 rounded-2xl p-8 border border-green-100">
              <h3 className="text-xl font-semibold text-green-900 mb-4 flex items-center gap-2">
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                CRB Analyser
              </h3>
              <ul className="space-y-3 text-green-800">
                <li className="flex items-start gap-2">
                  <span className="mt-1">•</span>
                  We research your company before you finish the quiz
                </li>
                <li className="flex items-start gap-2">
                  <span className="mt-1">•</span>
                  Specific tools, specific pricing, specific ROI
                </li>
                <li className="flex items-start gap-2">
                  <span className="mt-1">•</span>
                  Vendor-agnostic (we'll recommend free options)
                </li>
                <li className="flex items-start gap-2">
                  <span className="mt-1">•</span>
                  Honest: "You're not ready yet" is a valid answer
                </li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section id="how-it-works" className="py-20 px-4 bg-gray-50">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              How it works
            </h2>
            <p className="text-lg text-gray-600">
              From quiz to actionable insights in minutes
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {HOW_IT_WORKS.map((item) => (
              <div key={item.step} className="text-center">
                <div className="inline-flex items-center justify-center w-16 h-16 bg-primary-100 text-primary-600 rounded-2xl mb-4">
                  {item.icon}
                </div>
                <div className="text-sm font-medium text-primary-600 mb-2">
                  Step {item.step}
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">
                  {item.title}
                </h3>
                <p className="text-gray-600">
                  {item.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing */}
      <section id="pricing" className="py-20 px-4">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              Simple, transparent pricing
            </h2>
            <p className="text-lg text-gray-600">
              Start free. Upgrade if you want the full picture.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {PRICING_TIERS.map((tier) => (
              <div
                key={tier.id}
                className={`rounded-2xl p-8 ${
                  tier.highlighted
                    ? 'bg-primary-600 text-white ring-4 ring-primary-600 ring-offset-4'
                    : 'bg-white border-2 border-gray-100'
                }`}
              >
                {tier.badge && (
                  <div className="inline-block px-3 py-1 bg-white/20 rounded-full text-sm font-medium mb-4">
                    {tier.badge}
                  </div>
                )}
                <h3 className={`text-xl font-semibold mb-2 ${tier.highlighted ? 'text-white' : 'text-gray-900'}`}>
                  {tier.name}
                </h3>
                <div className={`text-4xl font-bold mb-2 ${tier.highlighted ? 'text-white' : 'text-gray-900'}`}>
                  {tier.price}
                </div>
                <p className={`mb-6 ${tier.highlighted ? 'text-primary-100' : 'text-gray-600'}`}>
                  {tier.description}
                </p>
                <Link
                  to={tier.ctaLink}
                  className={`block w-full py-3 rounded-xl font-semibold text-center transition ${
                    tier.highlighted
                      ? 'bg-white text-primary-600 hover:bg-primary-50'
                      : 'bg-primary-600 text-white hover:bg-primary-700'
                  }`}
                >
                  {tier.cta}
                </Link>
                <ul className={`mt-6 space-y-3 ${tier.highlighted ? 'text-primary-100' : 'text-gray-600'}`}>
                  {tier.features.map((feature, i) => (
                    <li key={i} className="flex items-start gap-2">
                      <svg
                        className={`w-5 h-5 mt-0.5 flex-shrink-0 ${tier.highlighted ? 'text-primary-200' : 'text-primary-600'}`}
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                      {feature}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Honest CTA */}
      <section className="py-20 px-4 bg-gray-900">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="text-3xl font-bold text-white mb-4">
            We'll be honest with you
          </h2>
          <p className="text-lg text-gray-400 mb-8">
            If AI isn't right for your business right now, we'll tell you.
            A report that saves you from a bad €10K investment is more valuable
            than one that sounds impressive but leads you astray.
          </p>
          <button
            onClick={handleQuizStart}
            className="px-8 py-4 bg-white text-gray-900 font-semibold rounded-xl hover:bg-gray-100 transition text-lg"
          >
            Find Out What's Right for You
          </button>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 px-4 bg-gray-50 border-t border-gray-100">
        <div className="max-w-5xl mx-auto">
          <div className="flex flex-col md:flex-row justify-between items-center gap-4">
            <div className="text-gray-600">
              © 2025 CRB Analyser. All rights reserved.
            </div>
            <div className="flex gap-6 text-gray-600">
              <Link to="/privacy" className="hover:text-gray-900 transition">Privacy</Link>
              <Link to="/terms" className="hover:text-gray-900 transition">Terms</Link>
              <a href="mailto:hello@crb-analyser.com" className="hover:text-gray-900 transition">Contact</a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}
