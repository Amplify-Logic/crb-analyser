import { Link, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { ShimmerButton, AnimatedGradientText, SpotlightCard } from '../components/magicui'
import { Logo } from '../components/Logo'

const VALUE_PROPS = [
  {
    title: 'We Tell You What to Skip',
    description: "Half of AI tools aren't worth your time. We'll tell you which half.",
    icon: (
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
      </svg>
    ),
  },
  {
    title: 'Real Prices, Not Ranges',
    description: 'Market-rate vendor pricing. Realistic implementation costs. No "it depends" handwaving.',
    icon: (
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 6h16M4 12h16M4 18h7" />
      </svg>
    ),
  },
  {
    title: 'Week-by-Week Playbook',
    description: 'Exactly what to do, when, and who to call. Not a "strategic framework."',
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
    title: 'Quick quiz',
    description: 'Answer 7 questions. Get your AI readiness score.',
    time: '5 min',
  },
  {
    step: 2,
    title: 'Deep dive',
    description: 'Tell us how your business actually works. The more detail, the better your report.',
    time: '90 min',
  },
  {
    step: 3,
    title: 'We do the work',
    description: 'AI analyzes your answers against industry data and vendor pricing.',
    time: '24-48 hrs',
  },
  {
    step: 4,
    title: 'Your roadmap',
    description: 'Clear verdicts. Real numbers. Specific next steps.',
    time: 'Done',
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
    verdict: 'Skip',
    verdictColor: 'gray',
    description: 'Your data infrastructure needs work before this makes sense.',
    potential: 'Deferred',
    confidence: 'high',
  },
]

const REPORT_FEATURES = [
  '10-15 AI opportunities analyzed',
  'Clear verdict on each: Proceed, Wait, or Skip',
  '3 options per recommendation with real pricing',
  'ROI calculator you can adjust',
  'Week-by-week implementation playbook',
  'Shareable link for your team',
]

export default function Landing() {
  const navigate = useNavigate()

  const handleQuizStart = () => {
    navigate('/quiz?new=true')
  }

  return (
    <div className="min-h-screen bg-white selection:bg-primary-100 selection:text-primary-900">
      {/* Navigation - Glass effect */}
      <nav className="fixed top-0 left-0 right-0 z-50 transition-all duration-300 bg-white/70 backdrop-blur-md border-b border-white/20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-4 flex justify-between items-center">
          <Logo size="sm" />
          <div className="flex items-center gap-6">
            <Link to="/login" className="text-sm font-medium text-gray-600 hover:text-gray-900 transition hidden sm:block">
              Sign In
            </Link>
            <button
              onClick={handleQuizStart}
              className="px-5 py-2.5 bg-gray-900 text-white font-medium rounded-xl hover:bg-black transition-all hover:scale-105 shadow-lg shadow-gray-200"
            >
              Take Free Quiz
            </button>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative pt-36 pb-20 sm:pt-44 sm:pb-32 px-4 overflow-hidden">
        {/* Abstract Background Elements */}
        <div className="absolute top-0 left-0 w-full h-full bg-mesh-light opacity-60 -z-10" />
        <div className="absolute top-20 right-0 w-96 h-96 bg-primary-200/30 rounded-full blur-3xl animate-float opacity-50" />
        <div className="absolute bottom-0 left-10 w-72 h-72 bg-blue-200/30 rounded-full blur-3xl animate-float" style={{ animationDelay: '1s' }} />

        <div className="max-w-5xl mx-auto text-center relative z-10">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
          >
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-white/60 backdrop-blur-sm border border-primary-100 rounded-full text-sm font-medium text-primary-700 mb-8 shadow-sm animate-fade-in-up">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-primary-500"></span>
              </span>
              Know exactly where AI fits.
            </div>

            <h1 className="text-5xl sm:text-6xl md:text-7xl font-bold text-gray-900 mb-8 leading-[1.15] tracking-tight">
              Should you invest in AI?
              <br />
              <AnimatedGradientText className="text-5xl sm:text-6xl md:text-7xl font-bold">
                We'll tell you.
              </AnimatedGradientText>
            </h1>

            <p className="text-xl text-gray-600 mb-10 max-w-2xl mx-auto leading-relaxed text-balance">
              Get a report that tells you exactly which AI tools make sense for your business, and which ones don't. With real prices, real ROI, and a week-by-week plan.
            </p>

            <div className="flex flex-col sm:flex-row gap-4 justify-center items-center mb-12">
              <ShimmerButton
                onClick={handleQuizStart}
                className="text-lg"
                shimmerColor="#ffffff"
                background="linear-gradient(135deg, #7c3aed 0%, #6366f1 50%, #8b5cf6 100%)"
              >
                Take the Free Quiz
                <span className="ml-2 inline-block transition-transform group-hover:translate-x-1">→</span>
              </ShimmerButton>
              <Link
                to="/report/sample"
                className="px-8 py-4 bg-white border-2 border-gray-200 rounded-xl font-semibold text-gray-700 hover:border-primary-300 hover:text-primary-700 hover:bg-primary-50 transition-all flex items-center gap-2 shadow-sm hover:shadow-md"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                See Sample Report
              </Link>
            </div>

            <div className="flex flex-wrap justify-center gap-x-8 gap-y-4 text-sm text-gray-500">
              <span className="flex items-center gap-2">
                <svg className="w-5 h-5 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                Free 5-min Analysis
              </span>
              <span className="flex items-center gap-2">
                <svg className="w-5 h-5 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                No Credit Card Required
              </span>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Value Props - Spotlight Cards */}
      <section className="py-20 bg-white relative">
        <div className="max-w-6xl mx-auto px-4">
          <div className="grid md:grid-cols-3 gap-8">
            {VALUE_PROPS.map((prop, index) => (
              <motion.div
                key={prop.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
              >
                <SpotlightCard className="group h-full p-8 hover:shadow-card-hover transition-all duration-300">
                  <div className="inline-flex items-center justify-center w-14 h-14 bg-gradient-to-br from-primary-50 to-primary-100 text-primary-600 rounded-2xl mb-6 shadow-sm border border-primary-100/50 group-hover:scale-110 group-hover:shadow-glow-primary transition-all duration-300">
                    {prop.icon}
                  </div>
                  <h3 className="text-xl font-bold text-gray-900 mb-3">{prop.title}</h3>
                  <p className="text-gray-600 leading-relaxed">{prop.description}</p>
                </SpotlightCard>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Sample Findings - Interactive feel */}
      <section className="py-24 px-4 bg-gray-50/50 border-y border-gray-100 relative overflow-hidden">
        <div className="absolute inset-0 bg-mesh-light opacity-30" />
        <div className="max-w-6xl mx-auto relative z-10">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-6">
              What you actually get
            </h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              Not vague advice. Specific verdicts on specific opportunities, with the reasoning behind each one.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-6">
            {SAMPLE_FINDINGS.map((finding, index) => (
              <motion.div
                key={finding.title}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100 hover:shadow-lg transition-all duration-300 hover:-translate-y-1"
              >
                <div className={`inline-block px-3 py-1 text-xs font-semibold uppercase tracking-wide rounded-full mb-4 ${finding.verdictColor === 'green' ? 'bg-emerald-50 text-emerald-700 border border-emerald-100' :
                  finding.verdictColor === 'yellow' ? 'bg-amber-50 text-amber-700 border border-amber-100' :
                    'bg-gray-100 text-gray-600'
                  }`}>
                  {finding.verdict}
                </div>
                <h3 className="font-bold text-gray-900 mb-2 text-lg">{finding.title}</h3>
                <p className="text-sm text-gray-600 mb-6 leading-relaxed">{finding.description}</p>
                <div className="pt-4 border-t border-gray-50 flex justify-between items-center">
                  <span className={`font-bold ${finding.potential === 'Deferred' ? 'text-gray-400' : 'text-emerald-600'
                    }`}>
                    {finding.potential}
                  </span>
                  <span className="text-xs text-gray-400 font-medium uppercase tracking-wider">{finding.confidence} confidence</span>
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
              The process
            </h2>
            <p className="text-lg text-gray-600">
              Four steps. One report. Zero guesswork.
            </p>
          </div>

          <div className="grid md:grid-cols-4 gap-6">
            {HOW_IT_WORKS.map((item, index) => (
              <motion.div
                key={item.step}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                className="text-center"
              >
                <div className="inline-flex items-center justify-center w-12 h-12 bg-primary-600 text-white rounded-full text-xl font-bold mb-4 shadow-lg shadow-primary-500/20">
                  {item.step}
                </div>
                <div className="text-xs font-medium text-primary-600 mb-2 uppercase tracking-wide">{item.time}</div>
                <h3 className="text-lg font-bold text-gray-900 mb-2">
                  {item.title}
                </h3>
                <p className="text-gray-600 text-sm leading-relaxed">
                  {item.description}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* What's Inside */}
      <section className="py-24 px-4 bg-gray-50">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              Inside your report
            </h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              An interactive report you can share with your team. Not a 50-page PDF that sits in a folder.
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
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.4, delay: index * 0.05 }}
                className="bg-white rounded-xl p-6 border border-gray-200 hover:border-primary-300 hover:shadow-lg hover:-translate-y-1 transition-all duration-300"
              >
                <div className="text-3xl mb-4">{item.icon}</div>
                <h3 className="font-bold text-gray-900 mb-2">{item.name}</h3>
                <p className="text-sm text-gray-600 leading-relaxed">{item.desc}</p>
              </motion.div>
            ))}
          </div>

          <div className="text-center mt-12">
            <Link
              to="/report/sample"
              className="inline-flex items-center gap-2 text-primary-600 font-bold hover:text-primary-700 transition"
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
      <section id="pricing" className="py-24 px-4 bg-white">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              Simple Pricing
            </h2>
            <p className="text-lg text-gray-600">
              Consultants charge €15,000+ for this. We charge €147.
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">
            {/* Tier 1 */}
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              className="bg-gray-50 rounded-3xl p-8 border border-gray-100 hover:border-gray-200 transition-colors"
            >
              <div className="mb-8">
                <h3 className="text-xl font-bold text-gray-900 mb-2">Readiness Report</h3>
                <div className="flex items-baseline gap-2 mb-4">
                  <span className="text-4xl font-bold text-gray-900">€147</span>
                  <span className="text-gray-500">one-time</span>
                </div>
                <p className="text-gray-600 text-sm">Everything you need to make the decision yourself.</p>
              </div>
              <ul className="space-y-4 mb-8">
                {REPORT_FEATURES.map((feature, i) => (
                  <li key={i} className="flex items-start gap-3">
                    <div className="mt-1 w-5 h-5 rounded-full bg-emerald-100 flex items-center justify-center shrink-0">
                      <svg className="w-3 h-3 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                      </svg>
                    </div>
                    <span className="text-gray-700 text-sm">{feature}</span>
                  </li>
                ))}
              </ul>
              <button onClick={handleQuizStart} className="w-full py-4 rounded-xl border-2 border-gray-200 text-gray-900 font-semibold hover:border-gray-300 hover:bg-gray-100 transition-all">
                Get Report
              </button>
            </motion.div>

            {/* Tier 2 - Premium with animated glow */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              className="bg-white rounded-3xl p-8 border-2 border-primary-400 shadow-premium relative transform hover:-translate-y-1 transition-all duration-300 hover:shadow-glow-primary hover:border-primary-500"
            >
              <div className="absolute -top-4 left-1/2 -translate-x-1/2 bg-gradient-to-r from-primary-600 to-indigo-600 text-white px-4 py-1.5 rounded-full text-sm font-bold shadow-lg shadow-primary-500/30 animate-pulse-slow">
                Most Popular
              </div>

              <div className="mb-8">
                <h3 className="text-xl font-bold text-gray-900 mb-2">Report + Strategy Call</h3>
                <div className="flex items-baseline gap-2 mb-4">
                  <span className="text-4xl font-bold text-gray-900">€497</span>
                  <span className="text-gray-500">one-time</span>
                </div>
                <p className="text-gray-600 text-sm">For those who want an expert second opinion.</p>
              </div>

              <div className="space-y-4 mb-8 border-t border-b border-gray-100 py-6">
                <div className="text-xs font-semibold text-primary-600 uppercase tracking-wide mb-2">Everything in Report, plus:</div>
                {[
                  '60-minute call with an AI Systems Specialist',
                  'Live Q&A on your specific situation',
                  'Priority email support',
                  'Recording of your session'
                ].map((item, i) => (
                  <li key={i} className="flex items-start gap-3 list-none">
                    <div className="mt-1 w-5 h-5 rounded-full bg-primary-100 flex items-center justify-center shrink-0">
                      <svg className="w-3 h-3 text-primary-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                      </svg>
                    </div>
                    <span className="text-gray-900 font-medium text-sm">{item}</span>
                  </li>
                ))}
              </div>

              <button onClick={handleQuizStart} className="w-full py-4 rounded-xl bg-gradient-to-r from-primary-600 to-indigo-600 text-white font-bold shadow-lg shadow-primary-500/25 hover:shadow-primary-500/40 transition-all hover:scale-[1.02]">
                Get Started
              </button>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 bg-white border-t border-gray-100">
        <div className="max-w-6xl mx-auto px-4 flex flex-col md:flex-row justify-between items-center gap-6">
          <Logo size="sm" showIcon={false} linkToHome={false} />
          <div className="text-sm text-gray-500">
            © 2026 Ready Path. No BS, just clarity.
          </div>
          <div className="flex gap-6 text-sm text-gray-500">
            <Link to="/privacy" className="hover:text-gray-900 transition">Privacy</Link>
            <Link to="/terms" className="hover:text-gray-900 transition">Terms</Link>
          </div>
        </div>
      </footer>
    </div>
  )
}
