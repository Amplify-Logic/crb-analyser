import { useMemo } from 'react'
import Chart from 'react-apexcharts'
import { ApexOptions } from 'apexcharts'

interface ValueTimelineChartProps {
  valueSaved: { min: number; max: number }
  valueCreated: { min: number; max: number }
  totalInvestment?: number
  showMilestones?: boolean
}

export default function ValueTimelineChart({
  valueSaved,
  valueCreated,
  totalInvestment = 0,
  showMilestones = true
}: ValueTimelineChartProps) {

  const formatCurrency = (value: number) => {
    if (value >= 1000000) return `€${(value / 1000000).toFixed(1)}M`
    if (value >= 1000) return `€${(value / 1000).toFixed(0)}K`
    return `€${value}`
  }

  // Generate 3-year projection data
  const { data, breakEvenMonth, year1Value, year2Value, year3Value } = useMemo(() => {
    const chartData = []
    const months = 36 // 3 years

    for (let month = 0; month <= months; month += 6) {
      const progress = month / months
      // S-curve adoption: slow start, accelerate, plateau
      const adoption = 1 / (1 + Math.exp(-10 * (progress - 0.3)))

      const savedMin = Math.round((valueSaved.min / 3) * progress * adoption)
      const savedMax = Math.round((valueSaved.max / 3) * progress * adoption)
      const createdMin = Math.round((valueCreated.min / 3) * progress * adoption)
      const createdMax = Math.round((valueCreated.max / 3) * progress * adoption)

      // Investment happens early
      const investmentSpent = month <= 12 ? totalInvestment * (month / 12) : totalInvestment

      chartData.push({
        month,
        label: month === 0 ? 'Now' : `${month}mo`,
        valueSavedMin: savedMin,
        valueSavedMax: savedMax,
        valueCreatedMin: createdMin,
        valueCreatedMax: createdMax,
        totalMin: savedMin + createdMin,
        totalMax: savedMax + createdMax,
        investment: Math.round(investmentSpent),
        netMin: savedMin + createdMin - Math.round(investmentSpent),
        netMax: savedMax + createdMax - Math.round(investmentSpent)
      })
    }

    const breakEven = chartData.find(d => d.netMin > 0)?.month || null
    const y1 = chartData.find(d => d.month === 12)
    const y2 = chartData.find(d => d.month === 24)
    const y3 = chartData.find(d => d.month === 36)

    return {
      data: chartData,
      breakEvenMonth: breakEven,
      year1Value: y1,
      year2Value: y2,
      year3Value: y3
    }
  }, [valueSaved, valueCreated, totalInvestment])

  const series = [
    {
      name: 'Total Value (High)',
      data: data.map(d => d.totalMax)
    },
    {
      name: 'Total Value (Low)',
      data: data.map(d => d.totalMin)
    },
    {
      name: 'Investment',
      data: data.map(d => d.investment)
    }
  ]

  const options: ApexOptions = {
    chart: {
      type: 'area',
      height: 280,
      toolbar: { show: false },
      animations: {
        enabled: true,
        speed: 800,
        animateGradually: {
          enabled: true,
          delay: 150
        },
        dynamicAnimation: {
          enabled: true,
          speed: 350
        }
      },
      fontFamily: 'Inter, system-ui, sans-serif',
      zoom: { enabled: false }
    },
    colors: ['#16a34a', '#22c55e', '#7c3aed'],
    dataLabels: { enabled: false },
    stroke: {
      curve: 'smooth',
      width: [3, 2, 3],
      dashArray: [0, 5, 0]
    },
    fill: {
      type: 'gradient',
      gradient: {
        shadeIntensity: 1,
        opacityFrom: 0.45,
        opacityTo: 0.05,
        stops: [0, 90, 100]
      }
    },
    xaxis: {
      categories: data.map(d => d.label),
      axisBorder: { show: false },
      axisTicks: { show: false },
      labels: {
        style: {
          colors: '#6b7280',
          fontSize: '12px',
          fontWeight: 500
        }
      }
    },
    yaxis: {
      labels: {
        formatter: formatCurrency,
        style: {
          colors: '#6b7280',
          fontSize: '11px'
        }
      }
    },
    grid: {
      borderColor: '#e5e7eb',
      strokeDashArray: 4,
      xaxis: { lines: { show: false } },
      yaxis: { lines: { show: true } },
      padding: { left: 10, right: 10 }
    },
    legend: {
      show: false
    },
    tooltip: {
      theme: 'light',
      x: { show: true },
      y: {
        formatter: (val) => formatCurrency(val)
      },
      style: {
        fontSize: '13px'
      },
      marker: { show: true }
    },
    annotations: breakEvenMonth ? {
      xaxis: [{
        x: `${breakEvenMonth}mo`,
        borderColor: '#7c3aed',
        strokeDashArray: 6,
        label: {
          text: 'Break-even',
          borderColor: '#7c3aed',
          style: {
            color: '#fff',
            background: '#7c3aed',
            fontSize: '11px',
            fontWeight: 600,
            padding: { left: 8, right: 8, top: 4, bottom: 4 }
          }
        }
      }]
    } : undefined
  }

  return (
    <div className="w-full">
      <div className="h-72">
        <Chart
          options={options}
          series={series}
          type="area"
          height="100%"
          width="100%"
        />
      </div>

      {/* Legend */}
      <div className="flex justify-center gap-8 mt-3 text-sm">
        <div className="flex items-center gap-2">
          <div className="w-4 h-1 bg-green-600 rounded-full" />
          <span className="text-gray-600 dark:text-gray-400">Cumulative Value</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-1 bg-purple-600 rounded-full" />
          <span className="text-gray-600 dark:text-gray-400">Investment</span>
        </div>
        {breakEvenMonth && (
          <div className="flex items-center gap-2">
            <div className="w-4 h-0.5 bg-purple-600 border-dashed" style={{ borderTop: '2px dashed #7c3aed' }} />
            <span className="text-gray-600 dark:text-gray-400">Break-even ~{breakEvenMonth}mo</span>
          </div>
        )}
      </div>

      {/* Milestone Summary Boxes */}
      {showMilestones && (
        <div className="grid grid-cols-3 gap-3 mt-6">
          <div className="bg-gray-50 dark:bg-gray-800 rounded-xl p-4 text-center border border-gray-200 dark:border-gray-700 transition-all hover:shadow-md hover:border-gray-300">
            <p className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wide font-medium">Year 1</p>
            <p className="text-xl font-bold text-gray-900 dark:text-white mt-1">
              {formatCurrency(year1Value?.totalMax || 0)}
            </p>
            <p className="text-xs text-gray-500 mt-0.5">value generated</p>
          </div>
          <div className="bg-gray-50 dark:bg-gray-800 rounded-xl p-4 text-center border border-gray-200 dark:border-gray-700 transition-all hover:shadow-md hover:border-gray-300">
            <p className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wide font-medium">Year 2</p>
            <p className="text-xl font-bold text-gray-900 dark:text-white mt-1">
              {formatCurrency(year2Value?.totalMax || 0)}
            </p>
            <p className="text-xs text-gray-500 mt-0.5">cumulative</p>
          </div>
          <div className="bg-gradient-to-br from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20 rounded-xl p-4 text-center border border-green-200 dark:border-green-800 transition-all hover:shadow-md hover:shadow-green-100">
            <p className="text-xs text-green-600 dark:text-green-400 uppercase tracking-wide font-semibold">Year 3</p>
            <p className="text-xl font-bold text-green-700 dark:text-green-300 mt-1">
              {formatCurrency(year3Value?.totalMax || 0)}
            </p>
            <p className="text-xs text-green-600 dark:text-green-400 mt-0.5">total potential</p>
          </div>
        </div>
      )}
    </div>
  )
}
