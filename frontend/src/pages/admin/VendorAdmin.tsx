/**
 * Vendor Admin Page
 *
 * Admin UI for managing the vendor database.
 * Features: list, search, filter, CRUD, industry tiers, audit log.
 */

import { useState, useEffect, useCallback } from 'react'
import { useSearchParams } from 'react-router-dom'
import apiClient from '../../services/apiClient'
import VendorResearchButtons from '../../components/admin/VendorResearchButtons'

// Types
interface Vendor {
  id: string
  slug: string
  name: string
  category: string
  subcategory?: string
  website?: string
  pricing_url?: string
  description?: string
  tagline?: string
  pricing?: {
    model?: string
    currency?: string
    tiers?: Array<{
      name: string
      price?: number
      per?: string
      features?: string[]
    }>
    starting_price?: number
    free_tier?: boolean
    free_trial_days?: number
  }
  company_sizes?: string[]
  industries?: string[]
  best_for?: string[]
  avoid_if?: string[]
  recommended_default?: boolean
  recommended_for?: string[]
  our_rating?: number
  our_notes?: string
  g2_score?: number
  capterra_score?: number
  implementation_weeks?: number
  implementation_complexity?: string
  requires_developer?: boolean
  integrations?: string[]
  key_capabilities?: string[]
  status?: string
  verified_at?: string
  verified_by?: string
  created_at?: string
  updated_at?: string
  // API & Integration fields
  api_available?: boolean
  api_openness_score?: number  // 1-5 rating
  api_type?: string  // REST, GraphQL, SOAP
  api_docs_url?: string
  has_webhooks?: boolean
  has_oauth?: boolean
  zapier_integration?: boolean
  make_integration?: boolean
  n8n_integration?: boolean
  api_rate_limits?: string
  custom_tool_examples?: string[]
}

interface Category {
  slug: string
  name: string
  vendor_count: number
}

interface Industry {
  slug: string
  name: string
  priority: string
}

interface VendorStats {
  total_vendors: number
  by_status: Record<string, number>
  by_category: Record<string, number>
  tier_assignments: Record<string, Record<string, number>>
  stale_vendors: number
}

interface TierVendor {
  vendor: Vendor
  tier: number
  boost_score: number
  notes?: string
}

interface IndustryTiers {
  industry: string
  tier_1: TierVendor[]
  tier_2: TierVendor[]
  tier_3: TierVendor[]
}

// ============================================================================
// Components
// ============================================================================

function VendorStatusBadge({ status }: { status?: string }) {
  const styles: Record<string, string> = {
    active: 'bg-green-100 text-green-700',
    deprecated: 'bg-gray-100 text-gray-500',
    needs_review: 'bg-amber-100 text-amber-700',
  }
  return (
    <span className={`text-xs px-2 py-0.5 rounded-full ${styles[status || 'active']}`}>
      {status || 'active'}
    </span>
  )
}

function formatDate(dateString?: string): string {
  if (!dateString) return 'Never'
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

  if (diffDays < 1) return 'Today'
  if (diffDays < 7) return `${diffDays}d ago`
  if (diffDays < 30) return `${Math.floor(diffDays / 7)}w ago`
  if (diffDays < 90) return `${Math.floor(diffDays / 30)}mo ago`
  return date.toLocaleDateString()
}

function VendorList({
  vendors,
  loading,
  onSelect,
  onVerify,
}: {
  vendors: Vendor[]
  loading: boolean
  onSelect: (vendor: Vendor) => void
  onVerify: (vendor: Vendor) => void
}) {
  if (loading) {
    return (
      <div className="space-y-3">
        {[...Array(5)].map((_, i) => (
          <div key={i} className="bg-white rounded-xl p-4 animate-pulse border border-gray-100">
            <div className="h-4 bg-gray-200 rounded w-1/3 mb-2" />
            <div className="h-3 bg-gray-100 rounded w-2/3" />
          </div>
        ))}
      </div>
    )
  }

  if (vendors.length === 0) {
    return (
      <div className="bg-white rounded-xl p-12 text-center border border-gray-100">
        <div className="text-4xl mb-4">📦</div>
        <h3 className="text-lg font-medium text-gray-900 mb-2">No vendors found</h3>
        <p className="text-gray-500">Try adjusting your filters or add a new vendor.</p>
      </div>
    )
  }

  return (
    <div className="space-y-2">
      {vendors.map((vendor) => (
        <div
          key={vendor.id}
          onClick={() => onSelect(vendor)}
          className="bg-white rounded-xl p-4 hover:shadow-md transition-shadow cursor-pointer border border-gray-100"
        >
          <div className="flex items-start justify-between">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <h3 className="font-medium text-gray-900 truncate">{vendor.name}</h3>
                <span className="text-xs px-2 py-0.5 bg-blue-50 text-blue-700 rounded-full">
                  {vendor.category}
                </span>
                <VendorStatusBadge status={vendor.status} />
              </div>
              <p className="text-sm text-gray-500 line-clamp-1">
                {vendor.description || vendor.tagline || 'No description'}
              </p>
              <div className="mt-2 flex flex-wrap gap-1">
                {vendor.industries?.slice(0, 3).map((ind) => (
                  <span key={ind} className="text-xs px-2 py-0.5 bg-gray-100 text-gray-600 rounded">
                    {ind}
                  </span>
                ))}
                {(vendor.industries?.length || 0) > 3 && (
                  <span className="text-xs text-gray-400">+{(vendor.industries?.length || 0) - 3}</span>
                )}
                {vendor.our_rating && (
                  <span className="text-xs px-2 py-0.5 bg-yellow-50 text-yellow-700 rounded flex items-center gap-1">
                    ★ {vendor.our_rating.toFixed(1)}
                  </span>
                )}
                {vendor.api_openness_score && (
                  <span className={`text-xs px-2 py-0.5 rounded flex items-center gap-1 ${
                    vendor.api_openness_score >= 4
                      ? 'bg-green-50 text-green-700'
                      : vendor.api_openness_score >= 3
                        ? 'bg-blue-50 text-blue-700'
                        : 'bg-gray-100 text-gray-600'
                  }`}>
                    API: {vendor.api_openness_score}/5
                  </span>
                )}
              </div>
            </div>
            <div className="flex flex-col items-end gap-2 ml-4">
              <span className="text-xs text-gray-400">
                Verified: {formatDate(vendor.verified_at)}
              </span>
              {!vendor.verified_at && vendor.status === 'active' && (
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    onVerify(vendor)
                  }}
                  className="text-xs px-2 py-1 text-green-600 hover:bg-green-50 rounded transition-colors"
                >
                  Mark Verified
                </button>
              )}
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}

function VendorEditor({
  vendor,
  categories,
  industries,
  onSave,
  onDelete,
  onCancel,
}: {
  vendor: Vendor | null
  categories: Category[]
  industries: Industry[]
  onSave: (vendor: Partial<Vendor>) => Promise<void>
  onDelete: (vendor: Vendor) => Promise<void>
  onCancel: () => void
}) {
  const [form, setForm] = useState<Partial<Vendor>>(
    vendor || {
      slug: '',
      name: '',
      category: 'customer_support',
      description: '',
      industries: [],
      company_sizes: [],
      status: 'active',
    }
  )
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const isNew = !vendor?.id

  const handleChange = (field: keyof Vendor, value: unknown) => {
    setForm((prev) => ({ ...prev, [field]: value }))
  }

  const handleArrayChange = (field: keyof Vendor, value: string) => {
    const arr = value
      .split(',')
      .map((s) => s.trim())
      .filter(Boolean)
    handleChange(field, arr)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSaving(true)
    setError(null)

    try {
      await onSave(form)
    } catch (err: unknown) {
      const apiError = err as { message?: string; detail?: string }
      setError(apiError.message || apiError.detail || 'Failed to save vendor')
    } finally {
      setSaving(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="bg-white rounded-xl p-6 border border-gray-100">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-xl font-semibold text-gray-900">
          {isNew ? 'Add New Vendor' : `Edit: ${vendor?.name}`}
        </h2>
        <div className="flex gap-2">
          <button type="button" onClick={onCancel} className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg">
            Cancel
          </button>
          {!isNew && (
            <button
              type="button"
              onClick={() => vendor && onDelete(vendor)}
              className="px-4 py-2 text-red-600 hover:bg-red-50 rounded-lg"
            >
              Delete
            </button>
          )}
          <button
            type="submit"
            disabled={saving}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            {saving ? 'Saving...' : 'Save'}
          </button>
        </div>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-50 text-red-700 rounded-lg text-sm">{error}</div>
      )}

      <div className="grid grid-cols-2 gap-6">
        {/* Left Column */}
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Slug *</label>
            <input
              type="text"
              value={form.slug || ''}
              onChange={(e) => handleChange('slug', e.target.value)}
              disabled={!isNew}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Name *</label>
            <input
              type="text"
              value={form.name || ''}
              onChange={(e) => handleChange('name', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Category *</label>
            <select
              value={form.category || ''}
              onChange={(e) => handleChange('category', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              required
            >
              {categories.map((cat) => (
                <option key={cat.slug} value={cat.slug}>
                  {cat.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Website</label>
            <input
              type="url"
              value={form.website || ''}
              onChange={(e) => handleChange('website', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
            <textarea
              value={form.description || ''}
              onChange={(e) => handleChange('description', e.target.value)}
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Industries (comma-separated)</label>
            <input
              type="text"
              value={(form.industries || []).join(', ')}
              onChange={(e) => handleArrayChange('industries', e.target.value)}
              placeholder="dental, recruiting, saas"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
            <div className="mt-1 flex flex-wrap gap-1">
              {industries.map((ind) => (
                <button
                  key={ind.slug}
                  type="button"
                  onClick={() => {
                    const current = form.industries || []
                    const updated = current.includes(ind.slug)
                      ? current.filter((i) => i !== ind.slug)
                      : [...current, ind.slug]
                    handleChange('industries', updated)
                  }}
                  className={`text-xs px-2 py-0.5 rounded transition-colors ${
                    (form.industries || []).includes(ind.slug)
                      ? 'bg-blue-100 text-blue-700'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                >
                  {ind.name}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Right Column */}
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Company Sizes (comma-separated)</label>
            <input
              type="text"
              value={(form.company_sizes || []).join(', ')}
              onChange={(e) => handleArrayChange('company_sizes', e.target.value)}
              placeholder="startup, smb, mid_market, enterprise"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Our Rating (0-5)</label>
              <input
                type="number"
                min="0"
                max="5"
                step="0.1"
                value={form.our_rating || ''}
                onChange={(e) => handleChange('our_rating', parseFloat(e.target.value) || undefined)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">G2 Score</label>
              <input
                type="number"
                min="0"
                max="5"
                step="0.1"
                value={form.g2_score || ''}
                onChange={(e) => handleChange('g2_score', parseFloat(e.target.value) || undefined)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Best For (comma-separated)</label>
            <input
              type="text"
              value={(form.best_for || []).join(', ')}
              onChange={(e) => handleArrayChange('best_for', e.target.value)}
              placeholder="Small teams, High volume support"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Avoid If (comma-separated)</label>
            <input
              type="text"
              value={(form.avoid_if || []).join(', ')}
              onChange={(e) => handleArrayChange('avoid_if', e.target.value)}
              placeholder="Need extensive customization"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Implementation Weeks</label>
              <input
                type="number"
                min="0"
                value={form.implementation_weeks || ''}
                onChange={(e) => handleChange('implementation_weeks', parseInt(e.target.value) || undefined)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Complexity</label>
              <select
                value={form.implementation_complexity || ''}
                onChange={(e) => handleChange('implementation_complexity', e.target.value || undefined)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="">-</option>
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
              </select>
            </div>
          </div>

          <div className="flex gap-6">
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={form.recommended_default || false}
                onChange={(e) => handleChange('recommended_default', e.target.checked)}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <span className="text-sm text-gray-700">Recommended Default</span>
            </label>
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={form.requires_developer || false}
                onChange={(e) => handleChange('requires_developer', e.target.checked)}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <span className="text-sm text-gray-700">Requires Developer</span>
            </label>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Internal Notes</label>
            <textarea
              value={form.our_notes || ''}
              onChange={(e) => handleChange('our_notes', e.target.value)}
              rows={2}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
            <select
              value={form.status || 'active'}
              onChange={(e) => handleChange('status', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="active">Active</option>
              <option value="needs_review">Needs Review</option>
              <option value="deprecated">Deprecated</option>
            </select>
          </div>
        </div>
      </div>

      {/* API & Integration Section */}
      <div className="mt-6 pt-6 border-t border-gray-200">
        <h3 className="text-lg font-medium text-gray-900 mb-4">API & Integration Capabilities</h3>
        <p className="text-sm text-gray-500 mb-4">
          Rate this vendor's API openness for automation-first recommendations.
        </p>

        <div className="grid grid-cols-2 gap-6">
          {/* Left Column - API Info */}
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                API Openness Score (1-5)
              </label>
              <select
                value={form.api_openness_score || ''}
                onChange={(e) => handleChange('api_openness_score', e.target.value ? parseInt(e.target.value) : undefined)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Not rated</option>
                <option value="5">5 - Full API + Webhooks + OAuth (Stripe, Twilio)</option>
                <option value="4">4 - Good API, some limitations (Salesforce)</option>
                <option value="3">3 - Basic API, limited endpoints</option>
                <option value="2">2 - Zapier/Make only, no direct API</option>
                <option value="1">1 - Closed system, no integrations</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">API Type</label>
              <select
                value={form.api_type || ''}
                onChange={(e) => handleChange('api_type', e.target.value || undefined)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="">None / Unknown</option>
                <option value="REST">REST</option>
                <option value="GraphQL">GraphQL</option>
                <option value="SOAP">SOAP</option>
                <option value="gRPC">gRPC</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">API Docs URL</label>
              <input
                type="url"
                value={form.api_docs_url || ''}
                onChange={(e) => handleChange('api_docs_url', e.target.value)}
                placeholder="https://docs.example.com/api"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">API Rate Limits</label>
              <input
                type="text"
                value={form.api_rate_limits || ''}
                onChange={(e) => handleChange('api_rate_limits', e.target.value)}
                placeholder="e.g., 1000/min, 100 req/hour"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          {/* Right Column - Integration Support */}
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">API Capabilities</label>
              <div className="space-y-2">
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={form.api_available || false}
                    onChange={(e) => handleChange('api_available', e.target.checked)}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="text-sm text-gray-700">API Available</span>
                </label>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={form.has_webhooks || false}
                    onChange={(e) => handleChange('has_webhooks', e.target.checked)}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="text-sm text-gray-700">Supports Webhooks</span>
                </label>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={form.has_oauth || false}
                    onChange={(e) => handleChange('has_oauth', e.target.checked)}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="text-sm text-gray-700">Supports OAuth</span>
                </label>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Integration Platforms</label>
              <div className="space-y-2">
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={form.zapier_integration || false}
                    onChange={(e) => handleChange('zapier_integration', e.target.checked)}
                    className="rounded border-gray-300 text-orange-500 focus:ring-orange-500"
                  />
                  <span className="text-sm text-gray-700">Zapier Integration</span>
                </label>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={form.make_integration || false}
                    onChange={(e) => handleChange('make_integration', e.target.checked)}
                    className="rounded border-gray-300 text-purple-600 focus:ring-purple-500"
                  />
                  <span className="text-sm text-gray-700">Make (Integromat) Integration</span>
                </label>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={form.n8n_integration || false}
                    onChange={(e) => handleChange('n8n_integration', e.target.checked)}
                    className="rounded border-gray-300 text-green-600 focus:ring-green-500"
                  />
                  <span className="text-sm text-gray-700">n8n Integration</span>
                </label>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Custom Tool Examples (one per line)
              </label>
              <textarea
                value={(form.custom_tool_examples || []).join('\n')}
                onChange={(e) => {
                  const examples = e.target.value.split('\n').filter(Boolean)
                  handleChange('custom_tool_examples', examples.length > 0 ? examples : undefined)
                }}
                rows={3}
                placeholder="AI-powered lead scoring&#10;Automated follow-up workflows&#10;Smart ticket routing"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-sm"
              />
              <p className="text-xs text-gray-500 mt-1">
                Examples of automations possible with this vendor's API
              </p>
            </div>
          </div>
        </div>
      </div>
    </form>
  )
}

function VendorStats({ stats }: { stats: VendorStats | null }) {
  if (!stats) {
    return (
      <div className="bg-white rounded-xl p-6 border border-gray-100 animate-pulse">
        <div className="h-6 bg-gray-200 rounded w-1/3 mb-4" />
        <div className="grid grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-24 bg-gray-100 rounded-lg" />
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-white rounded-xl p-4 border border-gray-100">
          <div className="text-2xl font-bold text-gray-900">{stats.total_vendors}</div>
          <div className="text-sm text-gray-500">Total Vendors</div>
        </div>
        <div className="bg-white rounded-xl p-4 border border-gray-100">
          <div className="text-2xl font-bold text-green-600">{stats.by_status.active || 0}</div>
          <div className="text-sm text-gray-500">Active</div>
        </div>
        <div className="bg-white rounded-xl p-4 border border-gray-100">
          <div className="text-2xl font-bold text-amber-600">{stats.stale_vendors}</div>
          <div className="text-sm text-gray-500">Stale (90+ days)</div>
        </div>
        <div className="bg-white rounded-xl p-4 border border-gray-100">
          <div className="text-2xl font-bold text-gray-400">{stats.by_status.deprecated || 0}</div>
          <div className="text-sm text-gray-500">Deprecated</div>
        </div>
      </div>

      <div className="bg-white rounded-xl p-6 border border-gray-100">
        <h3 className="font-semibold text-gray-900 mb-4">By Category</h3>
        <div className="grid grid-cols-2 gap-2">
          {Object.entries(stats.by_category)
            .sort((a, b) => b[1] - a[1])
            .map(([cat, count]) => (
              <div key={cat} className="flex justify-between items-center py-1">
                <span className="text-sm text-gray-600">{cat}</span>
                <span className="text-sm font-medium text-gray-900">{count}</span>
              </div>
            ))}
        </div>
      </div>

      <div className="bg-white rounded-xl p-6 border border-gray-100">
        <h3 className="font-semibold text-gray-900 mb-4">Industry Tier Assignments</h3>
        <div className="space-y-2">
          {Object.entries(stats.tier_assignments).map(([industry, tiers]) => (
            <div key={industry} className="flex items-center gap-4">
              <span className="text-sm text-gray-600 w-32">{industry}</span>
              <div className="flex gap-2">
                <span className="text-xs px-2 py-0.5 bg-green-100 text-green-700 rounded">
                  T1: {tiers.tier_1}
                </span>
                <span className="text-xs px-2 py-0.5 bg-blue-100 text-blue-700 rounded">
                  T2: {tiers.tier_2}
                </span>
                <span className="text-xs px-2 py-0.5 bg-gray-100 text-gray-600 rounded">
                  T3: {tiers.tier_3}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

// ============================================================================
// Industry Tier Manager Component
// ============================================================================

function IndustryTierManager({
  industries,
  onBack,
}: {
  industries: Industry[]
  onBack: () => void
}) {
  const [selectedIndustry, setSelectedIndustry] = useState<string>(industries[0]?.slug || '')
  const [tiers, setTiers] = useState<IndustryTiers | null>(null)
  const [loading, setLoading] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState<Vendor[]>([])
  const [searching, setSearching] = useState(false)
  const [editingVendor, setEditingVendor] = useState<{
    vendorId: string
    tier: number
    boost_score: number
    notes: string
  } | null>(null)

  // Load tiers when industry changes
  useEffect(() => {
    if (selectedIndustry) {
      loadTiers()
    }
  }, [selectedIndustry])

  const loadTiers = async () => {
    setLoading(true)
    try {
      const { data } = await apiClient.get<IndustryTiers>(
        `/api/admin/vendors/industries/${selectedIndustry}/tiers`
      )
      setTiers(data)
    } catch (err) {
      console.error('Failed to load tiers:', err)
    } finally {
      setLoading(false)
    }
  }

  const searchVendors = async () => {
    if (!searchQuery.trim()) {
      setSearchResults([])
      return
    }
    setSearching(true)
    try {
      const { data } = await apiClient.get<{ vendors: Vendor[] }>(
        `/api/admin/vendors?search=${encodeURIComponent(searchQuery)}&page_size=10`
      )
      // Filter out vendors already in tiers
      const tierVendorIds = new Set([
        ...(tiers?.tier_1.map((t) => t.vendor?.id) || []),
        ...(tiers?.tier_2.map((t) => t.vendor?.id) || []),
        ...(tiers?.tier_3.map((t) => t.vendor?.id) || []),
      ])
      setSearchResults((data.vendors || []).filter((v) => !tierVendorIds.has(v.id)))
    } catch (err) {
      console.error('Search failed:', err)
    } finally {
      setSearching(false)
    }
  }

  const addToTier = async (vendor: Vendor, tier: number) => {
    try {
      await apiClient.post(`/api/admin/vendors/industries/${selectedIndustry}/tiers/${vendor.id}`, {
        tier,
        boost_score: 0,
      })
      setSearchQuery('')
      setSearchResults([])
      loadTiers()
    } catch (err) {
      console.error('Failed to add vendor to tier:', err)
    }
  }

  const removeFromTier = async (vendorId: string) => {
    if (!confirm('Remove this vendor from the tier list?')) return
    try {
      await apiClient.delete(`/api/admin/vendors/industries/${selectedIndustry}/tiers/${vendorId}`)
      loadTiers()
    } catch (err) {
      console.error('Failed to remove vendor:', err)
    }
  }

  const updateTier = async (vendorId: string, newTier: number, boost_score: number, notes?: string) => {
    try {
      await apiClient.post(`/api/admin/vendors/industries/${selectedIndustry}/tiers/${vendorId}`, {
        tier: newTier,
        boost_score,
        notes,
      })
      setEditingVendor(null)
      loadTiers()
    } catch (err) {
      console.error('Failed to update tier:', err)
    }
  }

  const TierColumn = ({
    title,
    tier,
    vendors,
    color,
    boostLabel,
  }: {
    title: string
    tier: number
    vendors: TierVendor[]
    color: string
    boostLabel: string
  }) => (
    <div className="flex-1 min-w-0">
      <div className={`rounded-t-lg px-4 py-2 ${color}`}>
        <div className="flex items-center justify-between">
          <h3 className="font-semibold text-white">{title}</h3>
          <span className="text-xs text-white/80">{boostLabel}</span>
        </div>
      </div>
      <div className="bg-white border border-t-0 border-gray-200 rounded-b-lg min-h-[300px] p-2 space-y-2">
        {vendors.map((item) => (
          <div
            key={item.vendor?.id}
            className="p-3 bg-gray-50 rounded-lg border border-gray-100 group"
          >
            <div className="flex items-start justify-between">
              <div className="flex-1 min-w-0">
                <div className="font-medium text-sm text-gray-900 truncate">
                  {item.vendor?.name}
                </div>
                <div className="text-xs text-gray-500">{item.vendor?.category}</div>
                {item.boost_score > 0 && (
                  <div className="text-xs text-green-600 mt-1">+{item.boost_score} extra boost</div>
                )}
              </div>
              <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                <button
                  onClick={() =>
                    setEditingVendor({
                      vendorId: item.vendor?.id || '',
                      tier,
                      boost_score: item.boost_score,
                      notes: item.notes || '',
                    })
                  }
                  className="p-1 text-blue-600 hover:bg-blue-50 rounded"
                  title="Edit"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                  </svg>
                </button>
                <button
                  onClick={() => removeFromTier(item.vendor?.id || '')}
                  className="p-1 text-red-600 hover:bg-red-50 rounded"
                  title="Remove"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>
            {/* Move tier buttons */}
            <div className="mt-2 flex gap-1">
              {tier !== 1 && (
                <button
                  onClick={() => updateTier(item.vendor?.id || '', 1, item.boost_score, item.notes)}
                  className="text-xs px-2 py-0.5 bg-green-100 text-green-700 rounded hover:bg-green-200"
                >
                  → T1
                </button>
              )}
              {tier !== 2 && (
                <button
                  onClick={() => updateTier(item.vendor?.id || '', 2, item.boost_score, item.notes)}
                  className="text-xs px-2 py-0.5 bg-blue-100 text-blue-700 rounded hover:bg-blue-200"
                >
                  → T2
                </button>
              )}
              {tier !== 3 && (
                <button
                  onClick={() => updateTier(item.vendor?.id || '', 3, item.boost_score, item.notes)}
                  className="text-xs px-2 py-0.5 bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
                >
                  → T3
                </button>
              )}
            </div>
          </div>
        ))}
        {vendors.length === 0 && (
          <div className="text-center py-8 text-gray-400 text-sm">No vendors in this tier</div>
        )}
      </div>
    </div>
  )

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button
            onClick={onBack}
            className="text-gray-500 hover:text-gray-700"
          >
            ← Back
          </button>
          <h2 className="text-xl font-semibold text-gray-900">Industry Tier Management</h2>
        </div>
        <select
          value={selectedIndustry}
          onChange={(e) => setSelectedIndustry(e.target.value)}
          className="px-4 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
        >
          {industries.map((ind) => (
            <option key={ind.slug} value={ind.slug}>
              {ind.name}
            </option>
          ))}
        </select>
      </div>

      {/* Search to add */}
      <div className="bg-white rounded-xl p-4 border border-gray-100">
        <label className="block text-sm font-medium text-gray-700 mb-2">Add Vendor to Tier</label>
        <div className="flex gap-2">
          <div className="relative flex-1">
            <input
              type="text"
              placeholder="Search vendors to add..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && searchVendors()}
              className="w-full px-4 py-2 pl-10 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
            <svg
              className="absolute left-3 top-2.5 h-4 w-4 text-gray-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
          <button
            onClick={searchVendors}
            disabled={searching}
            className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 disabled:opacity-50"
          >
            {searching ? 'Searching...' : 'Search'}
          </button>
        </div>

        {/* Search Results */}
        {searchResults.length > 0 && (
          <div className="mt-3 border border-gray-200 rounded-lg divide-y divide-gray-100">
            {searchResults.map((vendor) => (
              <div key={vendor.id} className="p-3 flex items-center justify-between hover:bg-gray-50">
                <div>
                  <div className="font-medium text-sm text-gray-900">{vendor.name}</div>
                  <div className="text-xs text-gray-500">{vendor.category}</div>
                </div>
                <div className="flex gap-1">
                  <button
                    onClick={() => addToTier(vendor, 1)}
                    className="px-2 py-1 text-xs bg-green-100 text-green-700 rounded hover:bg-green-200"
                  >
                    + Tier 1
                  </button>
                  <button
                    onClick={() => addToTier(vendor, 2)}
                    className="px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded hover:bg-blue-200"
                  >
                    + Tier 2
                  </button>
                  <button
                    onClick={() => addToTier(vendor, 3)}
                    className="px-2 py-1 text-xs bg-gray-100 text-gray-600 rounded hover:bg-gray-200"
                  >
                    + Tier 3
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Tier Columns */}
      {loading ? (
        <div className="flex gap-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="flex-1 bg-gray-100 rounded-lg h-96 animate-pulse" />
          ))}
        </div>
      ) : tiers ? (
        <div className="flex gap-4">
          <TierColumn
            title="Tier 1 - Top Picks"
            tier={1}
            vendors={tiers.tier_1}
            color="bg-green-600"
            boostLabel="+30 boost"
          />
          <TierColumn
            title="Tier 2 - Recommended"
            tier={2}
            vendors={tiers.tier_2}
            color="bg-blue-600"
            boostLabel="+20 boost"
          />
          <TierColumn
            title="Tier 3 - Alternatives"
            tier={3}
            vendors={tiers.tier_3}
            color="bg-gray-500"
            boostLabel="+10 boost"
          />
        </div>
      ) : (
        <div className="text-center py-12 text-gray-500">Select an industry to manage tiers</div>
      )}

      {/* Edit Modal */}
      {editingVendor && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Edit Tier Assignment</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Tier</label>
                <select
                  value={editingVendor.tier}
                  onChange={(e) =>
                    setEditingVendor({ ...editingVendor, tier: parseInt(e.target.value) })
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                >
                  <option value={1}>Tier 1 - Top Picks (+30)</option>
                  <option value={2}>Tier 2 - Recommended (+20)</option>
                  <option value={3}>Tier 3 - Alternatives (+10)</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Extra Boost Score
                </label>
                <input
                  type="number"
                  min="0"
                  max="50"
                  value={editingVendor.boost_score}
                  onChange={(e) =>
                    setEditingVendor({ ...editingVendor, boost_score: parseInt(e.target.value) || 0 })
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Additional points on top of tier boost (0-50)
                </p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Notes</label>
                <textarea
                  value={editingVendor.notes}
                  onChange={(e) => setEditingVendor({ ...editingVendor, notes: e.target.value })}
                  rows={2}
                  placeholder="Why is this vendor in this tier?"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                />
              </div>
            </div>
            <div className="flex justify-end gap-2 mt-6">
              <button
                onClick={() => setEditingVendor(null)}
                className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg"
              >
                Cancel
              </button>
              <button
                onClick={() =>
                  updateTier(
                    editingVendor.vendorId,
                    editingVendor.tier,
                    editingVendor.boost_score,
                    editingVendor.notes
                  )
                }
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Save
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

// ============================================================================
// Main Page
// ============================================================================

export default function VendorAdmin() {
  const [searchParams, setSearchParams] = useSearchParams()

  // State
  const [vendors, setVendors] = useState<Vendor[]>([])
  const [categories, setCategories] = useState<Category[]>([])
  const [industries, setIndustries] = useState<Industry[]>([])
  const [stats, setStats] = useState<VendorStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)

  // UI State
  const [view, setView] = useState<'list' | 'stats' | 'tiers'>('list')
  const [selectedVendor, setSelectedVendor] = useState<Vendor | null>(null)
  const [isEditing, setIsEditing] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [useSemanticSearch, setUseSemanticSearch] = useState(false)
  const [semanticResults, setSemanticResults] = useState<Array<Vendor & { similarity: number }>>([])
  const [isSemanticSearching, setIsSemanticSearching] = useState(false)

  // Filters from URL
  const categoryFilter = searchParams.get('category') || ''
  const industryFilter = searchParams.get('industry') || ''
  const statusFilter = searchParams.get('status') || ''

  // Load metadata on mount
  useEffect(() => {
    loadCategories()
    loadIndustries()
  }, [])

  // Load vendors when filters change
  useEffect(() => {
    if (view === 'list') {
      loadVendors()
    }
  }, [view, categoryFilter, industryFilter, statusFilter, page])

  // Load stats when showing stats view
  useEffect(() => {
    if (view === 'stats') {
      loadStats()
    }
  }, [view])

  const loadCategories = async () => {
    try {
      const { data } = await apiClient.get<{ categories: Category[] }>('/api/admin/vendors/categories')
      setCategories(data.categories || [])
    } catch (err) {
      console.error('Failed to load categories:', err)
    }
  }

  const loadIndustries = async () => {
    try {
      const { data } = await apiClient.get<{ industries: Industry[] }>('/api/admin/vendors/industries')
      setIndustries(data.industries || [])
    } catch (err) {
      console.error('Failed to load industries:', err)
    }
  }

  const loadVendors = useCallback(async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      if (categoryFilter) params.set('category', categoryFilter)
      if (industryFilter) params.set('industry', industryFilter)
      if (statusFilter) params.set('status', statusFilter)
      if (searchQuery) params.set('search', searchQuery)
      params.set('page', page.toString())
      params.set('page_size', '20')

      const { data } = await apiClient.get<{
        vendors: Vendor[]
        total: number
        has_more: boolean
      }>(`/api/admin/vendors?${params}`)

      setVendors(data.vendors || [])
      setTotal(data.total || 0)
    } catch (err) {
      console.error('Failed to load vendors:', err)
    } finally {
      setLoading(false)
    }
  }, [categoryFilter, industryFilter, statusFilter, searchQuery, page])

  const loadStats = async () => {
    try {
      const { data } = await apiClient.get<VendorStats>('/api/admin/vendors/stats')
      setStats(data)
    } catch (err) {
      console.error('Failed to load stats:', err)
    }
  }

  const handleSearch = () => {
    if (useSemanticSearch && searchQuery.length >= 3) {
      performSemanticSearch()
    } else {
      setSemanticResults([])
      setPage(1)
      loadVendors()
    }
  }

  const performSemanticSearch = async () => {
    if (!searchQuery || searchQuery.length < 3) return

    setIsSemanticSearching(true)
    try {
      const params = new URLSearchParams()
      params.set('query', searchQuery)
      if (categoryFilter) params.set('category', categoryFilter)
      if (industryFilter) params.set('industry', industryFilter)
      params.set('limit', '20')
      params.set('threshold', '0.5')

      const { data } = await apiClient.post<{
        vendors: Array<Vendor & { similarity: number }>
        query: string
        total: number
      }>(`/api/admin/vendors/semantic-search?${params}`)

      setSemanticResults(data.vendors || [])
      setTotal(data.total || 0)
    } catch (err) {
      console.error('Semantic search failed:', err)
      setSemanticResults([])
    } finally {
      setIsSemanticSearching(false)
    }
  }

  const handleFilter = (key: string, value: string) => {
    const params = new URLSearchParams(searchParams)
    if (value) {
      params.set(key, value)
    } else {
      params.delete(key)
    }
    setSearchParams(params)
    setPage(1)
  }

  const handleSelectVendor = async (vendor: Vendor) => {
    // Load full vendor details
    try {
      const { data } = await apiClient.get<{ vendor: Vendor }>(`/api/admin/vendors/${vendor.slug}`)
      setSelectedVendor(data.vendor)
      setIsEditing(true)
    } catch (err) {
      console.error('Failed to load vendor:', err)
    }
  }

  const handleCreateNew = () => {
    setSelectedVendor(null)
    setIsEditing(true)
  }

  const handleSave = async (vendorData: Partial<Vendor>) => {
    if (selectedVendor?.id) {
      // Update existing
      await apiClient.put(`/api/admin/vendors/${selectedVendor.slug}`, vendorData)
    } else {
      // Create new
      await apiClient.post('/api/admin/vendors', vendorData)
    }
    setIsEditing(false)
    setSelectedVendor(null)
    loadVendors()
  }

  const handleDelete = async (vendor: Vendor) => {
    if (!confirm(`Delete "${vendor.name}"? This will mark it as deprecated.`)) return

    await apiClient.delete(`/api/admin/vendors/${vendor.slug}`)
    setIsEditing(false)
    setSelectedVendor(null)
    loadVendors()
  }

  const handleVerify = async (vendor: Vendor) => {
    try {
      await apiClient.post(`/api/admin/vendors/${vendor.slug}/verify`)
      loadVendors()
    } catch (err) {
      console.error('Failed to verify vendor:', err)
    }
  }

  const handleCancel = () => {
    setIsEditing(false)
    setSelectedVendor(null)
  }

  return (
    <div className="min-h-screen bg-gray-50 flex">
      {/* Sidebar */}
      <aside className="w-64 bg-white border-r border-gray-200 p-4 flex flex-col">
        <h1 className="text-lg font-semibold text-gray-900 mb-6">Vendor Admin</h1>

        <nav className="space-y-1 mb-6">
          <button
            onClick={() => setView('list')}
            className={`w-full text-left px-3 py-2 rounded-lg text-sm ${
              view === 'list' ? 'bg-blue-50 text-blue-700' : 'text-gray-600 hover:bg-gray-100'
            }`}
          >
            All Vendors
          </button>
          <button
            onClick={() => setView('tiers')}
            className={`w-full text-left px-3 py-2 rounded-lg text-sm ${
              view === 'tiers' ? 'bg-blue-50 text-blue-700' : 'text-gray-600 hover:bg-gray-100'
            }`}
          >
            Industry Tiers
          </button>
          <button
            onClick={() => setView('stats')}
            className={`w-full text-left px-3 py-2 rounded-lg text-sm ${
              view === 'stats' ? 'bg-blue-50 text-blue-700' : 'text-gray-600 hover:bg-gray-100'
            }`}
          >
            Statistics
          </button>
        </nav>

        {view === 'list' && (
          <>
            <div className="mb-4">
              <label className="block text-xs font-medium text-gray-500 uppercase mb-1">Category</label>
              <select
                value={categoryFilter}
                onChange={(e) => handleFilter('category', e.target.value)}
                className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg"
              >
                <option value="">All Categories</option>
                {categories.map((cat) => (
                  <option key={cat.slug} value={cat.slug}>
                    {cat.name} ({cat.vendor_count})
                  </option>
                ))}
              </select>
            </div>

            <div className="mb-4">
              <label className="block text-xs font-medium text-gray-500 uppercase mb-1">Industry</label>
              <select
                value={industryFilter}
                onChange={(e) => handleFilter('industry', e.target.value)}
                className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg"
              >
                <option value="">All Industries</option>
                {industries.map((ind) => (
                  <option key={ind.slug} value={ind.slug}>
                    {ind.name}
                  </option>
                ))}
              </select>
            </div>

            <div className="mb-4">
              <label className="block text-xs font-medium text-gray-500 uppercase mb-1">Status</label>
              <select
                value={statusFilter}
                onChange={(e) => handleFilter('status', e.target.value)}
                className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg"
              >
                <option value="">Active Only</option>
                <option value="needs_review">Needs Review</option>
                <option value="deprecated">Deprecated</option>
              </select>
            </div>
          </>
        )}

        <div className="mt-auto pt-4 border-t border-gray-200">
          <a href="/admin/knowledge" className="text-sm text-gray-500 hover:text-gray-700">
            ← Knowledge Base
          </a>
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <header className="bg-white border-b border-gray-200 px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <h2 className="text-xl font-semibold text-gray-900">
                {view === 'stats' ? 'Vendor Statistics' : view === 'tiers' ? 'Industry Tiers' : 'Vendors'}
              </h2>
              {view === 'list' && (
                <span className="text-sm text-gray-500">{total} vendors</span>
              )}
            </div>

            <div className="flex items-center gap-4">
              {view === 'list' && (
                <>
                  <div className="flex items-center gap-2">
                    <div className="relative">
                      <input
                        type="text"
                        placeholder={useSemanticSearch ? "Describe what you're looking for..." : "Search vendors..."}
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                        className={`w-72 px-4 py-2 pl-10 text-sm border rounded-lg focus:ring-2 focus:ring-blue-500 ${
                          useSemanticSearch ? 'border-purple-300 bg-purple-50' : 'border-gray-300'
                        }`}
                      />
                      <svg
                        className={`absolute left-3 top-2.5 h-4 w-4 ${useSemanticSearch ? 'text-purple-500' : 'text-gray-400'}`}
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                        />
                      </svg>
                      {isSemanticSearching && (
                        <div className="absolute right-3 top-2.5">
                          <div className="animate-spin h-4 w-4 border-2 border-purple-500 border-t-transparent rounded-full" />
                        </div>
                      )}
                    </div>
                    <button
                      onClick={() => {
                        setUseSemanticSearch(!useSemanticSearch)
                        setSemanticResults([])
                      }}
                      className={`px-3 py-2 text-xs font-medium rounded-lg border transition-colors ${
                        useSemanticSearch
                          ? 'bg-purple-100 text-purple-700 border-purple-300 hover:bg-purple-200'
                          : 'bg-gray-100 text-gray-600 border-gray-300 hover:bg-gray-200'
                      }`}
                      title={useSemanticSearch ? 'Switch to keyword search' : 'Switch to AI semantic search'}
                    >
                      {useSemanticSearch ? '🔮 AI Search' : '🔍 Keyword'}
                    </button>
                  </div>
                  <VendorResearchButtons
                    category={searchParams.get('category') || undefined}
                    industry={searchParams.get('industry') || undefined}
                    onComplete={() => loadVendors()}
                  />
                  <button
                    onClick={handleCreateNew}
                    className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700"
                  >
                    + Add Vendor
                  </button>
                </>
              )}
            </div>
          </div>
        </header>

        {/* Content */}
        <main className="flex-1 overflow-auto p-6">
          {isEditing ? (
            <VendorEditor
              vendor={selectedVendor}
              categories={categories}
              industries={industries}
              onSave={handleSave}
              onDelete={handleDelete}
              onCancel={handleCancel}
            />
          ) : view === 'tiers' ? (
            <IndustryTierManager
              industries={industries}
              onBack={() => setView('list')}
            />
          ) : view === 'stats' ? (
            <VendorStats stats={stats} />
          ) : useSemanticSearch && semanticResults.length > 0 ? (
            /* Semantic Search Results */
            <div className="space-y-3">
              <div className="flex items-center justify-between mb-4">
                <p className="text-sm text-purple-600">
                  🔮 Showing {semanticResults.length} semantic matches for "{searchQuery}"
                </p>
                <button
                  onClick={() => {
                    setSemanticResults([])
                    setSearchQuery('')
                  }}
                  className="text-sm text-gray-500 hover:text-gray-700"
                >
                  Clear
                </button>
              </div>
              {semanticResults.map((vendor) => (
                <div
                  key={vendor.id}
                  onClick={() => handleSelectVendor(vendor)}
                  className="bg-white rounded-xl p-4 border border-gray-100 hover:border-purple-200 hover:shadow-sm cursor-pointer transition-all"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-gray-900">{vendor.name}</span>
                        <span className="text-xs px-2 py-0.5 rounded-full bg-gray-100 text-gray-600">
                          {vendor.category}
                        </span>
                        <span className="text-xs px-2 py-0.5 rounded-full bg-purple-100 text-purple-700">
                          {Math.round(vendor.similarity * 100)}% match
                        </span>
                      </div>
                      {vendor.description && (
                        <p className="text-sm text-gray-500 mt-1 line-clamp-2">{vendor.description}</p>
                      )}
                      {vendor.tagline && !vendor.description && (
                        <p className="text-sm text-gray-500 mt-1">{vendor.tagline}</p>
                      )}
                    </div>
                    {vendor.our_rating && (
                      <div className="text-amber-500 text-sm">★ {vendor.our_rating}</div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : useSemanticSearch && searchQuery.length >= 3 && !isSemanticSearching && semanticResults.length === 0 ? (
            <div className="bg-white rounded-xl p-12 text-center border border-gray-100">
              <p className="text-gray-500">No semantic matches found for "{searchQuery}"</p>
              <p className="text-sm text-gray-400 mt-2">Try a different description or switch to keyword search</p>
            </div>
          ) : (
            <>
              <VendorList
                vendors={vendors}
                loading={loading || isSemanticSearching}
                onSelect={handleSelectVendor}
                onVerify={handleVerify}
              />

              {/* Pagination */}
              {total > 20 && !useSemanticSearch && (
                <div className="mt-6 flex justify-center gap-2">
                  <button
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    disabled={page === 1}
                    className="px-4 py-2 text-sm text-gray-600 hover:bg-gray-100 rounded-lg disabled:opacity-50"
                  >
                    Previous
                  </button>
                  <span className="px-4 py-2 text-sm text-gray-600">
                    Page {page} of {Math.ceil(total / 20)}
                  </span>
                  <button
                    onClick={() => setPage((p) => p + 1)}
                    disabled={page * 20 >= total}
                    className="px-4 py-2 text-sm text-gray-600 hover:bg-gray-100 rounded-lg disabled:opacity-50"
                  >
                    Next
                  </button>
                </div>
              )}
            </>
          )}
        </main>
      </div>
    </div>
  )
}
