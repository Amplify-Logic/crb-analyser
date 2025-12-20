import { Link, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'

const VALUE_PROPS = [
  {
    title: 'No BS Assessment',
    description: "We tell you what NOT to do. That's often more valuable than what to do.",
    icon: (
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
      </svg>
    ),
  },
  {
    title: 'Real Pricing, Real Data',
    description: 'Actual vendor costs, not guesses. We do the research so you can make informed decisions.',
    icon: (
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
  },
  {
    title: 'Gold In, Gold Out',
    description: 'Quality analysis requires quality input. Your effort in the workshop shapes every recommendation.',
    icon: (
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 10V3L4 14h7v7l9-11h-7z" />
      </svg>
    ),
  },
]

const HOW_IT_WORKS = [
  {
    step: 1,
    title: 'Take the free quiz',
    description: '5 minutes to see your AI readiness score and preview what we can find.',
    time: '5 min',
  },
  {
    step: 2,
    title: 'Complete the workshop',
    description: 'Deep-dive questions about your business. The more detailed your answers, the better your report.',
    time: '90 min',
  },
  {
    step: 3,
    title: 'AI analyzes everything',
    description: 'We research your industry, benchmark your operations, and identify real opportunities.',
    time: '24-48 hrs',
  },
  {
    step: 4,
    title: 'Get your roadmap',
    description: 'Specific recommendations with real pricing, honest ROI calculations, and clear next steps.',
    time: 'Delivered',
  },
]

const SAMPLE_FINDINGS = [
  {
    title: 'Customer Support Automation',
    verdict: 'Go for it',
    description: 'Your ticket volume and response patterns make this a clear win.',
    potential: '€24,000/year',
    confidence: 'high',
  },
  {
    title: 'AI Content Generation',
    verdict: 'Proceed with caution',
    description: 'Potential is there, but your brand voice needs more definition first.',
    potential: '€8,000/year',
    confidence: 'medium',
  },
  {
    title: 'Predictive Analytics',
    verdict: 'Not yet',
    description: 'Your data infrastructure needs work before this makes sense.',
    potential: 'Deferred',
    confidence: 'high',
  },
]

const REPORT_FEATURES = [
  '15-20 AI opportunities analyzed',
  'Honest verdicts: Go / Caution / Wait / No',
  'Real vendor pricing (not guesses)',
  'ROI calculations with visible assumptions',
  'Three options per recommendation',
  '"Don\'t do this" section included',
]

export default function Landing() {
  const navigate = useNavigate()

  const handleQuizStart = () => {
    // Always start fresh from landing page
    navigate('/quiz?new=true')
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
            <Link to="/login" className="text-gray-600 hover:text-gray-900 transition hidden sm:block">
              Sign In
            </Link>
            <button
              onClick={handleQuizStart}
              className="px-4 py-2 bg-primary-600 text-white font-medium rounded-lg hover:bg-primary-700 transition"
            >
              Take Free Quiz
            </button>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-28 sm:pt-32 pb-16 sm:pb-20 px-4">
        <div className="max-w-4xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <div className="inline-block px-4 py-1.5 bg-primary-50 text-primary-700 rounded-full text-sm font-medium mb-6">
              No fluff. No false promises. Just clarity.
            </div>
            <h1 className="text-4xl sm:text-5xl md:text-6xl font-bold text-gray-900 mb-6 leading-tight">
              Find Out Where AI
              <span className="text-primary-600"> Actually </span>
              Makes Sense for Your Business
            </h1>
            <p className="text-lg sm:text-xl text-gray-600 mb-4 max-w-2xl mx-auto">
              A 90-minute workshop that produces a genuinely useful AI roadmap.
            </p>
            <p className="text-base text-gray-500 mb-8 max-w-2xl mx-auto">
              Most AI assessments are 5-minute quizzes that tell you nothing.
              Ours requires effort because quality input = quality output.
            </p>

            <div className="flex flex-col sm:flex-row gap-4 justify-center mb-6">
              <button
                onClick={handleQuizStart}
                className="px-8 py-4 bg-primary-600 text-white font-semibold rounded-xl hover:bg-primary-700 transition shadow-lg shadow-primary-600/25 text-lg"
              >
                Start Free Quiz
                <span className="ml-2">→</span>
              </button>
              <Link
                to="/report/sample"
                className="px-8 py-4 border-2 border-gray-200 text-gray-700 font-semibold rounded-xl hover:border-gray-300 hover:bg-gray-50 transition text-lg"
              >
                See Sample Report
              </Link>
            </div>

            <p className="text-sm text-gray-500">
              Free quiz: 5 min • Full workshop: 90 min • Report: €147
            </p>
          </motion.div>
        </div>
      </section>

      {/* Value Props */}
      <section className="py-12 bg-gray-50 border-y border-gray-100">
        <div className="max-w-5xl mx-auto px-4">
          <div className="grid md:grid-cols-3 gap-8">
            {VALUE_PROPS.map((prop, index) => (
              <motion.div
                key={prop.title}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                className="text-center"
              >
                <div className="inline-flex items-center justify-center w-12 h-12 bg-primary-100 text-primary-600 rounded-xl mb-4">
                  {prop.icon}
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">{prop.title}</h3>
                <p className="text-gray-600">{prop.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* The Hard Truth */}
      <section className="py-20 px-4">
        <div className="max-w-3xl mx-auto">
          <div className="bg-yellow-50 border-2 border-yellow-200 rounded-2xl p-8">
            <h2 className="text-2xl font-bold text-yellow-900 mb-4">
              Let's be honest upfront
            </h2>
            <div className="space-y-4 text-yellow-800">
              <p>
                <strong>This is not a magic 10-minute solution.</strong> If you want a superficial AI assessment, there are plenty of free ones online. They'll tell you "AI can help!" and leave you no wiser.
              </p>
              <p>
                Our workshop takes <strong>90 minutes</strong> because we ask hard questions about your actual business operations, pain points, and goals. Generic questions = generic answers = useless report.
              </p>
              <p>
                <strong>The quality of your report directly depends on the quality of your answers.</strong> Rush through it, get a rushed report. Take it seriously, get insights worth 100x what you paid.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Sample Findings */}
      <section className="py-20 px-4 bg-gray-50">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              What honest findings look like
            </h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              We don't just say "implement AI." We tell you specifically what makes sense, what doesn't, and why.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-6">
            {SAMPLE_FINDINGS.map((finding, index) => (
              <motion.div
                key={finding.title}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.2 + index * 0.1 }}
                className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100"
              >
                <div className={`inline-block px-3 py-1 text-sm font-medium rounded-full mb-3 ${
                  finding.verdict === 'Go for it' ? 'bg-green-100 text-green-700' :
                  finding.verdict === 'Proceed with caution' ? 'bg-yellow-100 text-yellow-700' :
                  'bg-gray-100 text-gray-700'
                }`}>
                  {finding.verdict}
                </div>
                <h3 className="font-semibold text-gray-900 mb-2">{finding.title}</h3>
                <p className="text-sm text-gray-600 mb-4">{finding.description}</p>
                <div className="pt-3 border-t border-gray-100 flex justify-between items-center">
                  <span className={`text-lg font-bold ${
                    finding.potential === 'Deferred' ? 'text-gray-400' : 'text-green-600'
                  }`}>
                    {finding.potential}
                  </span>
                  <span className="text-xs text-gray-500">{finding.confidence} confidence</span>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section id="how-it-works" className="py-20 px-4">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              How it works
            </h2>
            <p className="text-lg text-gray-600">
              From quick assessment to comprehensive roadmap
            </p>
          </div>

          <div className="grid md:grid-cols-4 gap-6">
            {HOW_IT_WORKS.map((item, index) => (
              <motion.div
                key={item.step}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                className="text-center"
              >
                <div className="inline-flex items-center justify-center w-12 h-12 bg-primary-600 text-white rounded-full text-xl font-bold mb-4">
                  {item.step}
                </div>
                <div className="text-xs font-medium text-primary-600 mb-2">{item.time}</div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  {item.title}
                </h3>
                <p className="text-gray-600 text-sm">
                  {item.description}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section id="pricing" className="py-20 px-4 bg-gray-50">
        <div className="max-w-3xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              One price. No upsells.
            </h2>
            <p className="text-lg text-gray-600">
              €147 for the complete analysis. That's it.
            </p>
          </div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="bg-white rounded-3xl p-8 md:p-10 shadow-xl border border-gray-100"
          >
            <div className="text-center mb-8">
              <div className="inline-block px-4 py-1 bg-primary-100 text-primary-700 rounded-full text-sm font-medium mb-4">
                CRB Analysis Report
              </div>
              <div className="flex items-baseline justify-center gap-2 mb-2">
                <span className="text-5xl font-bold text-gray-900">€147</span>
                <span className="text-gray-500">one-time</span>
              </div>
              <p className="text-gray-500 text-sm">
                Requires ~90 min workshop completion
              </p>
            </div>

            <ul className="space-y-4 mb-8">
              {REPORT_FEATURES.map((feature, index) => (
                <li key={index} className="flex items-center gap-3">
                  <svg className="w-5 h-5 text-green-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  <span className="text-gray-700">{feature}</span>
                </li>
              ))}
            </ul>

            <button
              onClick={handleQuizStart}
              className="w-full py-4 bg-primary-600 text-white font-semibold rounded-xl hover:bg-primary-700 transition shadow-lg shadow-primary-600/25 text-lg mb-4"
            >
              Start With Free Quiz
            </button>

            <p className="text-center text-sm text-gray-500">
              Not satisfied? Full refund within 14 days.
            </p>
          </motion.div>

          {/* Enterprise option */}
          <div className="text-center mt-8 p-6 bg-white rounded-2xl border border-gray-200">
            <p className="font-medium text-gray-900 mb-2">Need hands-on help?</p>
            <p className="text-gray-600 text-sm mb-4">
              We offer live consultation packages where we work through the analysis together.
            </p>
            <a
              href="mailto:hello@crb-analyser.com?subject=Consultation%20Inquiry"
              className="text-primary-600 font-semibold hover:text-primary-700 transition"
            >
              Contact us for pricing →
            </a>
          </div>
        </div>
      </section>

      {/* Final CTA */}
      <section className="py-20 px-4 bg-gray-900">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="text-3xl font-bold text-white mb-4">
            Ready to find out what actually makes sense?
          </h2>
          <p className="text-lg text-gray-400 mb-8">
            Start with the free quiz. If the preview looks valuable, continue to the full workshop. No pressure, no tricks.
          </p>
          <button
            onClick={handleQuizStart}
            className="px-8 py-4 bg-white text-gray-900 font-semibold rounded-xl hover:bg-gray-100 transition text-lg"
          >
            Take the Free Quiz
          </button>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 px-4 bg-gray-50 border-t border-gray-100">
        <div className="max-w-5xl mx-auto">
          <div className="flex flex-col md:flex-row justify-between items-center gap-4">
            <div className="flex items-center gap-2">
              <span className="text-xl font-bold text-gray-900">
                CRB<span className="text-primary-600">Analyser</span>
              </span>
            </div>
            <div className="flex gap-6 text-gray-600 text-sm">
              <Link to="/privacy" className="hover:text-gray-900 transition">Privacy</Link>
              <Link to="/terms" className="hover:text-gray-900 transition">Terms</Link>
              <a href="mailto:hello@crb-analyser.com" className="hover:text-gray-900 transition">Contact</a>
            </div>
          </div>
          <div className="mt-6 pt-6 border-t border-gray-200 text-center text-sm text-gray-500">
            © 2025 CRB Analyser. No BS, just clarity.
          </div>
        </div>
      </footer>
    </div>
  )
}
