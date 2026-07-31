// 直连后端（CORS已在后端开启）
const API_BASE = 'http://localhost:8000/api'

// 导出方便 SSE 等服务使用
export function apiUrl(path: string): string {
  return `${API_BASE}${path}`
}

interface ApiError {
  message: string
  status?: number
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let message = `请求失败 (${response.status})`
    try {
      const body = await response.json()
      message = body.detail || body.message || message
    } catch {
      // ignore parse error
    }
    throw { message, status: response.status } as ApiError
  }
  return response.json()
}

export const api = {
  async get<T>(url: string, params?: Record<string, unknown>): Promise<T> {
    const searchParams = params ? new URLSearchParams(params as URLSearchParams).toString() : ''
    const response = await fetch(`${API_BASE}${url}${searchParams ? `?${searchParams}` : ''}`)
    return handleResponse<T>(response)
  },

  async post<T>(url: string, body?: unknown): Promise<T> {
    const isFormData = body instanceof FormData
    const response = await fetch(`${API_BASE}${url}`, {
      method: 'POST',
      headers: isFormData ? undefined : { 'Content-Type': 'application/json' },
      body: isFormData ? (body as FormData) : (body ? JSON.stringify(body) : undefined),
    })
    return handleResponse<T>(response)
  },

  async del<T>(url: string): Promise<T> {
    const response = await fetch(`${API_BASE}${url}`, { method: 'DELETE' })
    return handleResponse<T>(response)
  },

  async health(): Promise<{ status: string }> {
    const response = await fetch(`${API_BASE}/health`)
    return handleResponse(response)
  },
}

export default api
