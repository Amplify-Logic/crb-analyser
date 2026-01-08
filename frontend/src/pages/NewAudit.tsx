import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import apiClient from '../services/apiClient'

interface Client {
  id: string
  name: string
  industry: string
  company_size?: string
}

interface Tier {
  id: string
  name: string
  price: number
  description: string
  features: string[]
}

const TIERS: Tier[] = [
  {
    id: 'free',
    name: 'Free Assessment',
    price: 0,
    description: 'Get your AI Readiness Score',
    features: [
      'AI Readiness Score (0-100)',
      '3 finding titles (preview)',
      'Upgrade path to full report',
    ],
  },
  {
    id: 'professional',
    name: 'Professional Audit',
    price: 497,
    description: 'Complete AI readiness analysis with actionable insights',
    features: [
      'Full AI Readiness Score',
      '15-20 detailed findings',
      'ROI calculations for each recommendation',
      'Vendor comparisons',
      'Implementation roadmap',
      'PDF + Web report',
      'Raw data export',
    ],
  },
]

const INDUSTRIES = [
  { value: 'marketing_agency', label: 'Marketing/Creative Agency' },
  { value: 'retail', label: 'Retail' },
  { value: 'ecommerce', label: 'E-Commerce' },
  { value: 'tech_company', label: 'Tech Company' },
  { value: 'music_company', label: 'Music Company/Studio' },
  { value: 'other', label: 'Other' },
]

const COMPANY_SIZES = [
  { value: 'solo', label: 'Just me (solo)' },
  { value: '2-10', label: '2-10 employees' },
  { value: '11-50', label: '11-50 employees' },
  { value: '51-200', label: '51-200 employees' },
  { value: '200+', label: '200+ employees' },
]

export default function NewAudit() {
  const navigate = useNavigate()
  const [step, setStep] = useState<'client' | 'tier'>('client')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  // Client selection
  const [clients, setClients] = useState<Client[]>([])
  const [selectedClient, setSelectedClient] = useState<string | null>(null)
  const [createNew, setCreateNew] = useState(false)

  // New client form
  const [newClient, setNewClient] = useState({
    name: '',
    industry: '',
    company_size: '',
    website: '',
    contact_email: '',
  })

  // Tier selection
  const [selectedTier, setSelectedTier] = useState<string>('professional')

  useEffect(() => {
    loadClients()
  }, [])

  async function loadClients() {
    try {
      const { data } = await apiClient.get<{ data: Client[] }>('/api/clients')
      setClients(data.data || [])
    } catch (err) {
      console.error('Failed to load clients:', err)
    }
  }

  async function handleCreateClient() {
    if (!newClient.name || !newClient.industry) {
      setError('Please fill in required fields')
      return
    }

    setLoading(true)
    setError('')

    try {
      // Remove empty strings - backend expects null for optional fields
      const clientData = Object.fromEntries(
        Object.entries(newClient).filter(([_, v]) => v !== '')
      )
      const { data } = await apiClient.post<Client>('/api/clients', clientData)
      setClients([...clients, data])
      setSelectedClient(data.id)
      setCreateNew(false)
      setStep('tier')
    } catch (err: any) {
      setError(err.message || 'Failed to create client')
    } finally {
      setLoading(false)
    }
  }

  async function handleCreateAudit() {
    if (!selectedClient) {
      setError('Please select a client')
      return
    }

    setLoading(true)
    setError('')

    try {
      const client = clients.find((c) => c.id === selectedClient)
      const { data } = await apiClient.post<{ id: string }>('/api/audits', {
        client_id: selectedClient,
        tier: selectedTier,
        title: `${client?.name} - AI Readiness Audit`,
      })

      // Navigate to intake wizard
      navigate(`/audit/${data.id}/intake`)
    } catch (err: any) {
      setError(err.message || 'Failed to create audit')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="max-w-3xl mx-auto px-4">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">New Audit</h1>
          <p className="text-gray-600 mt-2">
            Start a new Cost/Risk/Benefit analysis
          </p>
        </div>

        {/* Progress indicator */}
        <div className="flex items-center mb-8">
          <div
            className={`flex items-center justify-center w-10 h-10 rounded-full ${
              step === 'client'
                ? 'bg-primary-600 text-white'
                : 'bg-primary-100 text-primary-600'
            }`}
          >
            1
          </div>
          <div
            className={`flex-1 h-1 mx-2 ${
              step === 'tier' ? 'bg-primary-600' : 'bg-gray-200'
            }`}
          />
          <div
            className={`flex items-center justify-center w-10 h-10 rounded-full ${
              step === 'tier'
                ? 'bg-primary-600 text-white'
                : 'bg-gray-200 text-gray-400'
            }`}
          >
            2
          </div>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl text-red-700">
            {error}
          </div>
        )}

        {/* Step 1: Select Client */}
        {step === 'client' && (
          <div className="bg-white rounded-2xl shadow-sm p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              Select or Create Client
            </h2>

            {!createNew && (
              <>
                {clients.length > 0 && (
                  <div className="space-y-3 mb-6">
                    {clients.map((client) => (
                      <label
                        key={client.id}
                        className={`flex items-center p-4 rounded-xl border-2 cursor-pointer transition ${
                          selectedClient === client.id
                            ? 'border-primary-600 bg-primary-50'
                            : 'border-gray-200 hover:border-gray-300'
                        }`}
                      >
                        <input
                          type="radio"
                          name="client"
                          value={client.id}
                          checked={selectedClient === client.id}
                          onChange={() => setSelectedClient(client.id)}
                          className="sr-only"
                        />
                        <div>
                          <p className="font-medium text-gray-900">
                            {client.name}
                          </p>
                          <p className="text-sm text-gray-500">
                            {client.industry} {client.company_size && `• ${client.company_size}`}
                          </p>
                        </div>
                      </label>
                    ))}
                  </div>
                )}

                <button
                  onClick={() => setCreateNew(true)}
                  className="w-full py-3 border-2 border-dashed border-gray-300 rounded-xl text-gray-600 hover:border-primary-600 hover:text-primary-600 transition"
                >
                  + Add New Client
                </button>

                {selectedClient && (
                  <button
                    onClick={() => setStep('tier')}
                    className="w-full mt-6 py-3 bg-primary-600 text-white font-semibold rounded-xl hover:bg-primary-700 transition"
                  >
                    Continue
                  </button>
                )}
              </>
            )}

            {createNew && (
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Company Name *
                  </label>
                  <input
                    type="text"
                    value={newClient.name}
                    onChange={(e) =>
                      setNewClient({ ...newClient, name: e.target.value })
                    }
                    className="w-full px-4 py-2 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                    placeholder="Acme Corp"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Industry *
                  </label>
                  <select
                    value={newClient.industry}
                    onChange={(e) =>
                      setNewClient({ ...newClient, industry: e.target.value })
                    }
                    className="w-full px-4 py-2 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  >
                    <option value="">Select industry</option>
                    {INDUSTRIES.map((ind) => (
                      <option key={ind.value} value={ind.value}>
                        {ind.label}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Company Size
                  </label>
                  <select
                    value={newClient.company_size}
                    onChange={(e) =>
                      setNewClient({ ...newClient, company_size: e.target.value })
                    }
                    className="w-full px-4 py-2 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  >
                    <option value="">Select size</option>
                    {COMPANY_SIZES.map((size) => (
                      <option key={size.value} value={size.value}>
                        {size.label}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Website
                  </label>
                  <input
                    type="url"
                    value={newClient.website}
                    onChange={(e) =>
                      setNewClient({ ...newClient, website: e.target.value })
                    }
                    className="w-full px-4 py-2 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                    placeholder="https://example.com"
                  />
                </div>

                <div className="flex gap-3 pt-4">
                  <button
                    onClick={() => setCreateNew(false)}
                    className="flex-1 py-3 border border-gray-300 text-gray-700 font-semibold rounded-xl hover:bg-gray-50 transition"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleCreateClient}
                    disabled={loading}
                    className="flex-1 py-3 bg-primary-600 text-white font-semibold rounded-xl hover:bg-primary-700 transition disabled:opacity-50"
                  >
                    {loading ? 'Creating...' : 'Create Client'}
                  </button>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Step 2: Select Tier */}
        {step === 'tier' && (
          <div className="bg-white rounded-2xl shadow-sm p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              Select Audit Tier
            </h2>

            <div className="space-y-4">
              {TIERS.map((tier) => (
                <label
                  key={tier.id}
                  className={`block p-6 rounded-xl border-2 cursor-pointer transition ${
                    selectedTier === tier.id
                      ? 'border-primary-600 bg-primary-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <input
                    type="radio"
                    name="tier"
                    value={tier.id}
                    checked={selectedTier === tier.id}
                    onChange={() => setSelectedTier(tier.id)}
                    className="sr-only"
                  />
                  <div className="flex justify-between items-start mb-3">
                    <div>
                      <h3 className="font-semibold text-gray-900">{tier.name}</h3>
                      <p className="text-sm text-gray-500">{tier.description}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-2xl font-bold text-gray-900">
                        {tier.price === 0 ? 'Free' : `€${tier.price}`}
                      </p>
                      {tier.id === 'professional' && (
                        <p className="text-xs text-green-600">Early bird pricing</p>
                      )}
                    </div>
                  </div>
                  <ul className="space-y-2">
                    {tier.features.map((feature, i) => (
                      <li key={i} className="flex items-center text-sm text-gray-600">
                        <svg
                          className="w-4 h-4 mr-2 text-green-500"
                          fill="currentColor"
                          viewBox="0 0 20 20"
                        >
                          <path
                            fillRule="evenodd"
                            d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                            clipRule="evenodd"
                          />
                        </svg>
                        {feature}
                      </li>
                    ))}
                  </ul>
                </label>
              ))}
            </div>

            <div className="flex gap-3 mt-6">
              <button
                onClick={() => setStep('client')}
                className="flex-1 py-3 border border-gray-300 text-gray-700 font-semibold rounded-xl hover:bg-gray-50 transition"
              >
                Back
              </button>
              <button
                onClick={handleCreateAudit}
                disabled={loading}
                className="flex-1 py-3 bg-primary-600 text-white font-semibold rounded-xl hover:bg-primary-700 transition disabled:opacity-50"
              >
                {loading ? 'Creating...' : 'Start Audit'}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
