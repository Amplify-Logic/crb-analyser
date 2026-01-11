import { ButtonHTMLAttributes, ReactNode } from 'react'

type ButtonVariant = 'primary' | 'secondary' | 'ghost'
type ButtonSize = 'sm' | 'md' | 'lg'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant
  size?: ButtonSize
  isLoading?: boolean
  loadingText?: string
  children: ReactNode
}

const LoadingSpinner = ({ className = 'w-5 h-5' }: { className?: string }) => (
  <svg className={`animate-spin ${className}`} fill="none" viewBox="0 0 24 24">
    <circle
      className="opacity-25"
      cx="12"
      cy="12"
      r="10"
      stroke="currentColor"
      strokeWidth="4"
    />
    <path
      className="opacity-75"
      fill="currentColor"
      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
    />
  </svg>
)

const variantStyles: Record<ButtonVariant, { base: string; disabled: string }> = {
  primary: {
    base: 'bg-primary-600 text-white hover:bg-primary-700 shadow-lg shadow-primary-600/25',
    disabled: 'bg-gray-200 text-gray-400 cursor-not-allowed shadow-none',
  },
  secondary: {
    base: 'bg-white text-gray-700 border border-gray-200 hover:bg-gray-50',
    disabled: 'bg-gray-100 text-gray-400 border-gray-200 cursor-not-allowed',
  },
  ghost: {
    base: 'text-gray-600 hover:text-gray-900 hover:bg-gray-100',
    disabled: 'text-gray-400 cursor-not-allowed',
  },
}

const sizeStyles: Record<ButtonSize, string> = {
  sm: 'px-4 py-2 text-sm rounded-lg',
  md: 'px-6 py-3 text-base rounded-xl',
  lg: 'px-8 py-4 text-lg rounded-xl',
}

export function Button({
  variant = 'primary',
  size = 'md',
  isLoading = false,
  loadingText,
  disabled,
  className = '',
  children,
  ...props
}: ButtonProps) {
  const isDisabled = disabled || isLoading
  const styles = variantStyles[variant]
  const sizeStyle = sizeStyles[size]

  return (
    <button
      disabled={isDisabled}
      className={`
        font-semibold transition-all duration-200
        flex items-center justify-center gap-2
        ${sizeStyle}
        ${isDisabled ? styles.disabled : styles.base}
        ${className}
      `.trim()}
      {...props}
    >
      {isLoading ? (
        <>
          <LoadingSpinner className={size === 'sm' ? 'w-4 h-4' : 'w-5 h-5'} />
          {loadingText || children}
        </>
      ) : (
        children
      )}
    </button>
  )
}

export { LoadingSpinner }
export default Button
