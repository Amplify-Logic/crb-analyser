/**
 * Interview API Service
 *
 * Handles communication with the SOTA interview engine backend.
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8383'

export interface ProcessAnswerRequest {
  session_id: string
  answer_text: string
  current_anchor: number
  follow_ups_asked: number
  industry: string
  company_name?: string
}

export interface ProcessAnswerResponse {
  signals_detected: string[]
  acknowledgment: string
  next_question: string
  next_question_type: 'anchor' | 'follow_up' | 'summary'
  next_topic?: string
  progress: {
    current_anchor: number
    questions_asked: number
    max_questions: number
  }
  interview_complete: boolean
}

export interface FirstQuestionResponse {
  question: string
  topic: string
  anchor: number
}

/**
 * Process an interview answer and get the next question.
 */
export async function processAnswer(
  request: ProcessAnswerRequest
): Promise<ProcessAnswerResponse> {
  const response = await fetch(`${API_BASE_URL}/api/interview/process-answer`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
    throw new Error(error.detail || 'Failed to process answer')
  }

  return response.json()
}

/**
 * Get the first question to start the interview.
 */
export async function getFirstQuestion(
  industry: string,
  companyName?: string
): Promise<FirstQuestionResponse> {
  const params = new URLSearchParams({ industry })
  if (companyName) params.append('company_name', companyName)

  const response = await fetch(
    `${API_BASE_URL}/api/interview/first-question?${params}`
  )

  if (!response.ok) {
    throw new Error('Failed to get first question')
  }

  return response.json()
}

/**
 * Transcribe audio and get text.
 */
export async function transcribeAudio(
  audioBlob: Blob,
  sessionId?: string
): Promise<string> {
  const formData = new FormData()
  formData.append('audio', audioBlob, 'recording.webm')
  if (sessionId) formData.append('session_id', sessionId)

  const response = await fetch(`${API_BASE_URL}/api/interview/transcribe`, {
    method: 'POST',
    body: formData,
  })

  if (!response.ok) {
    throw new Error('Transcription failed')
  }

  const data = await response.json()
  return data.text
}
