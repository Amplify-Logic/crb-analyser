/**
 * StructuredInput Component
 *
 * Renders different input types for adaptive quiz questions:
 * - Select (single choice)
 * - MultiSelect (multiple choices)
 * - Number (numeric input with optional range)
 * - Scale (1-5 or 1-10 rating)
 * - Text (short text answer)
 */

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

interface Option {
  value: string
  label: string
  description?: string
}

interface StructuredInputProps {
  inputType: 'select' | 'multi_select' | 'number' | 'scale' | 'text'
  options?: Option[]
  placeholder?: string
  value: string | string[] | number
  onChange: (value: string | string[] | number) => void
  onSubmit: () => void
  disabled?: boolean
  scaleMax?: number
  numberMin?: number
  numberMax?: number
  numberStep?: number
  numberUnit?: string
}

export default function StructuredInput({
  inputType,
  options = [],
  placeholder,
  value,
  onChange,
  onSubmit,
  disabled = false,
  scaleMax = 5,
  numberMin,
  numberMax,
  numberStep = 1,
  numberUnit,
}: StructuredInputProps) {
  const [isValid, setIsValid] = useState(false)

  const handleSelectChange = (optionValue: string) => {
    onChange(optionValue)
    setIsValid(true)
  }

  const handleMultiSelectChange = (optionValue: string) => {
    const currentValues = Array.isArray(value) ? value : []
    const newValues = currentValues.includes(optionValue)
      ? currentValues.filter(v => v !== optionValue)
      : [...currentValues, optionValue]
    onChange(newValues)
    setIsValid(newValues.length > 0)
  }

  const handleNumberChange = (numValue: string) => {
    const parsed = parseFloat(numValue)
    if (!isNaN(parsed)) {
      onChange(parsed)
      setIsValid(true)
    } else if (numValue === '') {
      onChange('')
      setIsValid(false)
    }
  }

  const handleScaleChange = (scaleValue: number) => {
    onChange(scaleValue)
    setIsValid(true)
  }

  const handleTextChange = (textValue: string) => {
    onChange(textValue)
    setIsValid(textValue.trim().length > 0)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey && isValid) {
      e.preventDefault()
      onSubmit()
    }
  }

  // Select input (single choice)
  if (inputType === 'select') {
    return (
      <div className="space-y-3">
        <div className="grid gap-2">
          {options.map((option) => (
            <motion.button
              key={option.value}
              onClick={() => {
                handleSelectChange(option.value)
                setTimeout(onSubmit, 150)
              }}
              disabled={disabled}
              whileHover={{ scale: 1.01 }}
              whileTap={{ scale: 0.99 }}
              className={`
                w-full p-4 rounded-xl text-left transition-all
                border-2
                ${value === option.value
                  ? 'border-primary-600 bg-primary-50 text-primary-900'
                  : 'border-gray-200 bg-white hover:border-gray-300 text-gray-900'
                }
                ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
              `}
            >
              <div className="flex items-center gap-3">
                <div className={`
                  w-5 h-5 rounded-full border-2 flex items-center justify-center
                  ${value === option.value ? 'border-primary-600' : 'border-gray-300'}
                `}>
                  <AnimatePresence>
                    {value === option.value && (
                      <motion.div
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        exit={{ scale: 0 }}
                        className="w-3 h-3 rounded-full bg-primary-600"
                      />
                    )}
                  </AnimatePresence>
                </div>
                <div>
                  <div className="font-medium">{option.label}</div>
                  {option.description && (
                    <div className="text-sm text-gray-500 mt-0.5">{option.description}</div>
                  )}
                </div>
              </div>
            </motion.button>
          ))}
        </div>
      </div>
    )
  }

  // MultiSelect input (multiple choices)
  if (inputType === 'multi_select') {
    const selectedValues = Array.isArray(value) ? value : []
    return (
      <div className="space-y-3">
        <div className="grid gap-2">
          {options.map((option) => (
            <motion.button
              key={option.value}
              onClick={() => handleMultiSelectChange(option.value)}
              disabled={disabled}
              whileHover={{ scale: 1.01 }}
              whileTap={{ scale: 0.99 }}
              className={`
                w-full p-4 rounded-xl text-left transition-all
                border-2
                ${selectedValues.includes(option.value)
                  ? 'border-primary-600 bg-primary-50 text-primary-900'
                  : 'border-gray-200 bg-white hover:border-gray-300 text-gray-900'
                }
                ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
              `}
            >
              <div className="flex items-center gap-3">
                <div className={`
                  w-5 h-5 rounded border-2 flex items-center justify-center
                  ${selectedValues.includes(option.value) ? 'border-primary-600 bg-primary-600' : 'border-gray-300'}
                `}>
                  <AnimatePresence>
                    {selectedValues.includes(option.value) && (
                      <motion.svg
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        exit={{ scale: 0 }}
                        className="w-3 h-3 text-white"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                      </motion.svg>
                    )}
                  </AnimatePresence>
                </div>
                <div>
                  <div className="font-medium">{option.label}</div>
                  {option.description && (
                    <div className="text-sm text-gray-500 mt-0.5">{option.description}</div>
                  )}
                </div>
              </div>
            </motion.button>
          ))}
        </div>

        {/* Submit button for multi-select */}
        <motion.button
          onClick={onSubmit}
          disabled={disabled || selectedValues.length === 0}
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          className={`
            w-full py-3 px-6 rounded-xl font-medium transition-all
            ${selectedValues.length > 0 && !disabled
              ? 'bg-primary-600 text-white hover:bg-primary-700'
              : 'bg-gray-200 text-gray-400 cursor-not-allowed'
            }
          `}
        >
          Continue {selectedValues.length > 0 && `(${selectedValues.length} selected)`}
        </motion.button>
      </div>
    )
  }

  // Number input
  if (inputType === 'number') {
    return (
      <div className="space-y-4">
        <div className="flex items-center gap-3">
          <input
            type="number"
            value={value as number | string}
            onChange={(e) => handleNumberChange(e.target.value)}
            onKeyDown={handleKeyDown}
            min={numberMin}
            max={numberMax}
            step={numberStep}
            placeholder={placeholder || 'Enter a number'}
            disabled={disabled}
            className={`
              flex-1 px-4 py-3 text-lg border-2 rounded-xl
              focus:ring-2 focus:ring-primary-500 focus:border-transparent
              ${disabled ? 'opacity-50 cursor-not-allowed bg-gray-100' : 'bg-white'}
              border-gray-200
            `}
          />
          {numberUnit && (
            <span className="text-gray-600 font-medium">{numberUnit}</span>
          )}
        </div>

        {(numberMin !== undefined || numberMax !== undefined) && (
          <div className="text-sm text-gray-500">
            {numberMin !== undefined && numberMax !== undefined
              ? `Between ${numberMin} and ${numberMax}`
              : numberMin !== undefined
              ? `Minimum: ${numberMin}`
              : `Maximum: ${numberMax}`
            }
          </div>
        )}

        <motion.button
          onClick={onSubmit}
          disabled={disabled || !isValid}
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          className={`
            w-full py-3 px-6 rounded-xl font-medium transition-all
            ${isValid && !disabled
              ? 'bg-primary-600 text-white hover:bg-primary-700'
              : 'bg-gray-200 text-gray-400 cursor-not-allowed'
            }
          `}
        >
          Continue
        </motion.button>
      </div>
    )
  }

  // Scale input (1-5 or 1-10)
  if (inputType === 'scale') {
    const scaleValues = Array.from({ length: scaleMax }, (_, i) => i + 1)
    return (
      <div className="space-y-4">
        <div className="flex justify-center gap-2">
          {scaleValues.map((num) => (
            <motion.button
              key={num}
              onClick={() => {
                handleScaleChange(num)
                setTimeout(onSubmit, 150)
              }}
              disabled={disabled}
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.95 }}
              className={`
                w-12 h-12 rounded-xl font-semibold text-lg transition-all
                ${value === num
                  ? 'bg-primary-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }
                ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
              `}
            >
              {num}
            </motion.button>
          ))}
        </div>

        <div className="flex justify-between text-sm text-gray-500 px-2">
          <span>Not at all</span>
          <span>Extremely</span>
        </div>
      </div>
    )
  }

  // Text input (default)
  return (
    <div className="space-y-4">
      <textarea
        value={value as string}
        onChange={(e) => handleTextChange(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder || 'Type your answer...'}
        disabled={disabled}
        rows={3}
        className={`
          w-full px-4 py-3 text-lg border-2 rounded-xl resize-none
          focus:ring-2 focus:ring-primary-500 focus:border-transparent
          ${disabled ? 'opacity-50 cursor-not-allowed bg-gray-100' : 'bg-white'}
          border-gray-200
        `}
      />

      <motion.button
        onClick={onSubmit}
        disabled={disabled || !isValid}
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
        className={`
          w-full py-3 px-6 rounded-xl font-medium transition-all
          ${isValid && !disabled
            ? 'bg-primary-600 text-white hover:bg-primary-700'
            : 'bg-gray-200 text-gray-400 cursor-not-allowed'
          }
        `}
      >
        Continue
      </motion.button>
    </div>
  )
}
