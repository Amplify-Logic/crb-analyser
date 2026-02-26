import { Link, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Logo } from '../../components/Logo'
import { ShimmerButton } from '../../components/magicui'

const PAIN_POINTS = [
  {
    title: 'Support Ticket Overload',
    problem: '40% repetitive',
    description: '"Where is my order?" "How do I return this?" Same questions, over and over, eating up your team\'s time.',
    potential: 'Deflect 40% of tickets',
  },
  {
    title: 'Inventory Forecasting',
    problem: 'Stockouts & overstock',
    description: 'Manual forecasting leads to missed sales from stockouts or capital tied up in excess inventory.',
    potential: 'Reduce stockouts 30%',
  },
  {
    title: 'Returns Processing',
    problem: '€5-15 per return',
    description: 'Manual review, restocking decisions, customer communication. Each return costs more than you think.',
    potential: 'Cut processing time 50%',
  },
  {
    title: 'Attribution Confusion',
    problem: 'Which ads actually work?',
    description: 'iOS changes broke tracking. You\'re spending on ads without knowing what\'s really driving sales.',
    potential: 'Clarity on ROAS',
  },
]

const SAMPLE_FINDINGS = [
  {
    title: 'Customer Support AI',
    verdict: 'Connect',
    verdictColor: 'emerald',
    description: 'Build a Claude workflow connecting your Shopify order data to your support tool. Auto-respond to WISMO queries in hours, not weeks.',
    roi: '€36,000/year',
  },
  {
    title: 'Inventory Forecasting Agent',
    verdict: 'Enhance',
    verdictColor: 'emerald',
    description: 'Deploy an AI agent on your existing sales data that predicts demand and flags reorder points. No new software needed.',
    roi: '€48,000/year',
  },
  {
    title: 'AI Product Descriptions',
    verdict: 'Skip',
    verdictColor: 'gray',
    description: 'Your product catalog is stable. Manual descriptions are fine for now — focus on higher-impact areas.',
    roi: 'Low impact',
  },
]

const SOFTWARE = [
  { name: 'Shopify', category: 'Platform' },
  { name: 'Gorgias', category: 'Support' },
  { name: 'Klaviyo', category: 'Email/SMS' },
  { name: 'Triple Whale', category: 'Attribution' },
  { name: 'Northbeam', category: 'Attribution' },
  { name: 'Recharge', category: 'Subscriptions' },
]

export default function Ecommerce() {
  const navigate = useNavigate()

  const handleQuizStart = () => {
    navigate('/quiz?industry=ecommerce&new=true')
  }

  return (
    <div className="min-h-screen bg-white">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-md border-b border-gray-100">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 py-4 flex justify-between items-center">
          <div className="flex items-center gap-4">
            <Logo size="sm" />
            <span className="text-sm text-gray-400">|</span>
            <span className="text-sm font-medium text-gray-600">E-commerce</span>
          </div>
          <div className="flex items-center gap-4">
            <Link to="/" className="text-sm text-gray-500 hover:text-gray-900 transition">
              All Industries
            </Link>
            <Link to="/login" className="text-sm font-medium text-gray-600 hover:text-gray-900 transition">
              Sign In
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="pt-32 pb-16 px-4 bg-gradient-to-b from-primary-50/50 to-white">
        <div className="max-w-4xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-primary-100 rounded-full text-sm font-medium text-primary-700 mb-6">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" />
              </svg>
              For DTC Brands & Online Retailers
            </div>

            <h1 className="text-4xl sm:text-5xl font-bold text-gray-900 mb-6 leading-tight">
              40% of your support tickets
              <br />
              <span className="text-primary-600">could answer themselves.</span>
            </h1>

            <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
              Get an architecture blueprint showing what to connect, what to automate, and what to skip.
              Real build estimates. Real ROI. No consultant fees.
            </p>

            <div className="flex flex-col sm:flex-row gap-4 justify-center items-center mb-8">
              <ShimmerButton
                onClick={handleQuizStart}
                className="text-lg"
                shimmerColor="#ffffff"
                background="linear-gradient(135deg, #7c3aed 0%, #6366f1 50%, #8b5cf6 100%)"
              >
                Take the Free Quiz
                <span className="ml-2">→</span>
              </ShimmerButton>

              <Link
                to="/report/sample-ecommerce"
                className="px-6 py-3 text-gray-700 font-medium hover:text-primary-600 transition flex items-center gap-2"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                Nordic Outdoor Co.
              </Link>
              <Link
                to="/report/sample-wizard-firepits"
                className="px-6 py-3 text-gray-700 font-medium hover:text-primary-600 transition flex items-center gap-2"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                Wizard Firepits
              </Link>
            </div>

            <div className="flex flex-wrap justify-center gap-6 text-sm text-gray-500">
              <span className="flex items-center gap-2">
                <svg className="w-4 h-4 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                5-min quiz
              </span>
              <span className="flex items-center gap-2">
                <svg className="w-4 h-4 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                €147 full report
              </span>
              <span className="flex items-center gap-2">
                <svg className="w-4 h-4 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                48-72h delivery
              </span>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Pain Points */}
      <section className="py-16 px-4">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-2xl font-bold text-gray-900 text-center mb-4">
            Sound familiar?
          </h2>
          <p className="text-center text-gray-600 mb-12">
            These are the problems we help e-commerce brands solve.
          </p>

          <div className="grid md:grid-cols-2 gap-6">
            {PAIN_POINTS.map((point, index) => (
              <motion.div
                key={point.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                className="bg-white rounded-xl p-6 border border-gray-200 hover:border-primary-300 hover:shadow-lg transition-all"
              >
                <div className="flex items-start justify-between mb-3">
                  <h3 className="font-bold text-gray-900">{point.title}</h3>
                  <span className="text-sm font-medium text-red-600 bg-red-50 px-2 py-0.5 rounded">
                    {point.problem}
                  </span>
                </div>
                <p className="text-sm text-gray-600 mb-3">{point.description}</p>
                <div className="pt-3 border-t border-gray-100">
                  <span className="text-sm font-medium text-emerald-600">
                    Potential: {point.potential}
                  </span>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Sample Output */}
      <section className="py-16 px-4 bg-gray-50 border-y border-gray-100">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-2xl font-bold text-gray-900 text-center mb-4">
            What you get
          </h2>
          <p className="text-center text-gray-600 mb-12">
            Not vague advice. Specific verdicts with clear reasoning.
          </p>

          <div className="grid md:grid-cols-3 gap-6">
            {SAMPLE_FINDINGS.map((finding, index) => (
              <motion.div
                key={finding.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                className="bg-white rounded-xl p-6 border border-gray-200"
              >
                <div className={`inline-block px-3 py-1 text-xs font-semibold uppercase tracking-wide rounded-full mb-4 ${
                  finding.verdictColor === 'emerald' ? 'bg-emerald-50 text-emerald-700 border border-emerald-100' :
                  finding.verdictColor === 'amber' ? 'bg-amber-50 text-amber-700 border border-amber-100' :
                  'bg-gray-100 text-gray-600'
                }`}>
                  {finding.verdict}
                </div>
                <h3 className="font-bold text-gray-900 mb-2">{finding.title}</h3>
                <p className="text-sm text-gray-600 mb-4">{finding.description}</p>
                <div className="pt-3 border-t border-gray-100 flex justify-between items-center">
                  <span className={`font-bold ${finding.roi === 'Low impact' ? 'text-gray-400' : 'text-emerald-600'}`}>
                    {finding.roi}
                  </span>
                  <span className="text-xs text-gray-400">estimated annual</span>
                </div>
              </motion.div>
            ))}
          </div>

          <div className="text-center mt-8 flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link
              to="/quiz"
              className="inline-flex items-center gap-2 text-primary-600 font-medium hover:text-primary-700"
            >
              Get your personalized report
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </Link>
            <span className="text-gray-300 hidden sm:inline">|</span>
            <Link
              to="/report/sample-ecommerce"
              className="inline-flex items-center gap-2 text-gray-500 font-medium hover:text-gray-700"
            >
              Nordic Outdoor Co.
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
              </svg>
            </Link>
            <span className="text-gray-300 hidden sm:inline">|</span>
            <Link
              to="/report/sample-wizard-firepits"
              className="inline-flex items-center gap-2 text-gray-500 font-medium hover:text-gray-700"
            >
              Wizard Firepits
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
              </svg>
            </Link>
          </div>
        </div>
      </section>

      {/* Software We Know */}
      <section className="py-16 px-4">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-2xl font-bold text-gray-900 text-center mb-4">
            We know your stack
          </h2>
          <p className="text-center text-gray-600 mb-8">
            Our blueprint integrates with the tools you already use.
          </p>

          <div className="flex flex-wrap justify-center gap-3">
            {SOFTWARE.map((tool) => (
              <div
                key={tool.name}
                className="px-4 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm"
              >
                <span className="font-medium text-gray-900">{tool.name}</span>
                <span className="text-gray-400 ml-2">• {tool.category}</span>
              </div>
            ))}
            <div className="px-4 py-2 bg-primary-50 border border-primary-200 rounded-lg text-sm text-primary-700">
              + 50 more
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-16 px-4 bg-gray-900">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="text-3xl font-bold text-white mb-4">
            Ready to build your AI operating system?
          </h2>
          <p className="text-gray-400 mb-8">
            Take the free 5-minute quiz. Get your AI readiness score instantly.
            Full report for €147 if you want to go deeper.
          </p>

          <button
            onClick={handleQuizStart}
            className="px-8 py-4 bg-white text-gray-900 font-bold rounded-xl hover:bg-gray-100 transition-all hover:scale-105 shadow-lg"
          >
            Start Free Quiz →
          </button>

          <p className="text-sm text-gray-500 mt-6">
            No credit card required for the quiz
          </p>
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
