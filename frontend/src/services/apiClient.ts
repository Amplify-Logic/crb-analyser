/**
 * API Client
 * Unified HTTP client for all API requests
 * Uses HTTP-only cookies for authentication (set by backend)
 */

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8383';

interface RetryConfig {
  maxRetries?: number;
  baseDelay?: number;
  retryOn?: (error: ApiError) => boolean;
}

interface RequestConfig {
  headers?: Record<string, string>;
  body?: unknown;
  timeout?: number;
  retry?: RetryConfig | boolean;
}

interface ApiError {
  message: string;
  status: number;
  detail?: string;
}

// Default retry settings
const DEFAULT_MAX_RETRIES = 3;
const DEFAULT_BASE_DELAY = 1000; // 1 second

// Determine if an error should trigger a retry
const isRetryableError = (error: ApiError): boolean => {
  // Retry on server errors (5xx) and network-related issues
  if (error.status >= 500 && error.status < 600) return true;
  if (error.status === 408) return true; // Timeout
  if (error.status === 429) return true; // Rate limited
  if (error.status === 0) return true; // Network error (no response)
  return false;
};

// Wait with exponential backoff
const wait = (ms: number): Promise<void> => new Promise(resolve => setTimeout(resolve, ms));

class ApiClient {
  private baseURL: string;

  constructor(baseURL: string) {
    this.baseURL = baseURL;
  }

  private getRetryConfig(config?: RequestConfig): RetryConfig | null {
    if (!config?.retry) return null;
    if (config.retry === true) {
      return {
        maxRetries: DEFAULT_MAX_RETRIES,
        baseDelay: DEFAULT_BASE_DELAY,
        retryOn: isRetryableError,
      };
    }
    return {
      maxRetries: config.retry.maxRetries ?? DEFAULT_MAX_RETRIES,
      baseDelay: config.retry.baseDelay ?? DEFAULT_BASE_DELAY,
      retryOn: config.retry.retryOn ?? isRetryableError,
    };
  }

  private async request<T>(
    method: string,
    url: string,
    config?: RequestConfig
  ): Promise<{ data: T }> {
    const fullUrl = url.startsWith('http') ? url : `${this.baseURL}${url}`;
    const retryConfig = this.getRetryConfig(config);
    const maxAttempts = retryConfig ? retryConfig.maxRetries! + 1 : 1;

    let lastError: ApiError | null = null;

    for (let attempt = 0; attempt < maxAttempts; attempt++) {
      // Wait before retry (exponential backoff)
      if (attempt > 0 && retryConfig) {
        const delay = retryConfig.baseDelay! * Math.pow(2, attempt - 1);
        await wait(delay);
      }

      // Default timeout of 30s
      const timeout = config?.timeout ?? 30000;
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), timeout);

      const options: RequestInit = {
        method,
        headers: {
          'Content-Type': 'application/json',
          ...config?.headers
        },
        credentials: 'include', // Send HTTP-only cookies
        signal: controller.signal,
      };

      if (config?.body) {
        options.body = JSON.stringify(config.body);
      }

      try {
        const response = await fetch(fullUrl, options);
        clearTimeout(timeoutId);

        if (!response.ok) {
          let errorDetail: string;
          try {
            const errorJson = await response.json();
            errorDetail = errorJson.detail || errorJson.message || response.statusText;
          } catch {
            errorDetail = await response.text() || response.statusText;
          }

          const error: ApiError = {
            message: errorDetail,
            status: response.status,
            detail: errorDetail,
          };

          // Check if we should retry
          if (retryConfig && attempt < maxAttempts - 1 && retryConfig.retryOn!(error)) {
            lastError = error;
            continue;
          }

          throw error;
        }

        // Handle 204 No Content
        if (response.status === 204) {
          return { data: null as T };
        }

        const data = await response.json();
        return { data };
      } catch (error) {
        clearTimeout(timeoutId);

        if (error instanceof Error && error.name === 'AbortError') {
          const timeoutError: ApiError = { message: `Request timeout after ${timeout}ms`, status: 408 };

          // Check if we should retry timeout
          if (retryConfig && attempt < maxAttempts - 1 && retryConfig.retryOn!(timeoutError)) {
            lastError = timeoutError;
            continue;
          }

          throw timeoutError;
        }

        // Handle network errors (fetch failures)
        if (error instanceof TypeError && error.message.includes('fetch')) {
          const networkError: ApiError = { message: 'Network error', status: 0 };

          if (retryConfig && attempt < maxAttempts - 1 && retryConfig.retryOn!(networkError)) {
            lastError = networkError;
            continue;
          }

          throw networkError;
        }

        throw error;
      }
    }

    // Should not reach here, but throw last error if we do
    throw lastError ?? { message: 'Request failed', status: 0 };
  }

  async get<T>(url: string, config?: RequestConfig): Promise<{ data: T }> {
    return this.request<T>('GET', url, config);
  }

  async post<T>(url: string, body?: unknown, config?: RequestConfig): Promise<{ data: T }> {
    return this.request<T>('POST', url, { ...config, body });
  }

  async put<T>(url: string, body?: unknown, config?: RequestConfig): Promise<{ data: T }> {
    return this.request<T>('PUT', url, { ...config, body });
  }

  async patch<T>(url: string, body?: unknown, config?: RequestConfig): Promise<{ data: T }> {
    return this.request<T>('PATCH', url, { ...config, body });
  }

  async delete<T>(url: string, config?: RequestConfig): Promise<{ data: T }> {
    return this.request<T>('DELETE', url, config);
  }

  async transcribeAudio(audioBlob: Blob): Promise<{ text: string; confidence: number }> {
    const formData = new FormData();
    formData.append('audio', audioBlob, 'recording.webm');

    const response = await fetch(`${this.baseURL}/api/intake/transcribe`, {
      method: 'POST',
      credentials: 'include',
      body: formData,
    });

    if (!response.ok) {
      let errorDetail: string;
      try {
        const errorJson = await response.json();
        errorDetail = errorJson.detail || errorJson.message || response.statusText;
      } catch {
        errorDetail = await response.text() || response.statusText;
      }
      throw { message: errorDetail, status: response.status };
    }

    return response.json();
  }

  async transcribeInterviewAudio(audioBlob: Blob, sessionId?: string): Promise<{ text: string; confidence: number }> {
    const formData = new FormData();
    formData.append('audio', audioBlob, 'recording.webm');
    if (sessionId) {
      formData.append('session_id', sessionId);
    }

    const response = await fetch(`${this.baseURL}/api/interview/transcribe`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      let errorDetail: string;
      try {
        const errorJson = await response.json();
        errorDetail = errorJson.detail || errorJson.message || response.statusText;
      } catch {
        errorDetail = await response.text() || response.statusText;
      }
      throw { message: errorDetail, status: response.status };
    }

    return response.json();
  }
}

export const apiClient = new ApiClient(API_BASE);

export default apiClient;

// Export types
export type { ApiError, RequestConfig, RetryConfig };
