import { useState, useRef, useEffect, useCallback } from 'react'
import { Send, Bot, User, ChevronDown, ChevronUp, Sparkles } from 'lucide-react'
import sseService, { ChatMessage, TraceStep } from '../services/sse'
import api from '../services/http'

interface Props {
  updateAppState: (updates: { llmConnected: boolean }) => void
}

const QUICK_QUESTIONS = [
  '当前设备状态如何？',
  '生产工单进度怎样？',
  '库存有短缺预警吗？',
  '推荐焊接工艺参数',
]

export default function ChatPage({ updateAppState }: Props) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [isStreaming, setIsStreaming] = useState(false)
  const [currentTrace, setCurrentTrace] = useState<TraceStep[]>([])
  const [expandedTrace, setExpandedTrace] = useState<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  // 检查后端健康状态
  useEffect(() => {
    api.health()
      .then(() => updateAppState({ llmConnected: true }))
      .catch(() => updateAppState({ llmConnected: false }))
  }, [updateAppState])

  // 自动滚动到底部
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const sendMessage = useCallback((text?: string) => {
    const messageText = text || input.trim()
    if (!messageText || isStreaming) return

    // 添加用户消息
    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: messageText,
      timestamp: new Date(),
    }
    setMessages(prev => [...prev, userMsg])
    setInput('')
    setIsStreaming(true)
    setCurrentTrace([])

    // 创建 AI 消息占位
    const aiMsgId = (Date.now() + 1).toString()
    setMessages(prev => [...prev, {
      id: aiMsgId,
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      isStreaming: true,
    }])

    // 连接 SSE
    sseService.onMessage((event, data) => {
      if (event === 'trace_step') {
        setCurrentTrace(prev => [...prev, data as TraceStep])
        setExpandedTrace(aiMsgId)
      } else if (event === 'answer') {
        const answerData = data as { answer: string; session_id: string; intent: string }
        setMessages(prev => prev.map(m =>
          m.id === aiMsgId
            ? { ...m, content: m.content + answerData.answer, intent: answerData.intent }
            : m
        ))
      } else if (event === 'done') {
        setIsStreaming(false)
        setMessages(prev => prev.map(m =>
          m.id === aiMsgId ? { ...m, isStreaming: false, trace: currentTrace } : m
        ))
      }
    })

    sseService.onError((error) => {
      console.error('[Chat] SSE error:', error)
      setIsStreaming(false)
      setMessages(prev => prev.map(m =>
        m.id === aiMsgId ? { ...m, content: '连接失败，请检查后端服务是否启动', isStreaming: false } : m
      ))
    })

    sseService.connect('/api/chat', { message: messageText })
  }, [input, isStreaming])

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  return (
    <div className="flex h-full flex-col gap-4">
      {/* 页面标题 */}
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-industrial-primary/20 to-blue-600/20 border border-industrial-primary/30">
          <Sparkles className="h-5 w-5 text-industrial-primary" />
        </div>
        <div>
          <h1 className="text-lg font-semibold text-industrial-text">AI 智能助手</h1>
          <p className="text-xs text-industrial-text-muted">基于多Agent架构的焊接设备智能问答系统</p>
        </div>
      </div>

      {/* 对话消息区 */}
      <div className="flex-1 overflow-y-auto rounded-xl bg-industrial-card/50 border border-industrial-border p-4 space-y-4">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center py-12">
            <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-industrial-primary/10 mb-4">
              <Bot className="h-8 w-8 text-industrial-primary/60" />
            </div>
            <p className="text-sm text-industrial-text-secondary mb-2">开始与 AI 助手对话</p>
            <p className="text-xs text-industrial-text-muted">我可以帮您查询设备状态、生产进度、库存信息等</p>
          </div>
        )}

        {messages.map((msg) => (
          <div key={msg.id} className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
            {/* 头像 */}
            <div className={`flex-shrink-0 h-8 w-8 rounded-lg flex items-center justify-center ${
              msg.role === 'user'
                ? 'bg-industrial-primary/20 border border-industrial-primary/30'
                : 'bg-industrial-accent/20 border border-industrial-accent/30'
            }`}>
              {msg.role === 'user' 
                ? <User className="h-4 w-4 text-industrial-primary" />
                : <Bot className="h-4 w-4 text-industrial-accent" />
              }
            </div>

            {/* 消息内容 */}
            <div className={`max-w-[75%] ${msg.role === 'user' ? 'items-end' : 'items-start'} space-y-1`}>
              <div className={`rounded-2xl px-4 py-3 ${
                msg.role === 'user'
                  ? 'bg-industrial-primary/15 border border-industrial-primary/25 text-industrial-text'
                  : 'bg-industrial-card border border-industrial-border text-industrial-text'
              }`}>
                <p className="text-sm leading-relaxed whitespace-pre-wrap">
                  {msg.content}
                  {msg.isStreaming && <span className="streaming-cursor"></span>}
                </p>
              </div>

              {/* 推理轨迹 */}
              {msg.trace && msg.trace.length > 0 && (
                <TraceTimeline
                  trace={msg.trace}
                  expanded={expandedTrace === msg.id}
                  onToggle={() => setExpandedTrace(expandedTrace === msg.id ? null : msg.id)}
                />
              )}

              {/* 时间戳 */}
              <p className={`text-[11px] text-industrial-text-muted px-1 ${msg.role === 'user' ? 'text-right' : ''}`}>
                {msg.timestamp.toLocaleTimeString('zh-CN')}
                {msg.intent && ` · ${msg.intent}`}
              </p>
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* 快捷提问 */}
      {!isStreaming && messages.length > 0 && messages.length < 3 && (
        <div className="flex flex-wrap gap-2">
          {QUICK_QUESTIONS.map((q) => (
            <button
              key={q}
              onClick={() => sendMessage(q)}
              className="rounded-full px-3 py-1.5 text-xs text-industrial-text-secondary bg-industrial-card border border-industrial-border hover:border-industrial-primary/50 hover:text-industrial-primary transition-colors"
            >
              {q}
            </button>
          ))}
        </div>
      )}

      {/* 输入框 */}
      <div className="flex items-center gap-3 rounded-xl bg-industrial-card border border-industrial-border px-4 py-3 focus-within:border-industrial-primary/50 focus-within:glow-border transition-all">
        <input
          ref={inputRef}
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="输入您的问题..."
          disabled={isStreaming}
          className="flex-1 bg-transparent text-sm text-industrial-text placeholder:text-industrial-text-muted outline-none disabled:opacity-50"
        />
        <button
          onClick={() => sendMessage()}
          disabled={isStreaming || !input.trim()}
          className="flex h-8 w-8 items-center justify-center rounded-lg bg-industrial-primary hover:bg-industrial-primary-hover transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
        >
          <Send className="h-4 w-4 text-white" />
        </button>
      </div>
    </div>
  )
}

// 轨迹时间线组件
function TraceTimeline({ trace, expanded, onToggle }: { trace: TraceStep[]; expanded: boolean; onToggle: () => void }) {
  const stepConfig = {
    think: { color: 'text-blue-400', bgColor: 'bg-blue-500/10', borderColor: 'border-blue-500/30', icon: '💡', label: '思考' },
    action: { color: 'text-amber-400', bgColor: 'bg-amber-500/10', borderColor: 'border-amber-500/30', icon: '🔧', label: '行动' },
    observe: { color: 'text-purple-400', bgColor: 'bg-purple-500/10', borderColor: 'border-purple-500/30', icon: '👁', label: '观察' },
  }

  return (
    <div className="mt-2 rounded-lg border border-industrial-border/50 overflow-hidden">
      <button
        onClick={onToggle}
        className="flex w-full items-center justify-between px-3 py-2 text-xs text-industrial-text-secondary hover:bg-industrial-card-hover/50 transition-colors"
      >
        <span>推理轨迹 ({trace.length} 步)</span>
        {expanded ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
      </button>

      {expanded && (
        <div className="border-t border-industrial-border/30 px-3 py-2 space-y-2 max-h-48 overflow-y-auto">
          {trace.map((step, i) => {
            const config = stepConfig[step.step_type]
            return (
              <div key={i} className={`flex gap-2.5 rounded-md ${config.bgColor} border ${config.borderColor} p-2.5`}>
                <span className="text-sm">{config.icon}</span>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-0.5">
                    <span className={`text-[11px] font-medium ${config.color}`}>{config.label}</span>
                    {step.duration_ms && (
                      <span className="text-[10px] text-industrial-text-muted">{step.duration_ms}ms</span>
                    )}
                  </div>
                  <p className="text-xs text-industrial-text-secondary leading-relaxed break-all">{step.content}</p>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
