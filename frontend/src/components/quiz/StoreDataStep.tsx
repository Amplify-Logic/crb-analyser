import { useState } from 'react'
import { motion } from 'framer-motion'

interface StoreMetrics {
  monthly_revenue: string
  average_order_value: string
  cart_abandonment_rate: string
  repeat_customer_rate: string
  email_list_size: string
}

interface StoreDataStepProps {
  currency: string
  onComplete: (data: {
    source: 'manual_entry' | 'skip'
    store_metrics: StoreMetrics
  }) => void
  onBack: () => void
}

const EMPTY_METRICS: StoreMetrics = {
  monthly_revenue: '',
  average_order_value: '',
  cart_abandonment_rate: '',
  repeat_customer_rate: '',
  email_list_size: '',
}

export default function StoreDataStep({ currency, onComplete, onBack }: StoreDataStepProps) {
  const [mode, setMode] = useState<'choose' | 'manual'>('choose')
  const [metrics, setMetrics] = useState<StoreMetrics>(EMPTY_METRICS)

  const currencySymbol = currency === 'USD' ? '$' : currency === 'GBP' ? '£' : '€'

  const handleSkip = () => {
    onComplete({ source: 'skip', store_metrics: EMPTY_METRICS })
  }

  const handleManualSubmit = () => {
    onComplete({ source: 'manual_entry', store_metrics: metrics })
  }

  const updateMetric = (field: keyof StoreMetrics, value: string) => {
    setMetrics(prev => ({ ...prev, [field]: value }))
  }

  const hasAnyData = Object.values(metrics).some(v => v.trim() !== '')

  if (mode === 'choose') {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="max-w-lg mx-auto space-y-4"
      >
        <div className="text-center mb-8">
          <h2 className="text-2xl font-semibold text-stone-800 mb-2">
            Personalise your analysis
          </h2>
          <p className="text-stone-500">
            Real numbers make your report dramatically more specific.
          </p>
        </div>

        {/* Option 1: Connect (coming soon) */}
        <div className="relative rounded-xl border border-stone-200 bg-stone-50 p-5 opacity-60 cursor-not-allowed">
          <div className="absolute top-3 right-3 text-xs font-medium text-stone-400 bg-stone-100 px-2 py-0.5 rounded-full">
            Coming soon
          </div>
          <div className="flex items-start gap-3">
            <span className="text-xl mt-0.5">&#x26A1;</span>
            <div>
              <h3 className="font-medium text-stone-600">Connect your store</h3>
              <p className="text-sm text-stone-400 mt-0.5">
                Automatic, read-only. Takes 10 seconds.
              </p>
            </div>
          </div>
        </div>

        {/* Option 2: Manual entry */}
        <button
          onClick={() => setMode('manual')}
          className="w-full text-left rounded-xl border-2 border-amber-200 bg-amber-50/50 p-5 hover:border-amber-300 hover:bg-amber-50 transition-all"
        >
          <div className="flex items-start gap-3">
            <span className="text-xl mt-0.5">&#x1F4CA;</span>
            <div>
              <h3 className="font-medium text-stone-800">Enter your numbers</h3>
              <p className="text-sm text-stone-500 mt-0.5">
                5 quick fields from your dashboard. Takes 2 minutes.
              </p>
            </div>
          </div>
        </button>

        {/* Option 3: Skip */}
        <button
          onClick={handleSkip}
          className="w-full text-left rounded-xl border border-stone-200 p-5 hover:bg-stone-50 transition-all"
        >
          <div className="flex items-start gap-3">
            <span className="text-xl mt-0.5">&#x23ED;&#xFE0F;</span>
            <div>
              <h3 className="font-medium text-stone-600">Skip for now</h3>
              <p className="text-sm text-stone-400 mt-0.5">
                We'll use industry benchmarks instead. You can add data later.
              </p>
            </div>
          </div>
        </button>

        <button
          onClick={onBack}
          className="mt-4 text-sm text-stone-400 hover:text-stone-600 transition-colors"
        >
          &larr; Back
        </button>
      </motion.div>
    )
  }

  // Manual entry form
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="max-w-lg mx-auto"
    >
      <div className="text-center mb-8">
        <h2 className="text-2xl font-semibold text-stone-800 mb-2">
          Your store numbers
        </h2>
        <p className="text-stone-500 text-sm">
          Leave any field blank if you don't know — we'll use benchmarks for those.
        </p>
      </div>

      <div className="space-y-5">
        <MetricField
          label="Monthly revenue"
          prefix={currencySymbol}
          placeholder="25,000"
          value={metrics.monthly_revenue}
          onChange={v => updateMetric('monthly_revenue', v)}
        />
        <MetricField
          label="Average order value"
          prefix={currencySymbol}
          placeholder="65"
          value={metrics.average_order_value}
          onChange={v => updateMetric('average_order_value', v)}
        />
        <MetricField
          label="Cart abandonment rate"
          suffix="%"
          placeholder="70"
          value={metrics.cart_abandonment_rate}
          onChange={v => updateMetric('cart_abandonment_rate', v)}
          hint="Check Shopify Analytics → Overview"
        />
        <MetricField
          label="Repeat customer rate"
          suffix="%"
          placeholder="25"
          value={metrics.repeat_customer_rate}
          onChange={v => updateMetric('repeat_customer_rate', v)}
        />
        <MetricField
          label="Email list size"
          placeholder="8,500"
          value={metrics.email_list_size}
          onChange={v => updateMetric('email_list_size', v)}
          hint="Check Klaviyo / Mailchimp subscribers"
        />
      </div>

      <div className="flex items-center justify-between mt-8">
        <button
          onClick={() => setMode('choose')}
          className="text-sm text-stone-400 hover:text-stone-600 transition-colors"
        >
          &larr; Back
        </button>
        <div className="flex gap-3">
          <button
            onClick={handleSkip}
            className="px-4 py-2 text-sm text-stone-400 hover:text-stone-600 transition-colors"
          >
            Skip instead
          </button>
          <button
            onClick={handleManualSubmit}
            disabled={!hasAnyData}
            className="px-6 py-2.5 bg-amber-600 text-white rounded-lg font-medium hover:bg-amber-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            Continue
          </button>
        </div>
      </div>
    </motion.div>
  )
}


// --- Internal component ---

function MetricField({
  label,
  prefix,
  suffix,
  placeholder,
  value,
  onChange,
  hint,
}: {
  label: string
  prefix?: string
  suffix?: string
  placeholder: string
  value: string
  onChange: (v: string) => void
  hint?: string
}) {
  return (
    <div>
      <label className="block text-sm font-medium text-stone-700 mb-1.5">
        {label}
      </label>
      <div className="flex items-center">
        {prefix && (
          <span className="text-stone-400 text-sm mr-2">{prefix}</span>
        )}
        <input
          type="text"
          inputMode="decimal"
          placeholder={placeholder}
          value={value}
          onChange={e => onChange(e.target.value.replace(/[^0-9.,]/g, ''))}
          className="flex-1 px-3 py-2.5 border border-stone-200 rounded-lg text-stone-800 placeholder:text-stone-300 focus:outline-none focus:ring-2 focus:ring-amber-200 focus:border-amber-300 transition-all"
        />
        {suffix && (
          <span className="text-stone-400 text-sm ml-2">{suffix}</span>
        )}
      </div>
      {hint && (
        <p className="text-xs text-stone-400 mt-1">{hint}</p>
      )}
    </div>
  )
}
