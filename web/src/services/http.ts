const API_BASE = '/api'

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
    const response = await fetch(`${API_BASE}${url}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: body ? JSON.stringify(body) : undefined,
    })
    return handleResponse<T>(response)
  },

  async health(): Promise<{ status: string }> {
    const response = await fetch(`${API_BASE}/health`)
    return handleResponse(response)
  },
}

export default api
