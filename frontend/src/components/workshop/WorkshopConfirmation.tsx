/**
 * WorkshopConfirmation - Phase 1 of the personalized workshop
 *
 * Displays confirmation cards built from quiz + research data.
 * User can mark items as accurate, inaccurate, or edit them.
 * User can also drag to reorder pain points by priority.
 */

import { useState } from 'react'
import { motion, AnimatePresence, Reorder } from 'framer-motion'

// =============================================================================
// Types
// =============================================================================

export interface ConfirmationCard {
  category: string
  title: string
  items: string[]
  sourceCount: number
  editable: boolean
}

export interface ConfirmationRating {
  [category: string]: 'accurate' | 'inaccurate' | 'edited'
}

export interface ConfirmationCorrection {
  field: string
  original: string
  corrected: string
}

interface WorkshopConfirmationProps {
  companyName: string
  cards: ConfirmationCard[]
  painPoints: { id: string; label: string }[]
  onComplete: (data: {
    ratings: ConfirmationRating
    corrections: ConfirmationCorrection[]
    priorityOrder: string[]
  }) => void
  onBack?: () => void
}

// =============================================================================
// Component
// =============================================================================

export default function WorkshopConfirmation({
  companyName,
  cards,
  painPoints,
  onComplete,
  onBack,
}: WorkshopConfirmationProps) {
  const [ratings, setRatings] = useState<ConfirmationRating>({})
  const [corrections, setCorrections] = useState<ConfirmationCorrection[]>([])
  const [editingCard, setEditingCard] = useState<string | null>(null)
  const [editedItems, setEditedItems] = useState<{ [category: string]: string[] }>({})
  const [orderedPainPoints, setOrderedPainPoints] = useState(painPoints)
  const [isSubmitting, setIsSubmitting] = useState(false)

  // Check if all cards are rated
  const allRated = cards.every(card => ratings[card.category])
  const canContinue = allRated && orderedPainPoints.length > 0

  const handleRating = (category: string, rating: 'accurate' | 'inaccurate' | 'edited') => {
    setRatings(prev => ({ ...prev, [category]: rating }))

    if (rating === 'inaccurate') {
      // Open edit mode for this card
      setEditingCard(category)
    }
  }

  const handleSaveEdit = (category: string, newItems: string[]) => {
    const card = cards.find(c => c.category === category)
    if (card) {
      // Record corrections
      const newCorrections: ConfirmationCorrection[] = card.items
        .map((original, i) => ({
          field: category,
          original,
          corrected: newItems[i] || original,
        }))
        .filter(c => c.original !== c.corrected)

      setCorrections(prev => [...prev.filter(c => c.field !== category), ...newCorrections])
      setEditedItems(prev => ({ ...prev, [category]: newItems }))
      setRatings(prev => ({ ...prev, [category]: 'edited' }))
    }
    setEditingCard(null)
  }

  const handleSubmit = async () => {
    if (!canContinue) return

    setIsSubmitting(true)

    onComplete({
      ratings,
      corrections,
      priorityOrder: orderedPainPoints.map(p => p.id),
    })
  }

  const getDisplayItems = (card: ConfirmationCard) => {
    return editedItems[card.category] || card.items
  }

  const getRatingIcon = (rating?: string) => {
    switch (rating) {
      case 'accurate':
        return (
          <svg className="w-5 h-5 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        )
      case 'inaccurate':
        return (
          <svg className="w-5 h-5 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        )
      case 'edited':
        return (
          <svg className="w-5 h-5 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
          </svg>
        )
      default:
        return null
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white pb-32">
      {/* Header */}
      <div className="bg-white border-b border-gray-100 sticky top-0 z-10">
        <div className="max-w-3xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-xl font-bold text-gray-900">
                Let's Confirm What We Know
              </h1>
              <p className="text-sm text-gray-500">
                Review and verify our research about {companyName}
              </p>
            </div>
            <div className="text-sm text-gray-400">
              Phase 1 of 3
            </div>
          </div>

          {/* Progress indicator */}
          <div className="mt-4 flex items-center gap-2">
            {cards.map((card) => (
              <div
                key={card.category}
                className={`h-1.5 flex-1 rounded-full transition-colors ${
                  ratings[card.category]
                    ? ratings[card.category] === 'accurate'
                      ? 'bg-green-500'
                      : ratings[card.category] === 'edited'
                      ? 'bg-blue-500'
                      : 'bg-yellow-500'
                    : 'bg-gray-200'
                }`}
              />
            ))}
          </div>
        </div>
      </div>

      {/* Cards */}
      <div className="max-w-3xl mx-auto px-4 py-8 space-y-6">
        <AnimatePresence>
          {cards.map((card, index) => (
            <motion.div
              key={card.category}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden"
            >
              {/* Card header */}
              <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <h3 className="font-semibold text-gray-900">{card.title}</h3>
                  {getRatingIcon(ratings[card.category])}
                </div>
                <span className="text-xs text-gray-400">
                  {card.sourceCount} source{card.sourceCount !== 1 ? 's' : ''}
                </span>
              </div>

              {/* Card content */}
              <div className="px-6 py-4">
                {editingCard === card.category ? (
                  <EditableCardContent
                    items={getDisplayItems(card)}
                    onSave={(items) => handleSaveEdit(card.category, items)}
                    onCancel={() => setEditingCard(null)}
                  />
                ) : (
                  <ul className="space-y-2">
                    {getDisplayItems(card).map((item, idx) => (
                      <li key={idx} className="flex items-start gap-2">
                        <span className="text-primary-600 mt-1">•</span>
                        <span className="text-gray-700">{item}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>

              {/* Card actions */}
              {editingCard !== card.category && (
                <div className="px-6 py-4 bg-gray-50 flex items-center gap-3">
                  <span className="text-sm text-gray-500">Is this accurate?</span>
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleRating(card.category, 'accurate')}
                      className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
                        ratings[card.category] === 'accurate'
                          ? 'bg-green-100 text-green-700 ring-2 ring-green-500'
                          : 'bg-white border border-gray-200 text-gray-700 hover:bg-gray-50'
                      }`}
                    >
                      Yes, accurate
                    </button>
                    <button
                      onClick={() => handleRating(card.category, 'inaccurate')}
                      className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
                        ratings[card.category] === 'inaccurate' || ratings[card.category] === 'edited'
                          ? 'bg-blue-100 text-blue-700 ring-2 ring-blue-500'
                          : 'bg-white border border-gray-200 text-gray-700 hover:bg-gray-50'
                      }`}
                    >
                      Edit this
                    </button>
                  </div>
                </div>
              )}
            </motion.div>
          ))}
        </AnimatePresence>

        {/* Pain Point Prioritization */}
        {painPoints.length > 1 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: cards.length * 0.1 }}
            className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden"
          >
            <div className="px-6 py-4 border-b border-gray-100">
              <h3 className="font-semibold text-gray-900">Prioritize Your Pain Points</h3>
              <p className="text-sm text-gray-500 mt-1">
                Drag to reorder. We'll focus on the top ones first.
              </p>
            </div>

            <div className="p-4">
              <Reorder.Group
                axis="y"
                values={orderedPainPoints}
                onReorder={setOrderedPainPoints}
                className="space-y-2"
              >
                {orderedPainPoints.map((painPoint, index) => (
                  <Reorder.Item
                    key={painPoint.id}
                    value={painPoint}
                    className="bg-gray-50 rounded-lg px-4 py-3 flex items-center gap-3 cursor-grab active:cursor-grabbing"
                  >
                    <span className="w-6 h-6 bg-primary-100 text-primary-600 rounded-full flex items-center justify-center text-sm font-medium">
                      {index + 1}
                    </span>
                    <span className="flex-1 text-gray-700">{painPoint.label}</span>
                    <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8h16M4 16h16" />
                    </svg>
                  </Reorder.Item>
                ))}
              </Reorder.Group>
            </div>
          </motion.div>
        )}
      </div>

      {/* Footer */}
      <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 p-4">
        <div className="max-w-3xl mx-auto flex justify-between items-center">
          {onBack && (
            <button
              onClick={onBack}
              className="text-gray-500 hover:text-gray-700"
            >
              Back
            </button>
          )}
          <div className="flex-1" />
          <button
            onClick={handleSubmit}
            disabled={!canContinue || isSubmitting}
            className={`px-6 py-3 rounded-xl font-medium transition ${
              canContinue && !isSubmitting
                ? 'bg-primary-600 text-white hover:bg-primary-700'
                : 'bg-gray-200 text-gray-400 cursor-not-allowed'
            }`}
          >
            {isSubmitting ? 'Saving...' : 'Continue to Deep-Dive'}
          </button>
        </div>
      </div>
    </div>
  )
}

// =============================================================================
// Sub-components
// =============================================================================

interface EditableCardContentProps {
  items: string[]
  onSave: (items: string[]) => void
  onCancel: () => void
}

function EditableCardContent({ items, onSave, onCancel }: EditableCardContentProps) {
  const [editedItems, setEditedItems] = useState(items)

  const handleItemChange = (index: number, value: string) => {
    setEditedItems(prev => {
      const updated = [...prev]
      updated[index] = value
      return updated
    })
  }

  const handleAddItem = () => {
    setEditedItems(prev => [...prev, ''])
  }

  const handleRemoveItem = (index: number) => {
    setEditedItems(prev => prev.filter((_, i) => i !== index))
  }

  return (
    <div className="space-y-3">
      {editedItems.map((item, index) => (
        <div key={index} className="flex items-center gap-2">
          <input
            type="text"
            value={item}
            onChange={(e) => handleItemChange(index, e.target.value)}
            className="flex-1 px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            placeholder="Enter item..."
          />
          <button
            onClick={() => handleRemoveItem(index)}
            className="p-2 text-gray-400 hover:text-red-500"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </button>
        </div>
      ))}

      <button
        onClick={handleAddItem}
        className="text-sm text-primary-600 hover:text-primary-700 flex items-center gap-1"
      >
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
        </svg>
        Add item
      </button>

      <div className="flex justify-end gap-2 pt-2">
        <button
          onClick={onCancel}
          className="px-4 py-2 text-gray-600 hover:text-gray-800"
        >
          Cancel
        </button>
        <button
          onClick={() => onSave(editedItems.filter(i => i.trim()))}
          className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
        >
          Save Changes
        </button>
      </div>
    </div>
  )
}
