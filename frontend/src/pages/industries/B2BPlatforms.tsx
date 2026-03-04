import { Link, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Logo } from '../../components/Logo'
import { ShimmerButton } from '../../components/magicui'

const PAIN_POINTS = [
  {
    title: 'System Integration Gaps',
    problem: 'Manual data sync',
    description: 'CRM doesn\'t talk to ERP, ERP doesn\'t talk to IoT. Someone manually copies data between systems every day.',
    potential: 'Automate 90% of data sync',
  },
  {
    title: 'Scaling Operations',
    problem: 'Processes breaking',
    description: 'What worked at 20 employees is cracking at 60. Knowledge is in people\'s heads, not systems.',
    potential: 'Build automated playbooks',
  },
  {
    title: 'Partner Management',
    problem: 'Onboarding bottleneck',
    description: 'Every new distributor needs manual setup, training, portal access. It doesn\'t scale to 100+ partners.',
    potential: 'Self-service partner portal',
  },
  {
    title: 'Revenue Optimization',
    problem: 'Blind spots in usage data',
    description: 'You\'re sitting on IoT usage data that could drive upsells, prevent churn, and optimize pricing. But nobody\'s looking at it.',
    potential: 'AI-driven pricing intelligence',
  },
]

const SAMPLE_FINDINGS = [
  {
    title: 'CRM to ERP Auto-Sync',
    verdict: 'Connect',
    verdictColor: 'emerald',
    description: 'Build a Claude workflow that syncs deal closures from HubSpot to auto-generate invoices in Exact. Ships in 8 hours.',
    roi: '\u20AC24,000/year',
  },
  {
    title: 'Predictive Churn Agent',
    verdict: 'Enhance',
    verdictColor: 'blue',
    description: 'AI agent monitoring usage patterns across your fleet. Flags at-risk accounts before they churn.',
    roi: '\u20AC48,000/year',
  },
  {
    title: 'Enterprise CRM Migration',
    verdict: 'Skip',
    verdictColor: 'gray',
    description: 'HubSpot works fine with API integrations. Salesforce migration would cost 6 months and \u20AC200K. Not worth it.',
    roi: 'Negative ROI',
  },
]

const STACK = [
  { name: 'HubSpot', category: 'CRM' },
  { name: 'Exact Online', category: 'ERP' },
  { name: 'Azure IoT Hub', category: 'IoT' },
  { name: 'Salesforce FSL', category: 'Field Service' },
  { name: 'Chargebee', category: 'Billing' },
  { name: 'Notion', category: 'Knowledge' },
]

export default function B2BPlatforms() {
  const navigate = useNavigate()

  const handleQuizStart = () => {
    navigate('/quiz?industry=b2b-platforms&new=true')
  }

  return (
    <div className="min-h-screen bg-white">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-md border-b border-gray-100">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 py-4 flex justify-between items-center">
          <div className="flex items-center gap-4">
            <Logo size="sm" />
            <span className="text-sm text-gray-400">|</span>
            <span className="text-sm font-medium text-gray-600">B2B Platforms</span>
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
      <section className="pt-32 pb-16 px-4 bg-gradient-to-b from-violet-50/50 to-white">
        <div className="max-w-4xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-violet-100 rounded-full text-sm font-medium text-violet-700 mb-6">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.25 3v1.5M4.5 8.25H3m18 0h-1.5M4.5 12H3m18 0h-1.5m-15 3.75H3m18 0h-1.5M8.25 19.5V21M12 3v1.5m0 15V21m3.75-18v1.5m0 15V21m-9-1.5h10.5a2.25 2.25 0 002.25-2.25V6.75a2.25 2.25 0 00-2.25-2.25H6.75A2.25 2.25 0 004.5 6.75v10.5a2.25 2.25 0 002.25 2.25zm.75-12h9v9h-9v-9z" />
              </svg>
              For Hardware-to-Platform & IoT Businesses
            </div>

            <h1 className="text-4xl sm:text-5xl font-bold text-gray-900 mb-6 leading-tight">
              Your systems don't talk to each other.
              <br />
              <span className="text-violet-600">We'll wire them up.</span>
            </h1>

            <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
              Get an architecture blueprint that connects your CRM, ERP, IoT, and billing
              into one AI-powered operating system. Only what makes sense for your stack.
            </p>

            <div className="flex flex-col sm:flex-row gap-4 justify-center items-center mb-8">
              <ShimmerButton
                onClick={handleQuizStart}
                className="text-lg"
                shimmerColor="#ffffff"
                background="linear-gradient(135deg, #7c3aed 0%, #6366f1 50%, #8b5cf6 100%)"
              >
                Get Your Architecture Blueprint
                <span className="ml-2">&rarr;</span>
              </ShimmerButton>
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
                &euro;147 full report
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
            These are the problems we help B2B platform companies solve.
          </p>

          <div className="grid md:grid-cols-2 gap-6">
            {PAIN_POINTS.map((point, index) => (
              <motion.div
                key={point.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                className="bg-white rounded-xl p-6 border border-gray-200 hover:border-violet-300 hover:shadow-lg transition-all"
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
            Not "buy this software." Specific architecture decisions with clear reasoning.
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
                  finding.verdictColor === 'blue' ? 'bg-blue-50 text-blue-700 border border-blue-100' :
                  'bg-gray-100 text-gray-600'
                }`}>
                  {finding.verdict}
                </div>
                <h3 className="font-bold text-gray-900 mb-2">{finding.title}</h3>
                <p className="text-sm text-gray-600 mb-4">{finding.description}</p>
                <div className="pt-3 border-t border-gray-100 flex justify-between items-center">
                  <span className={`font-bold ${finding.roi === 'Negative ROI' ? 'text-gray-400' : 'text-emerald-600'}`}>
                    {finding.roi}
                  </span>
                  <span className="text-xs text-gray-400">estimated annual</span>
                </div>
              </motion.div>
            ))}
          </div>

          <div className="text-center mt-8">
            <Link
              to="/quiz?industry=b2b-platforms&new=true"
              className="inline-flex items-center gap-2 text-violet-600 font-medium hover:text-violet-700"
            >
              Get your personalized architecture blueprint
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </Link>
          </div>
        </div>
      </section>

      {/* Stack We Know */}
      <section className="py-16 px-4">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-2xl font-bold text-gray-900 text-center mb-4">
            We know your stack
          </h2>
          <p className="text-center text-gray-600 mb-8">
            Our blueprint integrates with the tools you already use.
          </p>

          <div className="flex flex-wrap justify-center gap-3">
            {STACK.map((tool) => (
              <div
                key={tool.name}
                className="px-4 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm"
              >
                <span className="font-medium text-gray-900">{tool.name}</span>
                <span className="text-gray-400 ml-2">&bull; {tool.category}</span>
              </div>
            ))}
            <div className="px-4 py-2 bg-violet-50 border border-violet-200 rounded-lg text-sm text-violet-700">
              + custom IoT &amp; more
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-16 px-4 bg-gray-900">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="text-3xl font-bold text-white mb-4">
            Ready to connect your systems?
          </h2>
          <p className="text-gray-400 mb-8">
            Take the free 5-minute quiz. Get your AI readiness score instantly.
            Full architecture blueprint for &euro;147.
          </p>

          <button
            onClick={handleQuizStart}
            className="px-8 py-4 bg-white text-gray-900 font-bold rounded-xl hover:bg-gray-100 transition-all hover:scale-105 shadow-lg"
          >
            Start Free Quiz &rarr;
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
          <p className="text-sm text-gray-500">&copy; 2026 Ready Path. No BS, just clarity.</p>
          <div className="flex gap-6 text-sm text-gray-500">
            <Link to="/privacy" className="hover:text-gray-900 transition">Privacy</Link>
            <Link to="/terms" className="hover:text-gray-900 transition">Terms</Link>
          </div>
        </div>
      </footer>
    </div>
  )
}
