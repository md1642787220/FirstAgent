export interface TraceStep {
  step_type: 'think' | 'action' | 'observe'
  content: string
  timestamp: string
  duration_ms?: number
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: Date
  trace?: TraceStep[]
  intent?: string
  isStreaming?: boolean
}

type EventHandler = (event: string, data: unknown) => void
type ErrorHandler = (error: Event) => void

class SSEService {
  private controller: AbortController | null = null
  private messageHandler: EventHandler | null = null
  private errorHandler: ErrorHandler | null = null

  onMessage(handler: EventHandler): void {
    this.messageHandler = handler
  }

  onError(handler: ErrorHandler): void {
    this.errorHandler = handler
  }

  connect(url: string, body: object): AbortController {
    this.disconnect()
    this.controller = new AbortController()

    fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
      signal: this.controller.signal,
    }).then(async (response) => {
      if (!response.ok || !response.body) {
        this.errorHandler?.(new ErrorEvent('error'))
        return
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          const trimmed = line.trim()
          if (!trimmed || trimmed.startsWith(':')) continue

          if (trimmed.startsWith('event:')) {
            // next line should be data:
            continue
          }

          if (trimmed.startsWith('data:')) {
            const dataStr = trimmed.slice(5).trim()
            if (dataStr === '[DONE]') {
              this.messageHandler?.('done', null)
              continue
            }

            try {
              const data = JSON.parse(dataStr)
              // Determine event type from context or assume answer
              if (data.step_type) {
                this.messageHandler?.('trace_step', data)
              } else if (data.session_id) {
                this.messageHandler?.('answer', data)
              } else {
                this.messageHandler?.('message', data)
              }
            } catch {
              console.error('[SSE] Parse error:', dataStr)
            }
          }
        }
      }
    }).catch((err) => {
      if ((err as Error).name !== 'AbortError') {
        this.errorHandler?.(err as Event)
      }
    })

    return this.controller
  }

  disconnect(): void {
    if (this.controller) {
      this.controller.abort()
      this.controller = null
    }
  }
}

export const sseService = new SSEService()
export default sseService
