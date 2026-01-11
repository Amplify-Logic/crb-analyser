interface ValueSummaryProps {
  investment: number
  returnMin: number
  returnMax: number
}

export default function ValueSummary({ investment, returnMin, returnMax }: ValueSummaryProps) {
  const formatCurrency = (value: number) =>
    new Intl.NumberFormat('de-DE', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }).format(value)

  const roi = investment > 0 ? Math.round(((returnMin + returnMax) / 2) / investment) : 0

  return (
    <div className="bg-gradient-to-r from-primary-50 to-green-50 dark:from-primary-900/20 dark:to-green-900/20 rounded-xl p-6 border border-primary-200 dark:border-primary-800/30">
      <div className="flex flex-col md:flex-row items-center justify-center gap-6 md:gap-12 text-center">
        <div>
          <p className="text-sm font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-1">
            Your Investment
          </p>
          <p className="text-2xl md:text-3xl font-bold text-gray-900 dark:text-white">
            {formatCurrency(investment)}
          </p>
          <p className="text-xs text-gray-500">first year</p>
        </div>

        <div className="text-3xl text-primary-400">→</div>

        <div>
          <p className="text-sm font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-1">
            Your Return
          </p>
          <p className="text-2xl md:text-3xl font-bold text-green-600 dark:text-green-400">
            {formatCurrency(returnMin)} - {formatCurrency(returnMax)}
          </p>
          <p className="text-xs text-gray-500">3-year value</p>
        </div>
      </div>

      <div className="mt-4 pt-4 border-t border-primary-200 dark:border-primary-800/30 text-center">
        <span className="text-lg font-semibold text-primary-700 dark:text-primary-300">
          {roi}x ROI
        </span>
      </div>
    </div>
  )
}
