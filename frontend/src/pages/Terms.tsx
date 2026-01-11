import { Link } from 'react-router-dom'
import { Logo } from '../components/Logo'

export default function Terms() {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-md border-b border-gray-100">
        <div className="max-w-6xl mx-auto px-4 py-4 flex justify-between items-center">
          <Logo size="sm" showIcon={false} />
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
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Terms of Service</h1>
          <p className="text-gray-500 mb-8">Last updated: December 2024</p>

          <div className="bg-white rounded-2xl p-8 shadow-sm border border-gray-100 space-y-8">
            <section>
              <h2 className="text-xl font-semibold text-gray-900 mb-3">1. Agreement to Terms</h2>
              <p className="text-gray-600 leading-relaxed">
                By accessing or using Ready Path ("the Service"), you agree to be bound by these Terms of Service.
                If you disagree with any part of these terms, you may not access the Service.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-gray-900 mb-3">2. Description of Service</h2>
              <p className="text-gray-600 leading-relaxed">
                Ready Path provides AI-powered business analysis and consulting reports. Our service includes:
              </p>
              <ul className="mt-3 space-y-2 text-gray-600">
                <li className="flex items-start gap-2">
                  <span className="text-primary-600 mt-1">-</span>
                  AI-powered assessment of your business processes
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-primary-600 mt-1">-</span>
                  Cost/Risk/Benefit analysis for AI implementation
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-primary-600 mt-1">-</span>
                  Personalized recommendations and implementation roadmaps
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-primary-600 mt-1">-</span>
                  Interactive reports with ROI calculators
                </li>
              </ul>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-gray-900 mb-3">3. Payment Terms</h2>
              <p className="text-gray-600 leading-relaxed">
                We offer multiple tiers of service. All payments are processed securely through Stripe.
                Prices are displayed in Euros and are inclusive of applicable taxes.
              </p>
              <p className="text-gray-600 leading-relaxed mt-3">
                <strong>Refund Policy:</strong> We offer a 14-day money-back guarantee. If you're not satisfied
                with your report, contact us within 14 days of delivery for a full refund.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-gray-900 mb-3">4. User Responsibilities</h2>
              <p className="text-gray-600 leading-relaxed">
                You agree to:
              </p>
              <ul className="mt-3 space-y-2 text-gray-600">
                <li className="flex items-start gap-2">
                  <span className="text-primary-600 mt-1">-</span>
                  Provide accurate and complete information during the assessment
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-primary-600 mt-1">-</span>
                  Not share access credentials with unauthorized parties
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-primary-600 mt-1">-</span>
                  Use the Service only for lawful purposes
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-primary-600 mt-1">-</span>
                  Not attempt to reverse-engineer or copy our analysis methodology
                </li>
              </ul>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-gray-900 mb-3">5. Disclaimer</h2>
              <p className="text-gray-600 leading-relaxed">
                Our reports are based on AI analysis and industry benchmarks. While we strive for accuracy,
                recommendations are advisory in nature. The Service is provided "as is" without warranties
                of any kind. We do not guarantee specific business outcomes or ROI.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-gray-900 mb-3">6. Intellectual Property</h2>
              <p className="text-gray-600 leading-relaxed">
                The Service and its original content, features, and functionality are owned by Ready Path
                and are protected by international copyright, trademark, and other intellectual property laws.
              </p>
              <p className="text-gray-600 leading-relaxed mt-3">
                Your generated reports are yours to use for your business purposes. You may share them with
                your team and advisors.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-gray-900 mb-3">7. Limitation of Liability</h2>
              <p className="text-gray-600 leading-relaxed">
                In no event shall Ready Path be liable for any indirect, incidental, special, consequential,
                or punitive damages, including without limitation, loss of profits, data, use, or goodwill,
                arising out of or in connection with your use of the Service.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-gray-900 mb-3">8. Changes to Terms</h2>
              <p className="text-gray-600 leading-relaxed">
                We reserve the right to modify these terms at any time. We will notify users of any material
                changes via email or through the Service. Your continued use of the Service after such
                modifications constitutes acceptance of the updated terms.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-gray-900 mb-3">9. Contact Us</h2>
              <p className="text-gray-600 leading-relaxed">
                If you have any questions about these Terms, please contact us at{' '}
                <a href="mailto:support@crbanalyser.com" className="text-primary-600 hover:text-primary-700">
                  support@crbanalyser.com
                </a>
              </p>
            </section>
          </div>

          <div className="mt-8 text-center">
            <Link
              to="/privacy"
              className="text-primary-600 hover:text-primary-700 font-medium"
            >
              Read our Privacy Policy
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
