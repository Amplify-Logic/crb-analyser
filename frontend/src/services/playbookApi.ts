/**
 * Playbook API Service
 * Handles playbook progress persistence
 */

import apiClient from './apiClient'

interface TaskCompletionRequest {
  playbook_id: string
  task_id: string
  completed: boolean
}

interface TaskCompletionResponse {
  success: boolean
  task_id: string
  completed: boolean
  completed_at?: string
}

interface PlaybookProgressResponse {
  report_id: string
  playbook_id: string
  completed_tasks: string[]
  total_completed: number
}

export const playbookApi = {
  /**
   * Save task completion status
   */
  async saveTaskCompletion(
    reportId: string,
    request: TaskCompletionRequest
  ): Promise<TaskCompletionResponse> {
    const { data } = await apiClient.post<TaskCompletionResponse>(
      `/api/playbook/progress?report_id=${reportId}`,
      request
    )
    return data
  },

  /**
   * Get all playbook progress for a report
   */
  async getPlaybookProgress(reportId: string): Promise<Record<string, string[]>> {
    const { data } = await apiClient.get<PlaybookProgressResponse[]>(
      `/api/playbook/progress/${reportId}`
    )

    // Convert to playbookId -> taskIds map
    const progressMap: Record<string, string[]> = {}
    data.forEach(pb => {
      progressMap[pb.playbook_id] = pb.completed_tasks
    })

    return progressMap
  }
}
