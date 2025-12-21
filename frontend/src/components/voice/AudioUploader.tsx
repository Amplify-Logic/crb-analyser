/**
 * AudioUploader Component
 *
 * Allows users to upload an existing recording or record a live conversation.
 * Used for meeting recordings that AI will transcribe and extract insights from.
 */

import { useState, useRef, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

interface AudioUploaderProps {
  onAudioReady: (audioBlob: Blob, source: 'upload' | 'recording') => void
  onCancel?: () => void
  maxDurationMinutes?: number
  className?: string
}

type Mode = 'select' | 'uploading' | 'recording' | 'preview'

export default function AudioUploader({
  onAudioReady,
  onCancel,
  maxDurationMinutes = 120,
  className = '',
}: AudioUploaderProps) {
  const [mode, setMode] = useState<Mode>('select')
  const [fileName, setFileName] = useState<string | null>(null)
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null)
  const [audioUrl, setAudioUrl] = useState<string | null>(null)
  const [duration, setDuration] = useState(0)
  const [error, setError] = useState<string | null>(null)
  const [uploadProgress, setUploadProgress] = useState(0)

  const fileInputRef = useRef<HTMLInputElement>(null)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const chunksRef = useRef<Blob[]>([])
  const timerRef = useRef<NodeJS.Timeout | null>(null)

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    // Validate file type
    const validTypes = ['audio/mp3', 'audio/mpeg', 'audio/wav', 'audio/m4a', 'audio/mp4', 'audio/webm', 'audio/ogg']
    if (!validTypes.some(type => file.type.includes(type.split('/')[1]))) {
      setError('Please upload an audio file (MP3, WAV, M4A, or WebM)')
      return
    }

    // Validate file size (max 100MB)
    if (file.size > 100 * 1024 * 1024) {
      setError('File too large. Maximum size is 100MB.')
      return
    }

    setError(null)
    setFileName(file.name)
    setMode('uploading')

    // Simulate upload progress (in real app, this would be actual upload)
    let progress = 0
    const interval = setInterval(() => {
      progress += 10
      setUploadProgress(progress)
      if (progress >= 100) {
        clearInterval(interval)
        setAudioBlob(file)
        setAudioUrl(URL.createObjectURL(file))
        setMode('preview')
      }
    }, 100)
  }, [])

  const startRecording = async () => {
    try {
      setError(null)
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })

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
        stream.getTracks().forEach(track => track.stop())
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' })
        setAudioBlob(blob)
        setAudioUrl(URL.createObjectURL(blob))
        setMode('preview')
      }

      mediaRecorder.start(1000)
      setMode('recording')
      setDuration(0)

      timerRef.current = setInterval(() => {
        setDuration(d => {
          if (d >= maxDurationMinutes * 60) {
            stopRecording()
            return d
          }
          return d + 1
        })
      }, 1000)

    } catch (err) {
      console.error('Recording error:', err)
      setError('Could not access microphone. Please check permissions.')
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

  const handleSubmit = () => {
    if (audioBlob) {
      onAudioReady(audioBlob, fileName ? 'upload' : 'recording')
    }
  }

  const handleReset = () => {
    if (audioUrl) {
      URL.revokeObjectURL(audioUrl)
    }
    setMode('select')
    setFileName(null)
    setAudioBlob(null)
    setAudioUrl(null)
    setDuration(0)
    setUploadProgress(0)
    setError(null)
  }

  return (
    <div className={`${className}`}>
      <AnimatePresence mode="wait">
        {/* Selection Mode */}
        {mode === 'select' && (
          <motion.div
            key="select"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="space-y-4"
          >
            <div className="grid grid-cols-2 gap-4">
              {/* Upload option */}
              <button
                onClick={() => fileInputRef.current?.click()}
                className="p-6 bg-white border-2 border-dashed border-gray-200 rounded-2xl hover:border-primary-300 hover:bg-primary-50 transition group"
              >
                <div className="flex flex-col items-center text-center">
                  <div className="w-12 h-12 bg-gray-100 rounded-full flex items-center justify-center mb-3 group-hover:bg-primary-100 transition">
                    <svg className="w-6 h-6 text-gray-500 group-hover:text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                    </svg>
                  </div>
                  <span className="font-medium text-gray-900">Upload Recording</span>
                  <span className="text-sm text-gray-500 mt-1">MP3, WAV, M4A</span>
                </div>
              </button>

              {/* Record option */}
              <button
                onClick={startRecording}
                className="p-6 bg-white border-2 border-dashed border-gray-200 rounded-2xl hover:border-red-300 hover:bg-red-50 transition group"
              >
                <div className="flex flex-col items-center text-center">
                  <div className="w-12 h-12 bg-gray-100 rounded-full flex items-center justify-center mb-3 group-hover:bg-red-100 transition">
                    <div className="w-4 h-4 bg-red-500 rounded-full" />
                  </div>
                  <span className="font-medium text-gray-900">Record Conversation</span>
                  <span className="text-sm text-gray-500 mt-1">Up to {maxDurationMinutes} min</span>
                </div>
              </button>
            </div>

            <input
              ref={fileInputRef}
              type="file"
              accept="audio/*"
              onChange={handleFileSelect}
              className="hidden"
            />

            {error && (
              <p className="text-sm text-red-600 text-center">{error}</p>
            )}

            {onCancel && (
              <button
                onClick={onCancel}
                className="w-full py-2 text-sm text-gray-500 hover:text-gray-700"
              >
                Cancel
              </button>
            )}
          </motion.div>
        )}

        {/* Uploading Mode */}
        {mode === 'uploading' && (
          <motion.div
            key="uploading"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="p-6 bg-white rounded-2xl border border-gray-100 text-center"
          >
            <div className="w-16 h-16 mx-auto mb-4 relative">
              <svg className="w-16 h-16 text-primary-100" viewBox="0 0 100 100">
                <circle cx="50" cy="50" r="45" fill="none" stroke="currentColor" strokeWidth="8" />
              </svg>
              <svg className="w-16 h-16 text-primary-600 absolute inset-0" viewBox="0 0 100 100">
                <circle
                  cx="50"
                  cy="50"
                  r="45"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="8"
                  strokeDasharray={`${uploadProgress * 2.83} 283`}
                  transform="rotate(-90 50 50)"
                />
              </svg>
              <span className="absolute inset-0 flex items-center justify-center text-sm font-medium text-gray-700">
                {uploadProgress}%
              </span>
            </div>
            <p className="text-gray-600">Uploading {fileName}...</p>
          </motion.div>
        )}

        {/* Recording Mode */}
        {mode === 'recording' && (
          <motion.div
            key="recording"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="p-6 bg-white rounded-2xl border border-red-100 text-center"
          >
            <motion.div
              className="w-20 h-20 mx-auto mb-4 bg-red-500 rounded-full flex items-center justify-center cursor-pointer"
              animate={{ scale: [1, 1.1, 1] }}
              transition={{ duration: 1.5, repeat: Infinity }}
              onClick={stopRecording}
            >
              <div className="w-6 h-6 bg-white rounded" />
            </motion.div>
            <p className="text-2xl font-bold text-gray-900 mb-1">{formatDuration(duration)}</p>
            <p className="text-gray-500">Recording... Tap to stop</p>
            <p className="text-xs text-gray-400 mt-2">
              Max {maxDurationMinutes} minutes
            </p>
          </motion.div>
        )}

        {/* Preview Mode */}
        {mode === 'preview' && audioUrl && (
          <motion.div
            key="preview"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="p-6 bg-white rounded-2xl border border-gray-100"
          >
            <div className="flex items-center gap-4 mb-4">
              <div className="w-12 h-12 bg-primary-100 rounded-full flex items-center justify-center flex-shrink-0">
                <svg className="w-6 h-6 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3" />
                </svg>
              </div>
              <div className="flex-1 min-w-0">
                <p className="font-medium text-gray-900 truncate">
                  {fileName || `Recording (${formatDuration(duration)})`}
                </p>
                <audio src={audioUrl} controls className="w-full mt-2 h-8" />
              </div>
            </div>

            <div className="flex gap-3">
              <button
                onClick={handleReset}
                className="flex-1 py-2 border border-gray-200 text-gray-700 rounded-xl hover:bg-gray-50 transition"
              >
                Try Again
              </button>
              <button
                onClick={handleSubmit}
                className="flex-1 py-2 bg-primary-600 text-white rounded-xl hover:bg-primary-700 transition"
              >
                Use This Recording
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
