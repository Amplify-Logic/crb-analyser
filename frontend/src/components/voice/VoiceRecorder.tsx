/**
 * VoiceRecorder Component
 *
 * A sleek, animated microphone button for voice input.
 * Shows waveform animation while recording.
 */

import { useState, useRef, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

interface VoiceRecorderProps {
  onRecordingComplete: (audioBlob: Blob) => void
  onTranscript?: (text: string) => void
  disabled?: boolean
  size?: 'small' | 'medium' | 'large'
  className?: string
}

type RecordingState = 'idle' | 'recording' | 'processing'

export default function VoiceRecorder({
  onRecordingComplete,
  onTranscript,
  disabled = false,
  size = 'large',
  className = '',
}: VoiceRecorderProps) {
  const [state, setState] = useState<RecordingState>('idle')
  const [duration, setDuration] = useState(0)
  const [error, setError] = useState<string | null>(null)
  const [audioLevels, setAudioLevels] = useState<number[]>(Array(12).fill(0.1))

  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const chunksRef = useRef<Blob[]>([])
  const timerRef = useRef<NodeJS.Timeout | null>(null)
  const analyserRef = useRef<AnalyserNode | null>(null)
  const animationRef = useRef<number | null>(null)

  // Size configurations
  const sizes = {
    small: { button: 'w-14 h-14', icon: 'w-6 h-6', text: 'text-xs' },
    medium: { button: 'w-20 h-20', icon: 'w-8 h-8', text: 'text-sm' },
    large: { button: 'w-28 h-28', icon: 'w-10 h-10', text: 'text-base' },
  }

  const sizeConfig = sizes[size]

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current)
      if (animationRef.current) cancelAnimationFrame(animationRef.current)
      if (mediaRecorderRef.current?.state === 'recording') {
        mediaRecorderRef.current.stop()
      }
    }
  }, [])

  // Analyze audio for waveform
  const analyzeAudio = useCallback((analyser: AnalyserNode) => {
    const dataArray = new Uint8Array(analyser.frequencyBinCount)

    const updateLevels = () => {
      analyser.getByteFrequencyData(dataArray)

      // Sample 12 frequency bands for visualization
      const bands = 12
      const bandSize = Math.floor(dataArray.length / bands)
      const levels: number[] = []

      for (let i = 0; i < bands; i++) {
        let sum = 0
        for (let j = 0; j < bandSize; j++) {
          sum += dataArray[i * bandSize + j]
        }
        // Normalize to 0.1-1 range
        levels.push(0.1 + (sum / bandSize / 255) * 0.9)
      }

      setAudioLevels(levels)
      animationRef.current = requestAnimationFrame(updateLevels)
    }

    updateLevels()
  }, [])

  const startRecording = async () => {
    try {
      setError(null)

      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })

      // Set up audio analysis for waveform
      const audioContext = new AudioContext()
      const source = audioContext.createMediaStreamSource(stream)
      const analyser = audioContext.createAnalyser()
      analyser.fftSize = 256
      source.connect(analyser)
      analyserRef.current = analyser

      // Create media recorder
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      })

      mediaRecorderRef.current = mediaRecorder
      chunksRef.current = []

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          chunksRef.current.push(e.data)
        }
      }

      mediaRecorder.onstop = () => {
        // Stop all tracks
        stream.getTracks().forEach(track => track.stop())

        // Stop audio analysis
        if (animationRef.current) {
          cancelAnimationFrame(animationRef.current)
        }
        audioContext.close()

        // Create blob
        const audioBlob = new Blob(chunksRef.current, { type: 'audio/webm' })

        if (audioBlob.size > 0) {
          setState('processing')
          onRecordingComplete(audioBlob)
        } else {
          setState('idle')
          setError('No audio recorded')
        }
      }

      mediaRecorder.start(100)
      setState('recording')
      setDuration(0)

      // Start timer
      timerRef.current = setInterval(() => {
        setDuration(d => d + 1)
      }, 1000)

      // Start audio analysis
      analyzeAudio(analyser)

    } catch (err) {
      console.error('Recording error:', err)
      setError('Could not access microphone. Please check permissions.')
      setState('idle')
    }
  }

  const stopRecording = () => {
    if (timerRef.current) {
      clearInterval(timerRef.current)
      timerRef.current = null
    }

    if (mediaRecorderRef.current?.state === 'recording') {
      mediaRecorderRef.current.stop()
    }
  }

  const handleClick = () => {
    if (disabled) return

    if (state === 'idle') {
      startRecording()
    } else if (state === 'recording') {
      stopRecording()
    }
  }

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  // Reset to idle when processing is done externally
  useEffect(() => {
    // Parent can use onTranscript to know when to reset
    if (onTranscript) {
      // Callback available
    }
  }, [onTranscript])

  return (
    <div className={`flex flex-col items-center ${className}`}>
      {/* Main button */}
      <motion.button
        onClick={handleClick}
        disabled={disabled || state === 'processing'}
        className={`
          ${sizeConfig.button}
          rounded-full flex items-center justify-center
          transition-all duration-300 relative
          ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
          ${state === 'idle' ? 'bg-primary-600 hover:bg-primary-700 hover:scale-105' : ''}
          ${state === 'recording' ? 'bg-red-500' : ''}
          ${state === 'processing' ? 'bg-yellow-500' : ''}
        `}
        whileTap={!disabled ? { scale: 0.95 } : undefined}
      >
        {/* Pulsing ring for recording */}
        <AnimatePresence>
          {state === 'recording' && (
            <motion.div
              className="absolute inset-0 rounded-full bg-red-500"
              initial={{ opacity: 0.5, scale: 1 }}
              animate={{ opacity: 0, scale: 1.5 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 1.5, repeat: Infinity }}
            />
          )}
        </AnimatePresence>

        {/* Waveform visualization */}
        <AnimatePresence>
          {state === 'recording' && (
            <div className="absolute inset-0 flex items-center justify-center gap-0.5">
              {audioLevels.map((level, i) => (
                <motion.div
                  key={i}
                  className="w-1 bg-white rounded-full"
                  initial={{ height: 4 }}
                  animate={{ height: Math.max(4, level * 40) }}
                  transition={{ duration: 0.1 }}
                />
              ))}
            </div>
          )}
        </AnimatePresence>

        {/* Icon */}
        {state !== 'recording' && (
          <div className={`${sizeConfig.icon} text-white`}>
            {state === 'idle' && (
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
              </svg>
            )}
            {state === 'processing' && (
              <svg className="animate-spin" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
            )}
          </div>
        )}
      </motion.button>

      {/* Label */}
      <div className={`mt-3 text-center ${sizeConfig.text}`}>
        {state === 'idle' && (
          <span className="text-gray-600">Tap to talk</span>
        )}
        {state === 'recording' && (
          <div className="flex flex-col items-center">
            <span className="text-red-600 font-medium">{formatDuration(duration)}</span>
            <span className="text-gray-500 text-sm">Tap to stop</span>
          </div>
        )}
        {state === 'processing' && (
          <span className="text-yellow-600">Processing...</span>
        )}
      </div>

      {/* Error message */}
      <AnimatePresence>
        {error && (
          <motion.p
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="mt-2 text-sm text-red-600 text-center max-w-xs"
          >
            {error}
          </motion.p>
        )}
      </AnimatePresence>
    </div>
  )
}

// Export a hook for external control
export function useVoiceRecorderState() {
  const [isProcessing, setIsProcessing] = useState(false)

  return {
    isProcessing,
    setIsProcessing,
  }
}
