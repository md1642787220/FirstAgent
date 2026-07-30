type MessageHandler = (data: any) => void
type ConnectionChangeHandler = (connected: boolean) => void

class WebSocketService {
  private ws: WebSocket | null = null
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null
  private heartbeatTimer: ReturnType<typeof setInterval> | null = null
  private reconnectDelay = 1000
  private maxReconnectDelay = 30000
  private url: string = ''
  private handlers: Set<MessageHandler> = new Set()
  private connectionHandlers: Set<ConnectionChangeHandler> = new Set()

  connect(url: string): void {
    this.url = url
    this._connect()
  }

  private _connect(): void {
    if (this.ws?.readyState === WebSocket.OPEN) return

    try {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      this.ws = new WebSocket(`${protocol}//${window.location.host}${this.url}`)

      this.ws.onopen = () => {
        console.log('[WS] Connected to', this.url)
        this.reconnectDelay = 1000
        this.connectionHandlers.forEach(h => h(true))
        this._startHeartbeat()
      }

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          this.handlers.forEach(h => h(data))
        } catch {
          console.error('[WS] Parse error:', event.data)
        }
      }

      this.ws.onclose = () => {
        console.log('[WS] Disconnected')
        this._stopHeartbeat()
        this.connectionHandlers.forEach(h => h(false))
        this._scheduleReconnect()
      }

      this.ws.onerror = () => {
        this.ws?.close()
      }
    } catch (err) {
      console.error('[WS] Connect error:', err)
      this._scheduleReconnect()
    }
  }

  private _startHeartbeat(): void {
    this._stopHeartbeat()
    this.heartbeatTimer = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ type: 'ping' }))
      }
    }, 30000)
  }

  private _stopHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer)
      this.heartbeatTimer = null
    }
  }

  private _scheduleReconnect(): void {
    if (this.reconnectTimer) return
    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null
      console.log(`[WS] Reconnecting in ${this.reconnectDelay}ms...`)
      this._connect()
      this.reconnectDelay = Math.min(this.reconnectDelay * 2, this.maxReconnectDelay)
    }, this.reconnectDelay)
  }

  onMessage(handler: MessageHandler): () => void {
    this.handlers.add(handler)
    return () => this.handlers.delete(handler)
  }

  onConnectionChange(handler: ConnectionChangeHandler): () => void {
    this.connectionHandlers.add(handler)
    return () => this.connectionHandlers.delete(handler)
  }

  disconnect(): void {
    this._stopHeartbeat()
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }

  get isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN
  }
}

export const wsService = new WebSocketService()
export default wsService
