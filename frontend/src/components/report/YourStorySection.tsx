import { motion } from 'framer-motion'

interface YourStorySectionProps {
  keyInsight: string
  findingsCount: number
  mirroredStatements?: string[]
  companyContext: {
    teamSize?: string
    techLevel?: string
    budget?: string
    existingTools?: string[]
  }
}

export default function YourStorySection({
  keyInsight,
  findingsCount,
  mirroredStatements = [],
  companyContext
}: YourStorySectionProps) {
  return (
    <motion.section
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      id="story"
      className="scroll-mt-20"
    >
      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6 md:p-8 mb-6">
        <h2 className="text-sm font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-4">
          Your Story
        </h2>

        {/* The Hook */}
        <div className="bg-gradient-to-r from-primary-50 to-blue-50 dark:from-primary-900/20 dark:to-blue-900/20 rounded-xl p-6 mb-6 border border-primary-200 dark:border-primary-800/30">
          <p className="text-xl md:text-2xl font-semibold text-gray-900 dark:text-white leading-relaxed">
            "{keyInsight}"
          </p>
        </div>

        {/* Journey Indicator */}
        <p className="text-gray-600 dark:text-gray-400 mb-6 flex items-center gap-2">
          <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-primary-100 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400 text-sm font-medium">
            {findingsCount}
          </span>
          <span>high-impact findings from your analysis</span>
        </p>

        {/* What You Told Us */}
        {mirroredStatements.length > 0 && (
          <div className="mb-6">
            <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-3">
              What You Told Us
            </h3>
            <div className="space-y-2">
              {mirroredStatements.map((statement, i) => (
                <p key={i} className="text-gray-700 dark:text-gray-300 italic">
                  "{statement}"
                </p>
              ))}
            </div>
          </div>
        )}

        {/* Your Context */}
        <div>
          <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-3">
            Your Context
          </h3>
          <div className="flex flex-wrap gap-3">
            {companyContext.teamSize && (
              <span className="px-3 py-1.5 bg-gray-100 dark:bg-gray-700 rounded-lg text-sm text-gray-700 dark:text-gray-300">
                {companyContext.teamSize}
              </span>
            )}
            {companyContext.techLevel && (
              <span className="px-3 py-1.5 bg-gray-100 dark:bg-gray-700 rounded-lg text-sm text-gray-700 dark:text-gray-300">
                {companyContext.techLevel} tech comfort
              </span>
            )}
            {companyContext.budget && (
              <span className="px-3 py-1.5 bg-gray-100 dark:bg-gray-700 rounded-lg text-sm text-gray-700 dark:text-gray-300">
                {companyContext.budget} budget
              </span>
            )}
            {companyContext.existingTools?.map((tool, i) => (
              <span key={i} className="px-3 py-1.5 bg-blue-50 dark:bg-blue-900/20 rounded-lg text-sm text-blue-700 dark:text-blue-300">
                Using {tool}
              </span>
            ))}
          </div>
        </div>
      </div>
    </motion.section>
  )
}
