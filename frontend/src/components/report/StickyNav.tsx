interface NavSection {
  id: string
  label: string
}

interface StickyNavProps {
  sections: NavSection[]
  activeSection: string
  onSectionClick: (id: string) => void
}

export default function StickyNav({ sections, activeSection, onSectionClick }: StickyNavProps) {
  return (
    <nav className="sticky top-[72px] z-10 bg-white/95 dark:bg-gray-800/95 backdrop-blur-sm border-b border-gray-200 dark:border-gray-700 -mx-4 px-4">
      <div className="max-w-4xl mx-auto">
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
    </nav>
  )
}
