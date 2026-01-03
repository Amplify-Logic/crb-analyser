/**
 * Knowledge Editor Component
 *
 * Hybrid editor with form fields for common properties
 * and JSON editor for advanced metadata.
 */

import { useState, useEffect } from 'react'
import { KnowledgeItem } from '../../pages/admin/KnowledgeBase'

interface KnowledgeEditorProps {
  item: KnowledgeItem
  onSave: (item: KnowledgeItem) => Promise<void>
  onCancel: () => void
  onDelete: (item: KnowledgeItem) => void
  onReembed: (item: KnowledgeItem) => void
}

const INDUSTRIES = [
  'dental',
  'home-services',
  'professional-services',
  'recruiting',
  'coaching',
  'veterinary',
]

function formatDate(dateString?: string): string {
  if (!dateString) return 'Never'
  return new Date(dateString).toLocaleString()
}

export default function KnowledgeEditor({
  item,
  onSave,
  onCancel,
  onDelete,
  onReembed,
}: KnowledgeEditorProps) {
  const [formData, setFormData] = useState<KnowledgeItem>(item)
  const [metadataJson, setMetadataJson] = useState('')
  const [jsonError, setJsonError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false)

  const DRAFT_KEY = `kb-draft-${item.content_type}-${item.content_id || 'new'}`

  // Load item or restore draft
  useEffect(() => {
    const savedDraft = localStorage.getItem(DRAFT_KEY)
    if (savedDraft && !item.id) {
      try {
        const draft = JSON.parse(savedDraft)
        setFormData(draft)
        setMetadataJson(JSON.stringify(draft.metadata || {}, null, 2))
        setHasUnsavedChanges(true)
      } catch {
        setFormData(item)
        setMetadataJson(JSON.stringify(item.metadata || {}, null, 2))
      }
    } else {
      setFormData(item)
      setMetadataJson(JSON.stringify(item.metadata || {}, null, 2))
    }
    setJsonError(null)
  }, [item, DRAFT_KEY])

  // Auto-save draft to localStorage
  useEffect(() => {
    if (hasUnsavedChanges) {
      const timeoutId = setTimeout(() => {
        localStorage.setItem(DRAFT_KEY, JSON.stringify(formData))
      }, 1000)
      return () => clearTimeout(timeoutId)
    }
  }, [formData, hasUnsavedChanges, DRAFT_KEY])

  function handleFieldChange(field: keyof KnowledgeItem, value: any) {
    setFormData((prev) => ({ ...prev, [field]: value }))
    setHasUnsavedChanges(true)
  }

  function handleMetadataChange(json: string) {
    setMetadataJson(json)
    setHasUnsavedChanges(true)
    try {
      const parsed = JSON.parse(json)
      setFormData((prev) => ({ ...prev, metadata: parsed }))
      setJsonError(null)
    } catch (e) {
      setJsonError('Invalid JSON')
    }
  }

  function clearDraft() {
    localStorage.removeItem(DRAFT_KEY)
    setHasUnsavedChanges(false)
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (jsonError) return

    setSaving(true)
    try {
      await onSave(formData)
      clearDraft() // Clear draft on successful save
    } catch (err) {
      console.error('Save failed:', err)
    } finally {
      setSaving(false)
    }
  }

  const isNew = !item.id

  return (
    <form onSubmit={handleSubmit} className="bg-white rounded-xl shadow-sm">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
        <div className="flex items-center gap-3">
          <h2 className="text-lg font-semibold text-gray-900">
            {isNew ? 'Create New Item' : `Edit: ${item.title || item.content_id}`}
          </h2>
          {hasUnsavedChanges && (
            <span className="text-xs px-2 py-0.5 bg-amber-100 text-amber-700 rounded-full">
              Draft saved
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          {hasUnsavedChanges && (
            <button
              type="button"
              onClick={() => {
                clearDraft()
                setFormData(item)
                setMetadataJson(JSON.stringify(item.metadata || {}, null, 2))
              }}
              className="px-3 py-2 text-sm text-amber-600 hover:bg-amber-50 rounded-lg transition-colors"
            >
              Discard Draft
            </button>
          )}
          <button
            type="button"
            onClick={onCancel}
            className="px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 rounded-lg transition-colors"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={saving || !!jsonError}
            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors disabled:opacity-50"
          >
            {saving ? 'Saving...' : 'Save'}
          </button>
        </div>
      </div>

      {/* Form Body */}
      <div className="p-6 space-y-6">
        {/* Basic Fields */}
        <div className="grid grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Content ID *
            </label>
            <input
              type="text"
              value={formData.content_id}
              onChange={(e) => handleFieldChange('content_id', e.target.value)}
              disabled={!isNew}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-50 disabled:text-gray-500"
              placeholder="e.g., hubspot-crm"
            />
            {isNew && (
              <p className="mt-1 text-xs text-gray-500">
                Unique identifier (slug format recommended)
              </p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Industry
            </label>
            <select
              value={formData.industry || ''}
              onChange={(e) => handleFieldChange('industry', e.target.value || undefined)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="">All Industries</option>
              {INDUSTRIES.map((ind) => (
                <option key={ind} value={ind}>
                  {ind.replace(/-/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Title *
          </label>
          <input
            type="text"
            value={formData.title}
            onChange={(e) => handleFieldChange('title', e.target.value)}
            required
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="Enter a descriptive title"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Content *
          </label>
          <textarea
            value={formData.content}
            onChange={(e) => handleFieldChange('content', e.target.value)}
            required
            rows={8}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono text-sm"
            placeholder="Main content that will be embedded for semantic search..."
          />
          <p className="mt-1 text-xs text-gray-500">
            This content will be vectorized for semantic search
          </p>
        </div>

        {/* Advanced: JSON Metadata */}
        <div>
          <button
            type="button"
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="flex items-center gap-2 text-sm font-medium text-gray-700 hover:text-gray-900"
          >
            <span>{showAdvanced ? '▼' : '▶'}</span>
            <span>Advanced: JSON Metadata</span>
          </button>

          {showAdvanced && (
            <div className="mt-3">
              <textarea
                value={metadataJson}
                onChange={(e) => handleMetadataChange(e.target.value)}
                rows={10}
                className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono text-sm ${
                  jsonError ? 'border-red-300 bg-red-50' : 'border-gray-300'
                }`}
              />
              {jsonError && (
                <p className="mt-1 text-xs text-red-600">{jsonError}</p>
              )}
              <p className="mt-1 text-xs text-gray-500">
                Additional structured data (pricing, features, integrations, etc.)
              </p>
            </div>
          )}
        </div>

        {/* Embedding Status */}
        {!isNew && (
          <div className="bg-gray-50 rounded-lg p-4">
            <h3 className="text-sm font-medium text-gray-700 mb-3">
              Embedding Status
            </h3>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2">
                  {item.is_embedded ? (
                    <>
                      <span className="w-2.5 h-2.5 rounded-full bg-green-500" />
                      <span className="text-sm text-gray-700">
                        Embedded: {formatDate(item.embedded_at)}
                      </span>
                    </>
                  ) : (
                    <>
                      <span className="w-2.5 h-2.5 rounded-full bg-gray-300" />
                      <span className="text-sm text-gray-500">Not embedded</span>
                    </>
                  )}
                </div>
                {item.needs_update && (
                  <span className="text-xs px-2 py-0.5 bg-amber-100 text-amber-700 rounded-full">
                    Content changed - needs re-embedding
                  </span>
                )}
              </div>
              <button
                type="button"
                onClick={() => onReembed(item)}
                className="px-3 py-1.5 text-sm text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
              >
                {item.is_embedded ? 'Re-embed Now' : 'Embed Now'}
              </button>
            </div>
          </div>
        )}

        {/* Delete Button */}
        {!isNew && (
          <div className="pt-4 border-t border-gray-200">
            <button
              type="button"
              onClick={() => onDelete(item)}
              className="px-4 py-2 text-sm text-red-600 hover:bg-red-50 rounded-lg transition-colors"
            >
              Delete Item
            </button>
          </div>
        )}
      </div>
    </form>
  )
}
