interface UpgradeCTAProps {
  currentTier: 'quick' | 'full'
  reportId: string
}

export default function UpgradeCTA({ currentTier, reportId }: UpgradeCTAProps) {
  const upgradePrice = currentTier === 'quick' ? 350 : 0 // €497 - €147 = €350

  if (upgradePrice === 0) return null

  return (
    <section className="mt-12 pt-8 border-t border-gray-200 dark:border-gray-700">
      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6 md:p-8 text-center">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
          Ready to Move Forward?
        </h2>
        <p className="text-gray-600 dark:text-gray-400 mb-6 max-w-lg mx-auto">
          Add a 60-minute strategy call to review your results and create an action plan with a CRB specialist.
        </p>

        <a
          href={`/checkout/upgrade?report=${reportId}&tier=call`}
          className="inline-flex items-center gap-2 px-6 py-3 bg-primary-600 hover:bg-primary-700 text-white rounded-xl font-medium transition-colors shadow-lg shadow-primary-500/25"
        >
          Add Strategy Call
        </a>

        <div className="mt-6 pt-6 border-t border-gray-200 dark:border-gray-700">
          <p className="text-sm text-gray-500 dark:text-gray-400 mb-2">
            Need implementation help?
          </p>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            We can connect you with vetted partners who specialize in your industry.
          </p>
          <span className="inline-block mt-2 text-xs text-gray-400 bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded">
            Coming soon
          </span>
        </div>
      </div>
    </section>
  )
}
