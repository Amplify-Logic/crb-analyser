import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import type { ReactNode } from 'react'
import ROICalculator from './ROICalculator'

type MockProps = {
  children?: ReactNode
}

vi.mock('framer-motion', () => {
  const MockMotion = ({ children }: MockProps) => <div>{children}</div>
  return {
    motion: new Proxy({}, { get: () => MockMotion }),
    AnimatePresence: ({ children }: MockProps) => <>{children}</>,
  }
})

vi.mock('recharts', () => {
  const MockChart = ({ children }: MockProps) => <div>{children}</div>
  return {
    ResponsiveContainer: MockChart,
    BarChart: MockChart,
    Bar: MockChart,
    XAxis: MockChart,
    YAxis: MockChart,
    CartesianGrid: MockChart,
    Tooltip: MockChart,
    Cell: MockChart,
  }
})

describe('ROICalculator', () => {
  it('calculates first-year ROI using implementation plus yearly ongoing costs', () => {
    const recommendations = [
      {
        id: 'rec-1',
        title: 'Automate support routing',
        priority: 'high' as const,
        roi_percentage: 0,
        payback_months: 0,
        crb_analysis: {
          cost: { short_term: 0, mid_term: 0, long_term: 0, total: 1200 },
          risk: [],
          benefit: { short_term: 0, mid_term: 0, long_term: 0, total: 0 },
        },
        options: {
          enhance_with_ai: {
            monthly_cost: 100,
            implementation_weeks: 1,
          },
        },
        our_recommendation: 'enhance_with_ai',
        assumptions: [],
      },
    ]

    render(
      <ROICalculator
        recommendations={recommendations}
        valueSummary={{
          value_saved: { subtotal: { min: 0, max: 0 }, hours_per_week: 10, hourly_rate: 100 },
          value_created: { subtotal: { min: 0, max: 0 } },
          total: { min: 0, max: 0 },
        }}
        locale="en-NZ"
        currency="NZD"
      />
    )

    expect(screen.getByText('1466%')).toBeInTheDocument()
    expect(screen.queryByText('999+%')).not.toBeInTheDocument()
    expect(screen.getByText('0.4 mo')).toBeInTheDocument()
  })

  it('shows no payback when monthly net savings are negative', () => {
    const recommendations = [
      {
        id: 'rec-2',
        title: 'Expensive platform migration',
        priority: 'high' as const,
        roi_percentage: 0,
        payback_months: 0,
        crb_analysis: {
          cost: { short_term: 0, mid_term: 0, long_term: 0, total: 1000 },
          risk: [],
          benefit: { short_term: 0, mid_term: 0, long_term: 0, total: 0 },
        },
        options: {
          enhance_with_ai: {
            monthly_cost: 2000,
            implementation_weeks: 2,
          },
        },
        our_recommendation: 'enhance_with_ai',
        assumptions: [],
      },
    ]

    render(
      <ROICalculator
        recommendations={recommendations}
        valueSummary={{
          value_saved: { subtotal: { min: 0, max: 0 }, hours_per_week: 1, hourly_rate: 20 },
          value_created: { subtotal: { min: 0, max: 0 } },
          total: { min: 0, max: 0 },
        }}
        locale="en-NZ"
        currency="NZD"
      />
    )

    expect(screen.getByText('No payback')).toBeInTheDocument()
  })
})
