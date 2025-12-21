/**
 * Interview Voice Input Hook
 * Provides audio recording and transcription for the interview (no auth required).
 */

import { useState, useRef, useCallback } from 'react'
import apiClient from '../services/apiClient'

type VoiceState = 'idle' | 'recording' | 'transcribing'

interface UseInterviewVoiceOptions {
  sessionId?: string
  onTranscript?: (text: string) => void
  onError?: (error: string) => void
}

interface UseInterviewVoiceReturn {
  state: VoiceState
  isRecording: boolean
  isTranscribing: boolean
  startRecording: () => Promise<void>
  stopRecording: () => Promise<string>
  toggleRecording: () => Promise<string | void>
  error: string | null
}

export function useInterviewVoice(options: UseInterviewVoiceOptions = {}): UseInterviewVoiceReturn {
  const [state, setState] = useState<VoiceState>('idle')
  const [error, setError] = useState<string | null>(null)

  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const chunksRef = useRef<Blob[]>([])

  const startRecording = useCallback(async () => {
    try {
      setError(null)

      // Request microphone access
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })

      // Create MediaRecorder with webm format
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

      mediaRecorder.start(100) // Collect data every 100ms
      setState('recording')

    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to access microphone'
      setError(message)
      options.onError?.(message)
      throw err
    }
  }, [options])

  const stopRecording = useCallback(async (): Promise<string> => {
    return new Promise((resolve, reject) => {
      const mediaRecorder = mediaRecorderRef.current

      if (!mediaRecorder || mediaRecorder.state !== 'recording') {
        reject(new Error('Not recording'))
        return
      }

      mediaRecorder.onstop = async () => {
        setState('transcribing')

        // Stop all tracks
        mediaRecorder.stream.getTracks().forEach(track => track.stop())

        // Create blob from chunks
        const audioBlob = new Blob(chunksRef.current, { type: 'audio/webm' })

        if (audioBlob.size === 0) {
          setState('idle')
          const error = 'No audio recorded'
          setError(error)
          options.onError?.(error)
          reject(new Error(error))
          return
        }

        try {
          // Send to interview transcription API (no auth required)
          const result = await apiClient.transcribeInterviewAudio(audioBlob, options.sessionId)

          setState('idle')
          options.onTranscript?.(result.text)
          resolve(result.text)

        } catch (err: unknown) {
          setState('idle')
          const apiError = err as { message?: string }
          const message = apiError?.message || 'Transcription failed'
          setError(message)
          options.onError?.(message)
          reject(err)
        }
      }

      mediaRecorder.stop()
    })
  }, [options])

  const toggleRecording = useCallback(async (): Promise<string | void> => {
    if (state === 'recording') {
      return stopRecording()
    } else if (state === 'idle') {
      await startRecording()
    }
    // If transcribing, do nothing
  }, [state, startRecording, stopRecording])

  return {
    state,
    isRecording: state === 'recording',
    isTranscribing: state === 'transcribing',
    startRecording,
    stopRecording,
    toggleRecording,
    error,
  }
}

export default useInterviewVoice
