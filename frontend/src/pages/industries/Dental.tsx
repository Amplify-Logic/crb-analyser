import { Link, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Logo } from '../../components/Logo'
import { ShimmerButton } from '../../components/magicui'

const PAIN_POINTS = [
  {
    title: 'Patient No-Shows',
    problem: '10-15% appointment rate',
    description: 'Empty chairs mean lost revenue. Manual reminder calls are time-consuming and often ineffective.',
    potential: 'Reduce no-shows by 50%+',
  },
  {
    title: 'Insurance Verification',
    problem: '15-30 min per patient',
    description: 'Staff manually calling insurers, waiting on hold, re-verifying benefits before each visit.',
    potential: 'Save 10+ hours/week',
  },
  {
    title: 'Treatment Acceptance',
    problem: '50-60% average rate',
    description: 'Patients leave without scheduling recommended treatment. No systematic follow-up process.',
    potential: 'Increase acceptance to 80%+',
  },
  {
    title: 'Hygiene Recare',
    problem: 'Patients slip through cracks',
    description: 'No automated tracking of overdue hygiene patients. Manual recall lists that nobody has time to call.',
    potential: 'Recover €30K+/year in recare',
  },
]

const SAMPLE_FINDINGS = [
  {
    title: 'Patient Recall Automation',
    verdict: 'Proceed',
    verdictColor: 'emerald',
    description: 'Your no-show rate and recare gaps show clear automation potential. High ROI with minimal risk.',
    roi: '€24,000/year',
  },
  {
    title: 'AI Treatment Planning',
    verdict: 'Proceed with Caution',
    verdictColor: 'amber',
    description: 'AI-assisted diagnostics can improve case acceptance, but requires clinical workflow integration.',
    roi: '€12,000/year',
  },
  {
    title: 'Predictive No-Show System',
    verdict: 'Skip',
    verdictColor: 'gray',
    description: 'Your patient volume doesn\'t justify the investment yet. Revisit when scheduling 40+ patients/day.',
    roi: 'Deferred',
  },
]

const SOFTWARE = [
  { name: 'Dentrix', category: 'Practice Management' },
  { name: 'Open Dental', category: 'Practice Management' },
  { name: 'Curve Dental', category: 'Cloud PMS' },
  { name: 'Weave', category: 'Patient Communication' },
  { name: 'RevenueWell', category: 'Marketing & Recall' },
  { name: 'Pearl AI', category: 'AI Diagnostics' },
]

export default function Dental() {
  const navigate = useNavigate()

  const handleQuizStart = () => {
    navigate('/quiz?industry=dental&new=true')
  }

  return (
    <div className="min-h-screen bg-white">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-md border-b border-gray-100">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 py-4 flex justify-between items-center">
          <div className="flex items-center gap-4">
            <Logo size="sm" />
            <span className="text-sm text-gray-400">|</span>
            <span className="text-sm font-medium text-gray-600">Dental Practices</span>
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
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
              </svg>
              For Dental Practices & DSOs
            </div>

            <h1 className="text-4xl sm:text-5xl font-bold text-gray-900 mb-6 leading-tight">
              Every no-show costs your practice
              <br />
              <span className="text-primary-600">€200-500.</span>
            </h1>

            <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
              Find out exactly which AI tools will reduce no-shows, speed up insurance, and boost case acceptance—and which ones to skip.
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
                to="/report/sample"
                className="px-6 py-3 text-gray-700 font-medium hover:text-primary-600 transition flex items-center gap-2"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                See Sample Report
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
            These are the problems we help dental practices solve.
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
                  <span className={`font-bold ${finding.roi === 'Deferred' ? 'text-gray-400' : 'text-emerald-600'}`}>
                    {finding.roi}
                  </span>
                  <span className="text-xs text-gray-400">estimated annual</span>
                </div>
              </motion.div>
            ))}
          </div>

          <div className="text-center mt-8">
            <Link
              to="/report/sample"
              className="inline-flex items-center gap-2 text-primary-600 font-medium hover:text-primary-700"
            >
              View full sample report
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </Link>
          </div>
        </div>
      </section>

      {/* Software We Know */}
      <section className="py-16 px-4">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-2xl font-bold text-gray-900 text-center mb-4">
            We know your software
          </h2>
          <p className="text-center text-gray-600 mb-8">
            Our recommendations integrate with the tools you already use.
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
              + 30 more
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-16 px-4 bg-gray-900">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="text-3xl font-bold text-white mb-4">
            Ready to find out which AI tools make sense for your practice?
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
