import { useState } from 'react'
import { Link } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'

interface NavSection {
  id: string
  label: string
}

interface PersonalizedHeaderProps {
  companyName: string
  industry: string
  teamSize: string
  techLevel: string
  budgetRange: string
  tier: 'quick' | 'full'
  onExportPDF: () => void
  sections?: NavSection[]
  activeSection?: string
  onSectionClick?: (id: string) => void
}

export default function PersonalizedHeader({
  companyName,
  industry,
  teamSize,
  techLevel,
  budgetRange,
  tier,
  onExportPDF,
  sections,
  activeSection,
  onSectionClick
}: PersonalizedHeaderProps) {
  const [isCollapsed, setIsCollapsed] = useState(false)

  return (
    <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-md border-b border-white/20 dark:border-gray-700 sticky top-0 z-20">
      <div className="max-w-4xl mx-auto px-4 py-3">
        {/* Logo Row - Always visible */}
        <div className="flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2">
            <div className="w-8 h-8 bg-gradient-to-br from-primary-500 to-primary-700 rounded-lg flex items-center justify-center text-white shadow-lg shadow-primary-500/30">
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <div className="flex flex-col">
              <span className="text-xl font-bold text-gray-900 dark:text-white tracking-tight leading-tight">Ready<span className="text-primary-600">Path</span></span>
              <span className="text-[10px] text-gray-400 font-medium -mt-0.5">by Amplify Logic AI</span>
            </div>
          </Link>

          <div className="flex items-center gap-2">
            {/* Collapse/Expand Arrow */}
            <button
              onClick={() => setIsCollapsed(!isCollapsed)}
              className="p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-all"
              aria-label={isCollapsed ? 'Expand header' : 'Collapse header'}
            >
              <svg
                className={`w-5 h-5 transition-transform duration-200 ${isCollapsed ? 'rotate-180' : ''}`}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
              </svg>
            </button>

            {/* Export PDF Button */}
            <button
              onClick={onExportPDF}
              className={`
                ${isCollapsed
                  ? 'p-2.5 rounded-lg'
                  : 'px-4 py-2.5 rounded-xl'
                }
                bg-gradient-to-r from-primary-600 to-indigo-600 hover:from-primary-700 hover:to-indigo-700
                text-white font-medium transition-all flex items-center gap-2 text-sm
                shadow-lg shadow-primary-500/25 hover:shadow-primary-500/40 hover:scale-105
              `}
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
              {!isCollapsed && <span className="hidden sm:inline">Export PDF</span>}
            </button>
          </div>
        </div>

        {/* Report Info Row - Collapsible */}
        <AnimatePresence>
          {!isCollapsed && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="overflow-hidden"
            >
              <div className="flex items-start justify-between pt-4">
                <div>
                  <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">
                    AI Readiness Report for
                  </p>
                  <h1 className="text-2xl md:text-3xl font-bold text-gray-900 dark:text-white mb-2 tracking-tight">
                    {companyName || 'Your Business'}
                  </h1>
                  <div className="flex flex-wrap items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
                    {teamSize && <span className="bg-gray-100 dark:bg-gray-700 px-2 py-0.5 rounded-md">{teamSize}</span>}
                    {industry && <span className="bg-gray-100 dark:bg-gray-700 px-2 py-0.5 rounded-md">{industry}</span>}
                    {techLevel && <span className="bg-gray-100 dark:bg-gray-700 px-2 py-0.5 rounded-md">{techLevel} tech comfort</span>}
                    {budgetRange && <span className="bg-gray-100 dark:bg-gray-700 px-2 py-0.5 rounded-md">{budgetRange}</span>}
                  </div>
                </div>
                {tier && (
                  <span className={`px-3 py-1 text-xs font-semibold rounded-full flex-shrink-0 ${
                    tier === 'full'
                      ? 'bg-gradient-to-r from-primary-100 to-indigo-100 text-primary-700 border border-primary-200'
                      : 'bg-gray-100 text-gray-600 border border-gray-200'
                  }`}>
                    {tier === 'full' ? 'Full Report' : 'Quick Report'}
                  </span>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Navigation - Always visible */}
      {sections && sections.length > 0 && onSectionClick && (
        <div className="border-t border-gray-200/50 dark:border-gray-700/50 bg-white/50 dark:bg-gray-800/50">
          <div className="max-w-4xl mx-auto px-4">
            <div className="flex gap-1 overflow-x-auto py-2 scrollbar-hide">
              {sections.map((section) => (
                <button
                  key={section.id}
                  onClick={() => onSectionClick(section.id)}
                  className={`
                    px-4 py-2 font-medium text-sm rounded-lg transition-colors whitespace-nowrap
                    ${activeSection === section.id
                      ? 'bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300'
                      : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
                    }
                  `}
                >
                  {section.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
