interface DataQualityBadgeProps {
  completeness: number
  completenessLabel: string
}

export default function DataQualityBadge({ completeness, completenessLabel }: DataQualityBadgeProps) {
  const pct = Math.round(completeness * 100)

  const barColor = completeness >= 0.7
    ? 'bg-emerald-400'
    : completeness >= 0.3
    ? 'bg-amber-400'
    : 'bg-stone-300'

  const textColor = completeness >= 0.7
    ? 'text-emerald-700'
    : completeness >= 0.3
    ? 'text-amber-700'
    : 'text-stone-500'

  return (
    <div className="px-4 py-3 border-b border-stone-100">
      <div className="flex items-center justify-between mb-1.5">
        <span className="text-xs font-medium text-stone-500">Data quality</span>
        <span className={`text-xs font-medium ${textColor}`}>{pct}%</span>
      </div>
      <div className="w-full h-1.5 bg-stone-100 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all ${barColor}`}
          style={{ width: `${Math.max(pct, 4)}%` }}
        />
      </div>
      <p className="text-[11px] text-stone-400 mt-1.5">
        Based on {completenessLabel}
      </p>
    </div>
  )
}
