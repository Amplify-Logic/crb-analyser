/**
 * Refiner API Service
 * Handles report refiner conversations and messages.
 */

import apiClient from './apiClient'

// --- Types ---

export interface StarterPrompt {
  text: string
}

export interface Conversation {
  id: string
  report_id: string
  status: 'active' | 'archived'
  title?: string
  started_at: string
  last_message_at?: string
  starter_prompts?: string[]
}

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  suggestions?: Suggestion[]
  model_used?: string
  tokens_used?: number
  created_at: string
}

export interface Suggestion {
  id: string
  refinement_type: string
  impact_level: 'minor' | 'moderate' | 'major'
  energy_cost: number
  target_section: string
  target_ids: string[]
  change_summary: string
  preview?: {
    before: Record<string, unknown>
    after: Record<string, unknown>
  }
}

export interface CreateConversationResponse {
  id: string
  report_id: string
  status: string
  starter_prompts: string[]
}

export interface SendMessageResponse {
  id: string
  role: 'assistant'
  content: string
  model_used?: string
  tokens_used?: number
}

// --- API ---

export const refinerApi = {
  async createConversation(reportId: string): Promise<CreateConversationResponse> {
    const { data } = await apiClient.post<CreateConversationResponse>(
      `/api/reports/${reportId}/conversations`
    )
    return data
  },

  async listConversations(reportId: string): Promise<Conversation[]> {
    const { data } = await apiClient.get<{ conversations: Conversation[] }>(
      `/api/reports/${reportId}/conversations`
    )
    return data.conversations
  },

  async getMessages(reportId: string, conversationId: string): Promise<Message[]> {
    const { data } = await apiClient.get<{ messages: Message[] }>(
      `/api/reports/${reportId}/conversations/${conversationId}/messages`
    )
    return data.messages
  },

  async sendMessage(
    reportId: string,
    conversationId: string,
    content: string
  ): Promise<SendMessageResponse> {
    const { data } = await apiClient.post<SendMessageResponse>(
      `/api/reports/${reportId}/conversations/${conversationId}/messages`,
      { content },
      { timeout: 60000 } // 60s timeout for LLM calls
    )
    return data
  },
}
