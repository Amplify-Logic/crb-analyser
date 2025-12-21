import { Link } from 'react-router-dom'

export default function Privacy() {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-md border-b border-gray-100">
        <div className="max-w-6xl mx-auto px-4 py-4 flex justify-between items-center">
          <Link to="/" className="text-xl font-bold text-gray-900">
            CRB<span className="text-primary-600">Analyser</span>
          </Link>
          <Link
            to="/"
            className="text-gray-600 hover:text-gray-900 transition"
          >
            Back to Home
          </Link>
        </div>
      </nav>

      {/* Content */}
      <div className="pt-24 pb-20 px-4">
        <div className="max-w-3xl mx-auto">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Privacy Policy</h1>
          <p className="text-gray-500 mb-8">Last updated: December 2024</p>

          <div className="bg-white rounded-2xl p-8 shadow-sm border border-gray-100 space-y-8">
            <section>
              <h2 className="text-xl font-semibold text-gray-900 mb-3">1. Introduction</h2>
              <p className="text-gray-600 leading-relaxed">
                CRB Analyser ("we", "our", or "us") respects your privacy and is committed to protecting your
                personal data. This privacy policy explains how we collect, use, and safeguard your information
                when you use our service.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-gray-900 mb-3">2. Information We Collect</h2>
              <p className="text-gray-600 leading-relaxed mb-3">
                We collect information you provide directly to us:
              </p>
              <ul className="space-y-2 text-gray-600">
                <li className="flex items-start gap-2">
                  <span className="text-primary-600 mt-1">-</span>
                  <strong>Account Information:</strong> Email address, name (optional), company name
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-primary-600 mt-1">-</span>
                  <strong>Business Information:</strong> Company details, processes, and operational data you share during the assessment
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-primary-600 mt-1">-</span>
                  <strong>Payment Information:</strong> Processed securely through Stripe - we do not store card details
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-primary-600 mt-1">-</span>
                  <strong>Interview Data:</strong> Your responses during the AI interview (text and/or voice)
                </li>
              </ul>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-gray-900 mb-3">3. How We Use Your Information</h2>
              <p className="text-gray-600 leading-relaxed mb-3">
                We use your information to:
              </p>
              <ul className="space-y-2 text-gray-600">
                <li className="flex items-start gap-2">
                  <span className="text-primary-600 mt-1">-</span>
                  Generate your personalized CRB analysis report
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-primary-600 mt-1">-</span>
                  Improve our AI models and recommendations (aggregated, anonymized data only)
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-primary-600 mt-1">-</span>
                  Send you your report and relevant updates
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-primary-600 mt-1">-</span>
                  Process payments and prevent fraud
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-primary-600 mt-1">-</span>
                  Respond to your questions and provide support
                </li>
              </ul>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-gray-900 mb-3">4. Data Sharing</h2>
              <p className="text-gray-600 leading-relaxed">
                We do not sell your personal data. We share information only with:
              </p>
              <ul className="mt-3 space-y-2 text-gray-600">
                <li className="flex items-start gap-2">
                  <span className="text-primary-600 mt-1">-</span>
                  <strong>Stripe:</strong> For payment processing
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-primary-600 mt-1">-</span>
                  <strong>Anthropic (Claude AI):</strong> For AI-powered analysis (no personal data retained)
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-primary-600 mt-1">-</span>
                  <strong>Supabase:</strong> For secure data storage
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-primary-600 mt-1">-</span>
                  <strong>SendGrid:</strong> For email delivery
                </li>
              </ul>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-gray-900 mb-3">5. AI and Machine Learning</h2>
              <p className="text-gray-600 leading-relaxed">
                We use AI (specifically Anthropic's Claude) to analyze your business information and generate recommendations.
              </p>
              <ul className="mt-3 space-y-2 text-gray-600">
                <li className="flex items-start gap-2">
                  <span className="text-primary-600 mt-1">-</span>
                  Your data is processed in real-time and not stored by the AI provider
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-primary-600 mt-1">-</span>
                  We may use aggregated, anonymized patterns to improve our service
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-primary-600 mt-1">-</span>
                  Your individual business data is never used to train AI models
                </li>
              </ul>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-gray-900 mb-3">6. Data Security</h2>
              <p className="text-gray-600 leading-relaxed">
                We implement industry-standard security measures:
              </p>
              <ul className="mt-3 space-y-2 text-gray-600">
                <li className="flex items-start gap-2">
                  <span className="text-primary-600 mt-1">-</span>
                  All data is encrypted in transit (HTTPS/TLS) and at rest
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-primary-600 mt-1">-</span>
                  Database access is restricted and monitored
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-primary-600 mt-1">-</span>
                  Regular security audits and updates
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-primary-600 mt-1">-</span>
                  Row-level security policies in our database
                </li>
              </ul>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-gray-900 mb-3">7. Data Retention</h2>
              <p className="text-gray-600 leading-relaxed">
                We retain your data as follows:
              </p>
              <ul className="mt-3 space-y-2 text-gray-600">
                <li className="flex items-start gap-2">
                  <span className="text-primary-600 mt-1">-</span>
                  <strong>Reports:</strong> Indefinitely (for your continued access)
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-primary-600 mt-1">-</span>
                  <strong>Interview transcripts:</strong> 90 days after report generation
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-primary-600 mt-1">-</span>
                  <strong>Voice recordings:</strong> Deleted immediately after transcription
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-primary-600 mt-1">-</span>
                  <strong>Incomplete quiz data:</strong> 30 days
                </li>
              </ul>
              <p className="text-gray-600 leading-relaxed mt-3">
                You can request deletion of your data at any time by contacting us.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-gray-900 mb-3">8. Your Rights (GDPR)</h2>
              <p className="text-gray-600 leading-relaxed mb-3">
                If you are in the European Economic Area, you have the right to:
              </p>
              <ul className="space-y-2 text-gray-600">
                <li className="flex items-start gap-2">
                  <span className="text-primary-600 mt-1">-</span>
                  <strong>Access:</strong> Request a copy of your personal data
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-primary-600 mt-1">-</span>
                  <strong>Rectification:</strong> Correct inaccurate data
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-primary-600 mt-1">-</span>
                  <strong>Erasure:</strong> Request deletion of your data
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-primary-600 mt-1">-</span>
                  <strong>Portability:</strong> Receive your data in a structured format
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-primary-600 mt-1">-</span>
                  <strong>Object:</strong> Object to processing for marketing purposes
                </li>
              </ul>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-gray-900 mb-3">9. Cookies</h2>
              <p className="text-gray-600 leading-relaxed">
                We use essential cookies only:
              </p>
              <ul className="mt-3 space-y-2 text-gray-600">
                <li className="flex items-start gap-2">
                  <span className="text-primary-600 mt-1">-</span>
                  <strong>Session cookies:</strong> To keep you logged in
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-primary-600 mt-1">-</span>
                  <strong>Local storage:</strong> To save your quiz progress
                </li>
              </ul>
              <p className="text-gray-600 leading-relaxed mt-3">
                We do not use tracking or advertising cookies.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-gray-900 mb-3">10. Changes to This Policy</h2>
              <p className="text-gray-600 leading-relaxed">
                We may update this privacy policy from time to time. We will notify you of any changes by
                posting the new policy on this page and updating the "Last updated" date.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-gray-900 mb-3">11. Contact Us</h2>
              <p className="text-gray-600 leading-relaxed">
                For any questions about this privacy policy or your data, contact us at:{' '}
                <a href="mailto:privacy@crbanalyser.com" className="text-primary-600 hover:text-primary-700">
                  privacy@crbanalyser.com
                </a>
              </p>
            </section>
          </div>

          <div className="mt-8 text-center">
            <Link
              to="/terms"
              className="text-primary-600 hover:text-primary-700 font-medium"
            >
              Read our Terms of Service
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
