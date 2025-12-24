/**
 * usePlaybookProgress Hook
 *
 * Manages playbook task progress with backend persistence.
 * Provides optimistic updates with background sync.
 */

import { useState, useEffect, useCallback, useRef } from 'react'
import apiClient from '../services/apiClient'

interface TaskProgress {
  taskId: string
  completed: boolean
  completedAt?: string
}

interface PlaybookProgressState {
  [playbookId: string]: {
    [taskId: string]: TaskProgress
  }
}

interface UsePlaybookProgressOptions {
  reportId: string
  onError?: (error: Error) => void
}

interface PlaybookProgressReturn {
  /** Check if a task is completed */
  isTaskCompleted: (playbookId: string, taskId: string) => boolean
  /** Toggle task completion - returns optimistic state immediately */
  toggleTask: (playbookId: string, taskId: string) => Promise<boolean>
  /** Get completion percentage for a playbook */
  getProgress: (playbookId: string, totalTasks: number) => number
  /** Get completed task count for a playbook */
  getCompletedCount: (playbookId: string) => number
  /** Get all completed task IDs for a playbook */
  getCompletedTasks: (playbookId: string) => string[]
  /** Loading state */
  isLoading: boolean
  /** Syncing state (background save in progress) */
  isSyncing: boolean
}

export function usePlaybookProgress({
  reportId,
  onError
}: UsePlaybookProgressOptions): PlaybookProgressReturn {
  const [progress, setProgress] = useState<PlaybookProgressState>({})
  const [isLoading, setIsLoading] = useState(true)
  const [isSyncing, setIsSyncing] = useState(false)

  // Track pending syncs to avoid race conditions
  const pendingSyncs = useRef<Set<string>>(new Set())

  // Load initial progress from backend
  useEffect(() => {
    async function loadProgress() {
      if (!reportId) return

      setIsLoading(true)
      try {
        const { data } = await apiClient.get<Array<{
          playbook_id: string
          completed_tasks: string[]
        }>>(`/api/playbook/progress/${reportId}`)

        const initialProgress: PlaybookProgressState = {}
        for (const item of data) {
          initialProgress[item.playbook_id] = {}
          for (const taskId of item.completed_tasks) {
            initialProgress[item.playbook_id][taskId] = {
              taskId,
              completed: true
            }
          }
        }
        setProgress(initialProgress)
      } catch (err) {
        console.error('Failed to load playbook progress:', err)
        // Don't fail - just start with empty progress
      } finally {
        setIsLoading(false)
      }
    }

    loadProgress()
  }, [reportId])

  const isTaskCompleted = useCallback((playbookId: string, taskId: string): boolean => {
    return progress[playbookId]?.[taskId]?.completed ?? false
  }, [progress])

  const toggleTask = useCallback(async (playbookId: string, taskId: string): Promise<boolean> => {
    const currentCompleted = isTaskCompleted(playbookId, taskId)
    const newCompleted = !currentCompleted
    const syncKey = `${playbookId}:${taskId}`

    // Optimistic update
    setProgress(prev => ({
      ...prev,
      [playbookId]: {
        ...prev[playbookId],
        [taskId]: {
          taskId,
          completed: newCompleted,
          completedAt: newCompleted ? new Date().toISOString() : undefined
        }
      }
    }))

    // Background sync
    if (!pendingSyncs.current.has(syncKey)) {
      pendingSyncs.current.add(syncKey)
      setIsSyncing(true)

      try {
        await apiClient.post(`/api/playbook/progress?report_id=${reportId}`, {
          playbook_id: playbookId,
          task_id: taskId,
          completed: newCompleted
        })
      } catch (err) {
        console.error('Failed to sync task progress:', err)
        // Revert on error
        setProgress(prev => ({
          ...prev,
          [playbookId]: {
            ...prev[playbookId],
            [taskId]: {
              taskId,
              completed: currentCompleted
            }
          }
        }))
        onError?.(err as Error)
      } finally {
        pendingSyncs.current.delete(syncKey)
        if (pendingSyncs.current.size === 0) {
          setIsSyncing(false)
        }
      }
    }

    return newCompleted
  }, [reportId, isTaskCompleted, onError])

  const getProgress = useCallback((playbookId: string, totalTasks: number): number => {
    if (totalTasks === 0) return 0
    const completed = Object.values(progress[playbookId] || {}).filter(t => t.completed).length
    return Math.round((completed / totalTasks) * 100)
  }, [progress])

  const getCompletedCount = useCallback((playbookId: string): number => {
    return Object.values(progress[playbookId] || {}).filter(t => t.completed).length
  }, [progress])

  const getCompletedTasks = useCallback((playbookId: string): string[] => {
    return Object.entries(progress[playbookId] || {})
      .filter(([_, t]) => t.completed)
      .map(([id]) => id)
  }, [progress])

  return {
    isTaskCompleted,
    toggleTask,
    getProgress,
    getCompletedCount,
    getCompletedTasks,
    isLoading,
    isSyncing
  }
}

export default usePlaybookProgress
