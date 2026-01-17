/**
 * Admin Dashboard
 *
 * Central admin hub with overview stats and quick actions.
 * Links to: Vendors, Knowledge Base, Insights
 */

import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import apiClient from '../../services/apiClient'

interface DashboardStats {
  insights: {
    total: number
    reviewed: number
    unreviewed: number
    by_type: Record<string, { total: number; reviewed: number }>
    by_use_in: Record<string, number>
  }
  vendors: {
    total: number
  }
}

function StatCard({
  title,
  value,
  subtitle,
  icon,
  href,
  color = 'blue',
  trend,
}: {
  title: string
  value: number | string
  subtitle?: string
  icon: string
  href?: string
  color?: 'blue' | 'green' | 'purple' | 'amber'
  trend?: { value: number; label: string }
}) {
  const colorStyles = {
    blue: 'from-blue-500 to-blue-600',
    green: 'from-emerald-500 to-emerald-600',
    purple: 'from-violet-500 to-violet-600',
    amber: 'from-amber-500 to-amber-600',
  }

  const bgStyles = {
    blue: 'bg-blue-50',
    green: 'bg-emerald-50',
    purple: 'bg-violet-50',
    amber: 'bg-amber-50',
  }

  const content = (
    <div className="group relative bg-white rounded-2xl p-6 border border-gray-100 hover:border-gray-200 hover:shadow-lg transition-all duration-300 overflow-hidden">
      {/* Gradient accent */}
      <div className={`absolute inset-x-0 top-0 h-1 bg-gradient-to-r ${colorStyles[color]} opacity-0 group-hover:opacity-100 transition-opacity`} />

      <div className="flex items-start justify-between">
        <div className="space-y-1">
          <p className="text-sm font-medium text-gray-500">{title}</p>
          <p className="text-4xl font-bold text-gray-900 tracking-tight">{value}</p>
          {subtitle && (
            <p className="text-sm text-gray-400">{subtitle}</p>
          )}
          {trend && (
            <div className="flex items-center gap-1 mt-2">
              <span className={`text-xs font-medium ${trend.value >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>
                {trend.value >= 0 ? '+' : ''}{trend.value}%
              </span>
              <span className="text-xs text-gray-400">{trend.label}</span>
            </div>
          )}
        </div>
        <div className={`text-3xl p-4 rounded-2xl ${bgStyles[color]} group-hover:scale-110 transition-transform duration-300`}>
          {icon}
        </div>
      </div>
    </div>
  )

  if (href) {
    return <Link to={href} className="block">{content}</Link>
  }

  return content
}

function QuickAction({
  title,
  description,
  icon,
  href,
  badge,
}: {
  title: string
  description: string
  icon: string
  href: string
  badge?: { label: string; color: 'blue' | 'amber' | 'green' }
}) {
  const badgeColors = {
    blue: 'bg-blue-100 text-blue-700',
    amber: 'bg-amber-100 text-amber-700',
    green: 'bg-emerald-100 text-emerald-700',
  }

  return (
    <Link
      to={href}
      className="group flex items-center gap-4 p-5 bg-white rounded-2xl border border-gray-100 hover:border-gray-200 hover:shadow-lg transition-all duration-300"
    >
      <div className="text-3xl p-3 bg-gray-50 rounded-xl group-hover:bg-gray-100 group-hover:scale-105 transition-all duration-300">
        {icon}
      </div>
      <div className="flex-1">
        <div className="flex items-center gap-2">
          <p className="font-semibold text-gray-900">{title}</p>
          {badge && (
            <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${badgeColors[badge.color]}`}>
              {badge.label}
            </span>
          )}
        </div>
        <p className="text-sm text-gray-500 mt-0.5">{description}</p>
      </div>
      <div className="text-gray-300 group-hover:text-gray-500 group-hover:translate-x-1 transition-all duration-300">
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
        </svg>
      </div>
    </Link>
  )
}

export default function AdminDashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchStats()
  }, [])

  async function fetchStats() {
    try {
      setLoading(true)
      const response = await apiClient.get<{ data: DashboardStats }>('/api/admin/insights/dashboard/summary')
      setStats(response.data.data)
    } catch (err) {
      console.error('Failed to fetch dashboard stats:', err)
      setError('Failed to load dashboard data')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Header */}
      <div className="bg-white/80 backdrop-blur-sm border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-5">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900 tracking-tight">Admin Dashboard</h1>
              <p className="text-gray-500 text-sm mt-0.5">Manage insights, vendors, and knowledge base</p>
            </div>
            <Link
              to="/"
              className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-600 bg-gray-100 hover:bg-gray-200 rounded-xl transition-colors"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M10 19l-7-7m0 0l7-7m-7 7h18"
                />
              </svg>
              Back to App
            </Link>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-2xl text-red-700 flex items-center gap-3">
            <svg className="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            {error}
          </div>
        )}

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <StatCard
            title="Total Insights"
            value={loading ? '...' : stats?.insights.total || 0}
            subtitle={`${stats?.insights.reviewed || 0} reviewed`}
            icon="💡"
            color="purple"
            href="/admin/insights"
          />
          <StatCard
            title="Unreviewed"
            value={loading ? '...' : stats?.insights.unreviewed || 0}
            subtitle="Need attention"
            icon="📝"
            color="amber"
            href="/admin/insights?filter=unreviewed"
          />
          <StatCard
            title="Vendors"
            value={loading ? '...' : stats?.vendors.total || 0}
            subtitle="In database"
            icon="🏢"
            color="blue"
            href="/admin/vendors"
          />
          <StatCard
            title="For Reports"
            value={loading ? '...' : stats?.insights.by_use_in?.report || 0}
            subtitle="Ready to use"
            icon="📊"
            color="green"
          />
        </div>

        {/* Quick Actions */}
        <div className="mb-10">
          <div className="flex items-center justify-between mb-5">
            <h2 className="text-lg font-semibold text-gray-900">Quick Actions</h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <QuickAction
              title="Extract New Insights"
              description="Add insights from a YouTube transcript, article, or report"
              icon="✨"
              href="/admin/insights/extract"
              badge={{ label: 'AI-Powered', color: 'blue' }}
            />
            <QuickAction
              title="Review Pending Insights"
              description="Approve or edit recently extracted insights"
              icon="✅"
              href="/admin/insights?filter=unreviewed"
              badge={stats?.insights.unreviewed ? { label: `${stats.insights.unreviewed} pending`, color: 'amber' } : undefined}
            />
            <QuickAction
              title="Manage Vendors"
              description="Add, edit, or refresh vendor information"
              icon="🏢"
              href="/admin/vendors"
            />
            <QuickAction
              title="Knowledge Base"
              description="Manage industry data and benchmarks"
              icon="📚"
              href="/admin/knowledge"
            />
          </div>
        </div>

        {/* Insights by Type */}
        {stats?.insights.by_type && Object.keys(stats.insights.by_type).length > 0 && (
          <div className="mb-10">
            <h2 className="text-lg font-semibold text-gray-900 mb-5">Insights by Type</h2>
            <div className="bg-white rounded-2xl border border-gray-100 overflow-hidden shadow-sm">
              <table className="min-w-full">
                <thead>
                  <tr className="bg-gray-50/50">
                    <th className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                      Type
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                      Total
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                      Reviewed
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                      Pending
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {Object.entries(stats.insights.by_type).map(([type, counts]) => {
                    const typeColors: Record<string, string> = {
                      trend: 'bg-violet-100 text-violet-700',
                      framework: 'bg-blue-100 text-blue-700',
                      case_study: 'bg-emerald-100 text-emerald-700',
                      statistic: 'bg-amber-100 text-amber-700',
                      quote: 'bg-pink-100 text-pink-700',
                      prediction: 'bg-indigo-100 text-indigo-700',
                    }
                    return (
                      <tr key={type} className="hover:bg-gray-50/50 transition-colors">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`inline-flex items-center px-2.5 py-1 rounded-lg text-xs font-medium ${typeColors[type] || 'bg-gray-100 text-gray-700'}`}>
                            {type.replace('_', ' ')}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className="text-gray-900 font-semibold">{counts.total}</span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className="inline-flex items-center gap-1.5 text-emerald-600 font-medium">
                            <span className="w-2 h-2 bg-emerald-500 rounded-full" />
                            {counts.reviewed}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          {counts.total - counts.reviewed > 0 ? (
                            <span className="inline-flex items-center gap-1.5 text-amber-600 font-medium">
                              <span className="w-2 h-2 bg-amber-500 rounded-full animate-pulse" />
                              {counts.total - counts.reviewed}
                            </span>
                          ) : (
                            <span className="text-gray-400">0</span>
                          )}
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Claude Code Terminal Helper */}
        <div className="mb-10">
          <h2 className="text-lg font-semibold text-gray-900 mb-5">Claude Code Terminal</h2>
          <div className="bg-gradient-to-br from-gray-900 to-gray-800 rounded-2xl p-6 shadow-lg">
            <p className="text-gray-400 text-sm mb-4">
              Extract insights via Claude Code (uses Opus 4.5, no API costs on Max plan):
            </p>
            <div className="bg-black/30 rounded-xl p-4 font-mono text-sm">
              <p className="text-gray-500 mb-2"># Paste transcript/content and extract insights</p>
              <p className="text-emerald-400 break-all select-all cursor-pointer hover:bg-white/5 rounded px-1 -mx-1 transition-colors" title="Click to select">
                cd backend && python -m scripts.extract_insights --paste --title "Title Here" --author "Author" --source-type youtube
              </p>
              <p className="text-gray-500 mt-4 mb-2"># Or from a file</p>
              <p className="text-emerald-400 break-all select-all cursor-pointer hover:bg-white/5 rounded px-1 -mx-1 transition-colors" title="Click to select">
                cd backend && python -m scripts.extract_insights --file src/knowledge/insights/raw/transcript.txt
              </p>
              <p className="text-gray-500 mt-4 mb-2"># List existing insights</p>
              <p className="text-emerald-400 break-all select-all cursor-pointer hover:bg-white/5 rounded px-1 -mx-1 transition-colors" title="Click to select">
                cd backend && python -m scripts.extract_insights --list --stats
              </p>
            </div>
            <p className="text-gray-500 text-xs mt-4">
              Tip: Use <code className="text-gray-400">--auto-save</code> to skip the review prompt
            </p>
          </div>
        </div>

        {/* Footer */}
        <div className="mt-12 pt-8 border-t border-gray-200">
          <div className="flex items-center justify-center gap-2 text-sm text-gray-400">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
            <span>Full CLI docs: </span>
            <code className="bg-gray-100 px-2.5 py-1 rounded-lg font-mono text-xs text-gray-600">
              python -m scripts.extract_insights --help
            </code>
          </div>
        </div>
      </div>
    </div>
  )
}
