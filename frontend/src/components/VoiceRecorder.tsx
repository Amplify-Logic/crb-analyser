import { useState, useRef, useCallback } from 'react'
import apiClient from '../services/apiClient'

interface VoiceRecorderProps {
  onTranscription: (text: string) => void
  disabled?: boolean
}

type RecordingState = 'idle' | 'recording' | 'transcribing'

export default function VoiceRecorder({ onTranscription, disabled }: VoiceRecorderProps) {
  const [state, setState] = useState<RecordingState>('idle')
  const [error, setError] = useState<string | null>(null)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const chunksRef = useRef<Blob[]>([])

  const startRecording = useCallback(async () => {
    setError(null)

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })

      // Use webm/opus for good compression and compatibility
      const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
        ? 'audio/webm;codecs=opus'
        : 'audio/webm'

      const mediaRecorder = new MediaRecorder(stream, { mimeType })
      mediaRecorderRef.current = mediaRecorder
      chunksRef.current = []

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data)
        }
      }

      mediaRecorder.onstop = async () => {
        // Stop all tracks
        stream.getTracks().forEach((track) => track.stop())

        // Create blob from chunks
        const audioBlob = new Blob(chunksRef.current, { type: 'audio/webm' })

        if (audioBlob.size === 0) {
          setError('No audio recorded')
          setState('idle')
          return
        }

        // Transcribe
        setState('transcribing')
        try {
          const result = await apiClient.transcribeAudio(audioBlob)
          if (result.text) {
            onTranscription(result.text)
          } else {
            setError('No speech detected')
          }
        } catch (err: any) {
          setError(err.message || 'Transcription failed')
        } finally {
          setState('idle')
        }
      }

      mediaRecorder.start(1000) // Collect data every second
      setState('recording')
    } catch (err: any) {
      if (err.name === 'NotAllowedError') {
        setError('Microphone access denied')
      } else if (err.name === 'NotFoundError') {
        setError('No microphone found')
      } else {
        setError('Could not start recording')
      }
      setState('idle')
    }
  }, [onTranscription])

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && state === 'recording') {
      mediaRecorderRef.current.stop()
    }
  }, [state])

  const handleClick = () => {
    if (state === 'idle') {
      startRecording()
    } else if (state === 'recording') {
      stopRecording()
    }
  }

  return (
    <div className="relative inline-flex items-center">
      <button
        type="button"
        onClick={handleClick}
        disabled={disabled || state === 'transcribing'}
        title={
          state === 'idle'
            ? 'Click to record'
            : state === 'recording'
            ? 'Click to stop'
            : 'Transcribing...'
        }
        className={`
          p-2 rounded-lg transition-all duration-200
          ${state === 'idle' ? 'text-gray-500 hover:text-primary-600 hover:bg-primary-50' : ''}
          ${state === 'recording' ? 'text-red-600 bg-red-50 animate-pulse' : ''}
          ${state === 'transcribing' ? 'text-primary-600 bg-primary-50' : ''}
          disabled:opacity-50 disabled:cursor-not-allowed
        `}
      >
        {state === 'idle' && (
          <svg
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            strokeWidth={1.5}
            stroke="currentColor"
            className="w-5 h-5"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M12 18.75a6 6 0 006-6v-1.5m-6 7.5a6 6 0 01-6-6v-1.5m6 7.5v3.75m-3.75 0h7.5M12 15.75a3 3 0 01-3-3V4.5a3 3 0 116 0v8.25a3 3 0 01-3 3z"
            />
          </svg>
        )}
        {state === 'recording' && (
          <svg
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            strokeWidth={1.5}
            stroke="currentColor"
            className="w-5 h-5"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M5.25 7.5A2.25 2.25 0 017.5 5.25h9a2.25 2.25 0 012.25 2.25v9a2.25 2.25 0 01-2.25 2.25h-9a2.25 2.25 0 01-2.25-2.25v-9z"
            />
          </svg>
        )}
        {state === 'transcribing' && (
          <svg
            className="w-5 h-5 animate-spin"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
          >
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
        )}
      </button>

      {/* Recording indicator */}
      {state === 'recording' && (
        <span className="ml-2 text-xs text-red-600 font-medium">
          Recording...
        </span>
      )}

      {/* Transcribing indicator */}
      {state === 'transcribing' && (
        <span className="ml-2 text-xs text-primary-600 font-medium">
          Transcribing...
        </span>
      )}

      {/* Error tooltip */}
      {error && (
        <div className="absolute top-full left-0 mt-1 px-2 py-1 bg-red-100 text-red-700 text-xs rounded whitespace-nowrap z-10">
          {error}
        </div>
      )}
    </div>
  )
}
