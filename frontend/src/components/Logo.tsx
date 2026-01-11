import { Link } from 'react-router-dom'

interface LogoProps {
  /** Size variant */
  size?: 'sm' | 'md' | 'lg'
  /** Whether to show the icon */
  showIcon?: boolean
  /** Whether to link to home page */
  linkToHome?: boolean
  /** Dark variant for use on dark backgrounds */
  variant?: 'light' | 'dark'
  /** Custom className for the container */
  className?: string
}

const sizeConfig = {
  sm: {
    icon: 'w-8 h-8 rounded-lg',
    iconSvg: 'w-5 h-5',
    text: 'text-xl',
    subtitle: 'text-[10px] -mt-0.5',
  },
  md: {
    icon: 'w-10 h-10 rounded-xl',
    iconSvg: 'w-6 h-6',
    text: 'text-2xl',
    subtitle: 'text-[10px] -mt-0.5',
  },
  lg: {
    icon: 'w-12 h-12 rounded-xl',
    iconSvg: 'w-7 h-7',
    text: 'text-3xl',
    subtitle: 'text-xs -mt-0.5',
  },
}

export function Logo({ size = 'sm', showIcon = true, linkToHome = true, variant = 'light', className = '' }: LogoProps) {
  const config = sizeConfig[size]
  const isDark = variant === 'dark'

  const content = (
    <div className={`flex items-center gap-2 ${className}`}>
      {showIcon && (
        <div className={`${config.icon} bg-gradient-to-br from-primary-500 to-primary-700 flex items-center justify-center text-white shadow-lg shadow-primary-500/30`}>
          <svg className={config.iconSvg} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
        </div>
      )}
      <div className="flex flex-col">
        <span className={`${config.text} font-bold tracking-tight leading-tight ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Ready<span className={isDark ? 'text-primary-300' : 'text-primary-600'}>Path</span>
        </span>
        <span className={`${config.subtitle} font-medium ${isDark ? 'text-primary-300' : 'text-gray-400'}`}>by Amplify Logic AI</span>
      </div>
    </div>
  )

  if (linkToHome) {
    return <Link to="/">{content}</Link>
  }

  return content
}

export default Logo
