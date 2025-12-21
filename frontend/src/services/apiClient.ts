/**
 * API Client
 * Unified HTTP client for all API requests
 * Uses HTTP-only cookies for authentication (set by backend)
 */

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8383';

interface RequestConfig {
  headers?: Record<string, string>;
  body?: unknown;
  timeout?: number;
}

interface ApiError {
  message: string;
  status: number;
  detail?: string;
}

class ApiClient {
  private baseURL: string;

  constructor(baseURL: string) {
    this.baseURL = baseURL;
  }

  private async request<T>(
    method: string,
    url: string,
    config?: RequestConfig
  ): Promise<{ data: T }> {
    const fullUrl = url.startsWith('http') ? url : `${this.baseURL}${url}`;

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
        throw { message: `Request timeout after ${timeout}ms`, status: 408 };
      }

      throw error;
    }
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
export type { ApiError, RequestConfig };
