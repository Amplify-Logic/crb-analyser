/**
 * Dashboard Page
 * Main authenticated view showing audits overview
 */

import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import apiClient from '../services/apiClient'
import { Logo } from '../components/Logo'

interface Audit {
  id: string
  title: string
  status: string
  tier: string
  ai_readiness_score?: number
  total_potential_savings?: number
  created_at: string
  client_name?: string
}

interface AuditStats {
  total: number
  totalSavings: number
  inProgress: number
}

export default function Dashboard() {
  const { user, logout } = useAuth()
  const [audits, setAudits] = useState<Audit[]>([])
  const [stats, setStats] = useState<AuditStats>({ total: 0, totalSavings: 0, inProgress: 0 })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadAudits()
  }, [])

  async function loadAudits() {
    try {
      const { data } = await apiClient.get<{ data: Audit[]; total: number }>('/api/audits')
      const auditList = data.data || []
      setAudits(auditList)

      // Calculate stats
      const totalSavings = auditList.reduce((sum, a) => sum + (a.total_potential_savings || 0), 0)
      const inProgress = auditList.filter(a => ['intake', 'processing'].includes(a.status)).length

      setStats({
        total: auditList.length,
        totalSavings,
        inProgress,
      })
    } catch (err) {
      console.error('Failed to load audits:', err)
    } finally {
      setLoading(false)
    }
  }

  const statusColors: Record<string, string> = {
    intake: 'bg-blue-100 text-blue-700',
    processing: 'bg-yellow-100 text-yellow-700',
    completed: 'bg-green-100 text-green-700',
    failed: 'bg-red-100 text-red-700',
  }

  const statusLabels: Record<string, string> = {
    intake: 'Intake',
    processing: 'Processing',
    completed: 'Completed',
    failed: 'Failed',
  }

  function getAuditLink(audit: Audit): string {
    switch (audit.status) {
      case 'intake':
        return `/audit/${audit.id}/intake`
      case 'processing':
        return `/audit/${audit.id}/progress`
      case 'completed':
        return `/audit/${audit.id}/report`
      default:
        return `/audit/${audit.id}/report`
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <Logo size="sm" showIcon={false} />
            </div>
            <div className="flex items-center gap-4">
              <span className="text-sm text-gray-600">
                {user?.full_name || user?.email}
              </span>
              <button
                onClick={logout}
                className="p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100 transition"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Welcome Section */}
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-gray-900">
            Welcome back{user?.full_name ? `, ${user.full_name.split(' ')[0]}` : ''}
          </h1>
          <p className="text-gray-600 mt-1">
            Here's an overview of your AI readiness reports.
          </p>
        </div>

        {/* Quick Actions */}
        <div className="mb-8">
          <Link
            to="/new-audit"
            className="inline-flex items-center gap-2 px-6 py-3 bg-primary-600 text-white font-semibold rounded-xl hover:bg-primary-700 transition"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            Start New Audit
          </Link>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <StatCard
            icon={
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            }
            label="Total Audits"
            value={stats.total.toString()}
            color="primary"
          />
          <StatCard
            icon={
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
              </svg>
            }
            label="Potential Savings"
            value={`€${stats.totalSavings.toLocaleString()}`}
            color="green"
          />
          <StatCard
            icon={
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            }
            label="In Progress"
            value={stats.inProgress.toString()}
            color="yellow"
          />
        </div>

        {/* Audits List */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-200">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">Recent Audits</h2>
          </div>

          {loading ? (
            <div className="p-12 text-center">
              <div className="w-8 h-8 border-4 border-primary-600 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
              <p className="text-gray-600">Loading audits...</p>
            </div>
          ) : audits.length === 0 ? (
            <div className="p-12 text-center">
              <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">No audits yet</h3>
              <p className="text-gray-600 mb-6">
                Start your first analysis to discover AI opportunities for your business.
              </p>
              <Link
                to="/new-audit"
                className="inline-flex items-center gap-2 px-6 py-3 bg-primary-600 text-white font-semibold rounded-xl hover:bg-primary-700 transition"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                Start New Audit
              </Link>
            </div>
          ) : (
            <div className="divide-y divide-gray-200">
              {audits.map((audit) => (
                <Link
                  key={audit.id}
                  to={getAuditLink(audit)}
                  className="flex items-center justify-between p-6 hover:bg-gray-50 transition"
                >
                  <div className="flex-1">
                    <h3 className="font-medium text-gray-900">{audit.title}</h3>
                    <p className="text-sm text-gray-500 mt-1">
                      {new Date(audit.created_at).toLocaleDateString()}
                      {audit.client_name && ` • ${audit.client_name}`}
                    </p>
                  </div>

                  <div className="flex items-center gap-4">
                    {audit.ai_readiness_score && (
                      <div className="text-right">
                        <p className="text-lg font-bold text-primary-600">{audit.ai_readiness_score}</p>
                        <p className="text-xs text-gray-500">Score</p>
                      </div>
                    )}

                    {audit.total_potential_savings && audit.total_potential_savings > 0 && (
                      <div className="text-right">
                        <p className="text-lg font-bold text-green-600">€{audit.total_potential_savings.toLocaleString()}</p>
                        <p className="text-xs text-gray-500">Savings</p>
                      </div>
                    )}

                    <span className={`px-3 py-1 text-sm font-medium rounded-full ${statusColors[audit.status] || 'bg-gray-100 text-gray-700'}`}>
                      {statusLabels[audit.status] || audit.status}
                    </span>

                    <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  )
}

// Stat card component
interface StatCardProps {
  icon: React.ReactNode
  label: string
  value: string
  color: 'primary' | 'green' | 'yellow'
}

function StatCard({ icon, label, value, color }: StatCardProps) {
  const colorClasses = {
    primary: 'bg-primary-50 text-primary-600',
    green: 'bg-green-50 text-green-600',
    yellow: 'bg-yellow-50 text-yellow-600',
  }

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6">
      <div className={`w-12 h-12 rounded-xl flex items-center justify-center mb-4 ${colorClasses[color]}`}>
        {icon}
      </div>
      <p className="text-sm text-gray-600">{label}</p>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
    </div>
  )
}
