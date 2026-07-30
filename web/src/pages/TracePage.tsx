import { useState } from 'react'
import { GitBranch, Search, Lightbulb, ArrowRight, Clock, Cpu, Eye, Wrench } from 'lucide-react'
import api from '../services/http'

interface TraceStep {
  step_type: 'think' | 'action' | 'observe'
  content: string
  timestamp: string
  duration_ms?: number
  detail?: any
}

interface TraceData {
  session_id: string
  query: string
  intent: string
  routed_agents: string[]
  steps: TraceStep[]
  created_at: string
  total_duration_ms: number
}

export default function TracePage() {
  const [sessionId, setSessionId] = useState('')
  const [traceData, setTraceData] = useState<TraceData | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [expandedStep, setExpandedStep] = useState<number | null>(null)

  async function handleSearch() {
    if (!sessionId.trim()) return

    try {
      setLoading(true)
      setError('')
      const data = await api.get<any>(`/sessions/${sessionId.trim()}/trace`)
      setTraceData(data as TraceData)
    } catch (err: any) {
      console.error('[Trace] Error:', err)
      setError(err.message || '查询失败，请检查 Session ID')
      setTraceData(null)
    } finally {
      setLoading(false)
    }
  }

  const stepIcons = {
    think: { icon: Lightbulb, color: 'text-blue-400', bgColor: 'bg-blue-500/15', borderColor: 'border-blue-500/30', label: '思考' },
    action: { icon: Wrench, color: 'text-amber-400', bgColor: 'bg-amber-500/15', borderColor: 'border-amber-500/30', label: '行动' },
    observe: { icon: Eye, color: 'text-purple-400', bgColor: 'bg-purple-500/15', borderColor: 'border-purple-500/30', label: '观察' },
  }

  return (
    <div className="flex h-full flex-col gap-4">
      {/* 标题栏 */}
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-violet-500/20 to-purple-600/20 border border-violet-500/30">
          <GitBranch className="h-5 w-5 text-violet-400" />
        </div>
        <div>
          <h1 className="text-lg font-semibold text-industrial-text">执行轨迹追踪</h1>
          <p className="text-xs text-industrial-text-muted">查看 Agent 推理链路与执行过程</p>
        </div>
      </div>

      {/* 搜索栏 */}
      <div className="flex gap-3">
        <div className="flex-1 flex items-center gap-3 rounded-xl bg-industrial-card border border-industrial-border px-4 focus-within:border-industrial-primary/50 transition-colors">
          <Search className="h-4 w-4 text-industrial-text-muted shrink-0" />
          <input
            type="text"
            value={sessionId}
            onChange={(e) => setSessionId(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            placeholder="输入 Session ID 查询轨迹..."
            className="flex-1 bg-transparent text-sm text-industrial-text placeholder:text-industrial-text-muted outline-none py-2.5"
          />
        </div>
        <button
          onClick={handleSearch}
          disabled={loading || !sessionId.trim()}
          className="flex items-center gap-2 rounded-xl bg-industrial-primary hover:bg-industrial-primary-hover px-5 py-2.5 text-sm font-medium text-white transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
        >
          {loading ? (
            <>
              <div className="h-4 w-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
              查询中...
            </>
          ) : (
            <>
              <Search className="h-4 w-4" />
              查询轨迹
            </>
          )}
        </button>
      </div>

      {/* 错误提示 */}
      {error && (
        <div className="rounded-xl bg-red-500/10 border border-red-500/30 px-4 py-3 text-sm text-red-400">
          {error}
        </div>
      )}

      {/* 轨迹结果 */}
      {traceData && (
        <div className="flex-1 overflow-auto space-y-4">
          {/* 会话概览 */}
          <div className="glass-card rounded-xl p-5">
            <div className="flex items-center justify-between mb-4">
              <div>
                <p className="text-xs text-industrial-text-muted mb-1">Session ID</p>
                <p className="font-mono text-sm text-industrial-primary">{traceData.session_id}</p>
              </div>
              <div className="text-right">
                <p className="text-xs text-industrial-text-muted mb-1">总耗时</p>
                <p className="text-sm font-medium text-industrial-text tabular-nums">{traceData.total_duration_ms}ms</p>
              </div>
            </div>

            <div className="flex flex-wrap gap-3">
              <div className="flex items-center gap-2 rounded-lg bg-industrial-bg px-3 py-1.5">
                <Cpu className="h-3.5 w-3.5 text-industrial-info" />
                <span className="text-xs text-industrial-text-secondary">意图：</span>
                <span className="text-xs font-medium text-industrial-info">{traceData.intent}</span>
              </div>
              <div className="flex items-center gap-2 rounded-lg bg-industrial-bg px-3 py-1.5">
                <ArrowRight className="h-3.5 w-3.5 text-industrial-accent" />
                <span className="text-xs text-industrial-text-secondary">路由到：</span>
                <span className="text-xs font-medium text-industrial-accent">{traceData.routed_agents.join(', ')}</span>
              </div>
              <div className="flex items-center gap-2 rounded-lg bg-industrial-bg px-3 py-1.5">
                <Clock className="h-3.5 w-3.5 text-industrial-text-muted" />
                <span className="text-xs text-industrial-text-muted">{traceData.created_at}</span>
              </div>
            </div>

            <div className="mt-4 pt-4 border-t border-industrial-border/50">
              <p className="text-xs text-industrial-text-muted mb-1">用户查询</p>
              <p className="text-sm text-industrial-text">{traceData.query}</p>
            </div>
          </div>

          {/* 时间线 */}
          <div className="glass-card rounded-xl p-5">
            <p className="text-sm font-medium text-industrial-text mb-4">执行时间线</p>

            <div className="relative space-y-4 before:absolute before:left-[19px] before:top-2 before:bottom-2 before:w-px before:bg-industrial-border">
              {traceData.steps.map((step, index) => {
                const config = stepIcons[step.step_type]
                const Icon = config.icon

                return (
                  <div key={index} className="relative flex gap-4 pl-0">
                    {/* 时间线节点 */}
                    <div className="relative z-10 flex flex-col items-center">
                      <div className={`flex h-10 w-10 items-center justify-center rounded-xl ${config.bgColor} border ${config.borderColor}`}>
                        <Icon className={`h-4.5 w-4.5 ${config.color}`} />
                      </div>
                      {index < traceData.steps.length - 1 && (
                        <div className="w-px h-full bg-industrial-border mt-1" />
                      )}
                    </div>

                    {/* 内容卡片 */}
                    <div className={`flex-1 rounded-xl ${config.bgColor} border ${config.borderColor} p-4 cursor-pointer transition-all hover:shadow-lg`}
                      onClick={() => setExpandedStep(expandedStep === index ? null : index)}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <Icon className={`h-4 w-4 ${config.color}`} />
                          <span className={`text-xs font-medium ${config.color}`}>{config.label}</span>
                        </div>
                        <div className="flex items-center gap-3">
                          {step.duration_ms && (
                            <span className="text-[11px] text-industrial-text-muted tabular-nums">{step.duration_ms}ms</span>
                          )}
                          <span className="text-[11px] text-industrial-text-muted">{step.timestamp.split(' ')[1]}</span>
                        </div>
                      </div>

                      <p className="text-sm text-industrial-text leading-relaxed">{step.content}</p>

                      {/* 展开详情 */}
                      {expandedStep === index && step.detail && (
                        <pre className="mt-3 p-3 rounded-lg bg-industrial-bg/50 text-xs text-industrial-text-muted overflow-x-auto whitespace-pre-wrap">
                          {JSON.stringify(step.detail, null, 2)}
                        </pre>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        </div>
      )}

      {/* 空状态 */}
      {!traceData && !loading && !error && (
        <div className="flex-1 flex flex-col items-center justify-center text-center py-16">
          <div className="flex h-20 w-20 items-center justify-center rounded-2xl bg-industrial-card border border-industrial-border mb-5">
            <GitBranch className="h-10 w-10 text-industrial-text-muted/40" />
          </div>
          <p className="text-sm text-industrial-text-secondary mb-1">查询 Agent 执行轨迹</p>
          <p className="text-xs text-industrial-text-muted">输入从 AI 对话获取的 Session ID，查看完整的推理过程</p>
        </div>
      )}
    </div>
  )
}
