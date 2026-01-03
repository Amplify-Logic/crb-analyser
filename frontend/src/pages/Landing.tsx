import { Link, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'

const VALUE_PROPS = [
  {
    title: 'We Tell You What to Skip',
    description: "Most consultants recommend everything. We tell you what NOT to do—that's often more valuable than what to do.",
    icon: (
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
      </svg>
    ),
  },
  {
    title: 'Three Options, Not One',
    description: 'For each recommendation: off-the-shelf SaaS, best-in-class solution, or custom build. Real pricing for all three.',
    icon: (
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 6h16M4 12h16M4 18h7" />
      </svg>
    ),
  },
  {
    title: 'Week-by-Week Playbook',
    description: 'Not just "what" but "how." Get an implementation timeline with specific tasks, vendors, and expected outcomes.',
    icon: (
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
      </svg>
    ),
  },
]

const HOW_IT_WORKS = [
  {
    step: 1,
    title: 'Take the free quiz',
    description: 'See your AI readiness score and a preview of opportunities.',
    time: '5 min',
  },
  {
    step: 2,
    title: 'Complete the workshop',
    description: 'Deep-dive questions about your operations. Better answers = better report.',
    time: '90 min',
  },
  {
    step: 3,
    title: 'AI analyzes everything',
    description: 'We research your industry, benchmark your operations, and build your report.',
    time: '24-48 hrs',
  },
  {
    step: 4,
    title: 'Get your interactive report',
    description: 'Specific recommendations with real pricing, honest ROI, and clear next steps.',
    time: 'Delivered',
  },
]

const SAMPLE_FINDINGS = [
  {
    title: 'Customer Support Automation',
    verdict: 'Proceed',
    verdictColor: 'green',
    description: 'Your ticket volume and response patterns make this a clear win.',
    potential: '€24,000/year',
    confidence: 'high',
  },
  {
    title: 'AI Content Generation',
    verdict: 'Proceed with Caution',
    verdictColor: 'yellow',
    description: 'Potential is there, but your brand voice needs more definition first.',
    potential: '€8,000/year',
    confidence: 'medium',
  },
  {
    title: 'Predictive Analytics',
    verdict: 'Not Recommended',
    verdictColor: 'gray',
    description: 'Your data infrastructure needs work before this makes sense.',
    potential: 'Deferred',
    confidence: 'high',
  },
]

const REPORT_FEATURES = [
  'AI opportunities tailored to your business',
  'Clear verdicts: Proceed, Caution, Wait, or Skip',
  'Three options per recommendation (DIY, SaaS, Custom)',
  'Live ROI calculator you can adjust',
  'Real vendor pricing from our database',
  'Implementation playbook with week-by-week tasks',
  'Shareable link for your team',
]

const SPRINT_FEATURES = [
  '3x 45-min implementation calls over 2 weeks',
  'We help you set up your #1 AI recommendation',
  'Async support via Slack/email during sprint',
  'Vendor introductions where relevant',
  'Troubleshooting when you get stuck',
  'End-of-sprint review + next steps',
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
            <div className="inline-block px-4 py-1.5 bg-amber-50 text-amber-700 rounded-full text-sm font-medium mb-6">
              For service businesses tired of AI hype
            </div>
            <h1 className="text-4xl sm:text-5xl md:text-6xl font-bold text-gray-900 mb-6 leading-tight">
              Find Out Which AI Tools
              <span className="text-primary-600"> Are Worth It</span>
            </h1>
            <p className="text-xl sm:text-2xl text-gray-600 mb-8 max-w-2xl mx-auto">
              Get an honest analysis with clear verdicts: <span className="font-semibold text-emerald-600">Proceed</span>, <span className="font-semibold text-amber-600">Caution</span>, <span className="font-semibold text-orange-500">Wait</span>, or <span className="font-semibold text-gray-500">Skip</span>.
            </p>

            <div className="flex flex-col sm:flex-row gap-4 justify-center mb-6">
              <button
                onClick={handleQuizStart}
                className="px-8 py-4 bg-primary-600 text-white font-semibold rounded-xl hover:bg-primary-700 transition shadow-lg shadow-primary-600/25 text-lg"
              >
                Take the Free Quiz
                <span className="ml-2">→</span>
              </button>
              <Link
                to="/report/sample"
                className="px-8 py-4 border-2 border-gray-200 text-gray-700 font-semibold rounded-xl hover:border-gray-300 hover:bg-gray-50 transition text-lg"
              >
                See Sample Report
              </Link>
            </div>

            <p className="text-sm text-gray-500 mb-2">
              5-min quiz is free • Full report from €147
            </p>
            <p className="text-xs text-gray-400">
              Built for dental, legal, home services, recruiting, and coaching businesses
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
                <strong>This isn't a magic 5-minute quiz.</strong> Our workshop takes 90 minutes because generic questions = generic answers = useless report.
              </p>
              <p>
                <strong>The quality of your report depends on the quality of your input.</strong> Rush through it, get a rushed report. Take it seriously, get insights worth 100x what you paid.
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
                  finding.verdictColor === 'green' ? 'bg-emerald-100 text-emerald-700' :
                  finding.verdictColor === 'yellow' ? 'bg-amber-100 text-amber-700' :
                  finding.verdictColor === 'orange' ? 'bg-orange-100 text-orange-700' :
                  'bg-gray-100 text-gray-600'
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
              From quick quiz to comprehensive roadmap
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

      {/* What's Inside */}
      <section className="py-20 px-4 bg-gray-50">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              What's inside your report
            </h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              An interactive web report you can share with your team—not a static PDF.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
            {[
              { name: 'Summary', desc: 'AI readiness score + top opportunities at a glance', icon: '📊' },
              { name: 'Findings', desc: 'Each opportunity with honest verdict and reasoning', icon: '🔍' },
              { name: 'Three Options', desc: 'Off-the-shelf, best-in-class, and custom for each', icon: '⚖️' },
              { name: 'ROI Calculator', desc: 'Adjust assumptions and see ROI change in real-time', icon: '🧮' },
              { name: 'Stack Diagram', desc: 'Visual map of your tools + recommended AI layer', icon: '🏗️' },
              { name: 'Playbook', desc: 'Week-by-week implementation tasks you can check off', icon: '✅' },
              { name: 'Industry Insights', desc: 'How your peers are adopting AI in your industry', icon: '📈' },
              { name: 'Roadmap', desc: '3-phase timeline: Quick Wins → Foundation → Transformation', icon: '🗺️' },
            ].map((item, index) => (
              <motion.div
                key={item.name}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4, delay: index * 0.05 }}
                className="bg-white rounded-xl p-5 border border-gray-200 hover:border-primary-300 hover:shadow-md transition"
              >
                <div className="text-2xl mb-2">{item.icon}</div>
                <h3 className="font-semibold text-gray-900 mb-1">{item.name}</h3>
                <p className="text-sm text-gray-600">{item.desc}</p>
              </motion.div>
            ))}
          </div>

          <div className="text-center mt-8">
            <Link
              to="/report/sample"
              className="inline-flex items-center gap-2 text-primary-600 font-medium hover:text-primary-700 transition"
            >
              See a sample report
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </Link>
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section id="pricing" className="py-20 px-4">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              Consultant-quality analysis, software pricing
            </h2>
            <p className="text-lg text-gray-600">
              Start with the report. Add guidance or hands-on help if you need it.
            </p>
          </div>

          {/* Main 2 tiers */}
          <div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">
            {/* Tier 1: Report Only */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
              className="bg-white rounded-3xl p-8 shadow-lg border border-gray-200"
            >
              <div className="text-center mb-6">
                <div className="inline-block px-4 py-1 bg-gray-100 text-gray-700 rounded-full text-sm font-medium mb-4">
                  CRB Report
                </div>
                <div className="flex items-baseline justify-center gap-2 mb-2">
                  <span className="text-4xl font-bold text-gray-900">€147</span>
                  <span className="text-gray-500">one-time</span>
                </div>
                <p className="text-gray-500 text-sm">
                  Self-service analysis
                </p>
              </div>

              <ul className="space-y-3 mb-8">
                {REPORT_FEATURES.map((feature, index) => (
                  <li key={index} className="flex items-start gap-3">
                    <svg className="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    <span className="text-gray-700 text-sm">{feature}</span>
                  </li>
                ))}
              </ul>

              <button
                onClick={handleQuizStart}
                className="w-full py-3 border-2 border-gray-300 text-gray-700 font-semibold rounded-xl hover:border-gray-400 hover:bg-gray-50 transition text-lg"
              >
                Get Started
              </button>
            </motion.div>

            {/* Tier 2: Report + Call */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.1 }}
              className="bg-white rounded-3xl p-8 shadow-xl border-2 border-primary-500 relative"
            >
              <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
                <span className="bg-primary-600 text-white text-sm font-medium px-4 py-1 rounded-full">
                  Most Popular
                </span>
              </div>

              <div className="text-center mb-6">
                <div className="inline-block px-4 py-1 bg-primary-100 text-primary-700 rounded-full text-sm font-medium mb-4">
                  Report + Strategy Call
                </div>
                <div className="flex items-baseline justify-center gap-2 mb-2">
                  <span className="text-4xl font-bold text-gray-900">€497</span>
                  <span className="text-gray-500">one-time</span>
                </div>
                <p className="text-gray-500 text-sm">
                  Expert-guided analysis
                </p>
              </div>

              <ul className="space-y-3 mb-8">
                <li className="text-gray-500 text-xs mb-1">Everything in Report, plus:</li>
                <li className="flex items-start gap-3">
                  <svg className="w-5 h-5 text-primary-600 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  <span className="text-gray-900 font-medium text-sm">60-min strategy call</span>
                </li>
                <li className="flex items-start gap-3">
                  <svg className="w-5 h-5 text-primary-600 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  <span className="text-gray-900 font-medium text-sm">Live Q&A on your situation</span>
                </li>
                <li className="flex items-start gap-3">
                  <svg className="w-5 h-5 text-primary-600 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  <span className="text-gray-900 font-medium text-sm">Priority email support</span>
                </li>
                <li className="flex items-start gap-3">
                  <svg className="w-5 h-5 text-primary-600 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  <span className="text-gray-900 font-medium text-sm">Recording of your call</span>
                </li>
              </ul>

              <button
                onClick={handleQuizStart}
                className="w-full py-3 bg-primary-600 text-white font-semibold rounded-xl hover:bg-primary-700 transition shadow-lg shadow-primary-600/25 text-lg"
              >
                Get Started
              </button>
            </motion.div>
          </div>

          {/* Tier 3: Implementation Sprint - glass minimal */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.3 }}
            className="mt-10 max-w-md mx-auto"
          >
            <div className="relative group cursor-pointer" onClick={handleQuizStart}>
              <div className="backdrop-blur-sm bg-white/40 rounded-2xl p-5 border-2 border-amber-400 shadow-sm hover:bg-white/60 hover:border-amber-500 transition duration-300">
                <div className="flex items-center justify-between gap-6">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-gray-100/80 flex items-center justify-center">
                      <svg className="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                      </svg>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-700">Implementation Sprint</p>
                      <p className="text-xs text-gray-400">2 weeks of hands-on help</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <span className="text-lg font-semibold text-gray-600">€1,997</span>
                    <div className="px-4 py-2 text-sm font-medium text-gray-500 bg-white/50 border border-gray-200/50 rounded-lg group-hover:text-gray-700 group-hover:bg-white/80 transition">
                      Learn more
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </motion.div>

          <p className="text-center text-sm text-gray-500 mt-8">
            14-day money-back guarantee on all options. Choose your tier after completing the quiz.
          </p>
        </div>
      </section>

      {/* Final CTA */}
      <section className="py-20 px-4 bg-gray-900">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="text-3xl font-bold text-white mb-4">
            Stop guessing. Start knowing.
          </h2>
          <p className="text-lg text-gray-400 mb-2">
            Consultants charge €15,000+ for AI assessments. Ours costs €147.
          </p>
          <p className="text-gray-500 mb-8">
            Same methodology. Same depth. No vendor agenda.
          </p>
          <button
            onClick={handleQuizStart}
            className="px-8 py-4 bg-white text-gray-900 font-semibold rounded-xl hover:bg-gray-100 transition text-lg"
          >
            Take the Free Quiz
            <span className="ml-2">→</span>
          </button>
          <p className="text-sm text-gray-500 mt-4">
            5 minutes. No credit card. See your AI readiness score instantly.
          </p>
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
