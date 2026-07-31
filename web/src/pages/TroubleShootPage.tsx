import { useState, useRef } from 'react'
import {
  Wrench, Zap, Flame, AlertTriangle, Search, Lightbulb,
  ChevronRight, Wind, Settings2, Activity, Thermometer,
  HelpCircle, MessageSquare, Loader2, Sparkles
} from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import Markdown from '../components/Markdown'

// 故障类别配置
const faultCategories = [
  { id: 'arc', name: '起弧异常', desc: '难以引弧、电弧不稳、断弧', icon: Zap, color: 'amber', count: 8 },
  { id: 'defect', name: '焊缝缺陷', desc: '气孔、夹渣、裂纹、咬边等', icon: AlertTriangle, color: 'red', count: 12 },
  { id: 'wire', name: '送丝异常', desc: '送丝不均、堵丝、爆丝', icon: Settings2, color: 'blue', count: 6 },
  { id: 'gas', name: '气体保护', desc: '气流量不稳、保护不良', icon: Wind, color: 'cyan', count: 5 },
  { id: 'temp', name: '温度报警', desc: '设备过热、温度异常', icon: Thermometer, color: 'orange', count: 4 },
  { id: 'elec', name: '电气故障', desc: '电源异常、通讯故障', icon: Activity, color: 'purple', count: 7 },
]

// 常见故障库
interface FaultEntry {
  id: number
  symptom: string
  category: string
  cause: string
  solution: string
  severity: 'high' | 'medium' | 'low'
}

const faultLibrary: FaultEntry[] = [
  {
    id: 1,
    symptom: '难以引弧或频繁断弧',
    category: '起弧异常',
    cause: '电流设置过低 / 钨极氧化 / 接地不良',
    solution: '检查电流设置、清理钨极、确认工件接地良好',
    severity: 'high',
  },
  {
    id: 2,
    symptom: '焊缝表面出现气孔',
    category: '焊缝缺陷',
    cause: '保护气体不纯 / 工件表面油污锈迹 / 气流量过大或过小',
    solution: '更换气体、检查气路、清理工件表面、调整流量至15-20L/min',
    severity: 'high',
  },
  {
    id: 3,
    symptom: '焊缝有夹渣',
    category: '焊缝缺陷',
    cause: '层间清理不彻底 / 焊接电流过低 / 焊接速度过快',
    solution: '加强层间打磨、提高电流、降低焊接速度',
    severity: 'medium',
  },
  {
    id: 4,
    symptom: '送丝不均匀、有卡顿',
    category: '送丝异常',
    cause: '导电嘴磨损 / 送丝管堵塞 / 压轮压力不当',
    solution: '更换导电嘴、清理送丝管、调整压轮压力',
    severity: 'medium',
  },
  {
    id: 5,
    symptom: '焊缝出现咬边',
    category: '焊缝缺陷',
    cause: '焊接电流过大 / 焊接速度过快 / 运条角度不当',
    solution: '适当降低电流、调整速度、保持正确运条角度',
    severity: 'low',
  },
  {
    id: 6,
    symptom: '设备温度过高报警',
    category: '温度报警',
    cause: '长时间高负荷运行 / 散热风扇故障 / 环境温度过高',
    solution: '停机降温、检查风扇、降低负载、改善通风',
    severity: 'high',
  },
  {
    id: 7,
    symptom: '气体流量不稳定',
    category: '气体保护',
    cause: '气瓶压力低 / 减压阀故障 / 管路漏气',
    solution: '更换气瓶、检查减压阀、检测管路密封',
    severity: 'medium',
  },
  {
    id: 8,
    symptom: '电弧漂移、磁偏吹',
    category: '起弧异常',
    cause: '工件磁性 / 接地位置不对称 / 电缆走向不合理',
    solution: '调整接地位置、改变电缆走向、分段焊接',
    severity: 'low',
  },
]

const severityConfig = {
  high: { label: '严重', color: 'bg-red-500/15 text-red-400 border-red-500/30' },
  medium: { label: '中等', color: 'bg-amber-500/15 text-amber-400 border-amber-500/30' },
  low: { label: '轻微', color: 'bg-green-500/15 text-green-400 border-green-500/30' },
}

const colorMap: Record<string, { bg: string; text: string; border: string }> = {
  amber: { bg: 'bg-amber-500/10', text: 'text-amber-400', border: 'border-amber-500/30' },
  red: { bg: 'bg-red-500/10', text: 'text-red-400', border: 'border-red-500/30' },
  blue: { bg: 'bg-blue-500/10', text: 'text-blue-400', border: 'border-blue-500/30' },
  cyan: { bg: 'bg-cyan-500/10', text: 'text-cyan-400', border: 'border-cyan-500/30' },
  orange: { bg: 'bg-orange-500/10', text: 'text-orange-400', border: 'border-orange-500/30' },
  purple: { bg: 'bg-purple-500/10', text: 'text-purple-400', border: 'border-purple-500/30' },
}

export default function TroubleShootPage() {
  const navigate = useNavigate()
  const [selectedCategory, setSelectedCategory] = useState<string>('all')
  const [searchQuery, setSearchQuery] = useState('')
  const [diagInput, setDiagInput] = useState('')
  const [diaging, setDiaging] = useState(false)
  const [diagThinking, setDiagThinking] = useState(false)
  const [diagContent, setDiagContent] = useState('')
  const [diagRefs, setDiagRefs] = useState<string[]>([])
  const abortRef = useRef<AbortController | null>(null)

  const filteredFaults = faultLibrary.filter(f => {
    const matchCategory = selectedCategory === 'all' || f.category === selectedCategory
    const q = searchQuery.trim().toLowerCase()
    const matchSearch = !q ||
      f.symptom.toLowerCase().includes(q) ||
      f.cause.toLowerCase().includes(q) ||
      f.solution.toLowerCase().includes(q)
    return matchCategory && matchSearch
  })

  // AI 流式诊断 (调用 /api/chat，解析 event:/data: SSE)
  async function runDiagnosis() {
    if (!diagInput.trim() || diaging) return
    setDiaging(true)
    setDiagThinking(true)
    setDiagContent('')
    setDiagRefs([])

    const controller = new AbortController()
    abortRef.current = controller

    try {
      const resp = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: `【故障诊断】请根据以下故障现象，结合焊接知识库给出排查建议：${diagInput}`,
        }),
        signal: controller.signal,
      })

      if (!resp.ok || !resp.body) throw new Error('API unavailable')

      const reader = resp.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      let currentEvent = ''

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
            currentEvent = trimmed.slice(6).trim()
            continue
          }

          if (trimmed.startsWith('data:')) {
            const dataStr = trimmed.slice(5).trim()

            if (currentEvent === 'done' || dataStr === '[DONE]') {
              setDiagThinking(false)
              setDiaging(false)
              continue
            }

            if (currentEvent === 'answer_chunk') {
              // DeepSeek token 级流式 — 逐字追加
              setDiagThinking(false)
              setDiagContent(prev => prev + dataStr)
              continue
            }

            if (currentEvent === 'trace_step') {
              try {
                const parsed = JSON.parse(dataStr)
                if (parsed.step_type === 'think') {
                  setDiagThinking(true)
                }
              } catch { /* ignore */ }
              continue
            }

            // 旧格式兼容: answer 事件含完整JSON
            if (currentEvent === 'answer') {
              setDiagThinking(false)
              try {
                const parsed = JSON.parse(dataStr)
                setDiagContent(parsed.answer || '')
              } catch {
                setDiagContent(dataStr)
              }
              continue
            }

            // 无法识别的事件 — 尝试作为答案追加
            if (dataStr !== '' && dataStr !== '[DONE]') {
              try {
                const parsed = JSON.parse(dataStr)
                if (parsed.answer) {
                  setDiagThinking(false)
                  setDiagContent(parsed.answer)
                } else if (!parsed.step_type) {
                  setDiagThinking(false)
                  setDiagContent(prev => prev + (parsed.content || ''))
                }
              } catch {
                // 纯文本, 可能是未标注类型的 chunk
              }
            }
          }
        }
      }
    } catch (err: any) {
      if (err.name !== 'AbortError') {
        setDiagThinking(false)
        setDiagContent('未能完成在线诊断，请检查后端接口或网络。建议前往「AI 对话」详细描述故障现象、当前焊接参数、设备型号等，获取更精准的诊断结果。')
      }
    } finally {
      if (!controller.signal.aborted) {
        setDiagThinking(false)
        setDiaging(false)
      }
    }
  }

  return (
    <div className="flex h-full flex-col gap-4">
      {/* 标题栏 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-orange-500/20 to-red-600/20 border border-orange-500/30">
            <Wrench className="h-5 w-5 text-orange-400" />
          </div>
          <div>
            <h1 className="text-lg font-semibold text-industrial-text">故障排查中心</h1>
            <p className="text-xs text-industrial-text-muted">智能诊断 + 常见故障库 + 排查流程指引</p>
          </div>
        </div>
      </div>

      {/* 故障类别卡片 */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        {faultCategories.map(cat => {
          const c = colorMap[cat.color]
          const isActive = selectedCategory === cat.name
          return (
            <button
              key={cat.id}
              onClick={() => setSelectedCategory(isActive ? 'all' : cat.name)}
              className={`glass-card rounded-xl p-3 text-left transition-all hover:scale-[1.02] ${isActive ? 'glow-border-accent' : ''}`}
            >
              <div className={`flex h-8 w-8 items-center justify-center rounded-lg ${c.bg} ${c.text} mb-2`}>
                <cat.icon className="h-4 w-4" />
              </div>
              <p className="text-sm font-medium text-industrial-text">{cat.name}</p>
              <p className="text-[11px] text-industrial-text-muted line-clamp-2 mt-0.5">{cat.desc}</p>
              <p className={`text-[11px] mt-1.5 tabular-nums ${c.text}`}>{cat.count} 个常见故障</p>
            </button>
          )
        })}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 flex-1 min-h-0">
        {/* AI 智能诊断 */}
        <div className="glass-card rounded-xl p-4 flex flex-col">
          <div className="flex items-center gap-2 mb-3">
            <div className="flex h-7 w-7 items-center justify-center rounded-md bg-industrial-primary/15">
              <Lightbulb className="h-4 w-4 text-industrial-primary" />
            </div>
            <h2 className="text-sm font-medium text-industrial-text">AI 智能诊断</h2>
          </div>
          <p className="text-xs text-industrial-text-muted mb-3">
            描述您遇到的故障现象（越详细越准确），AI 将基于知识库给出排查建议。
          </p>
          <textarea
            value={diagInput}
            onChange={(e) => setDiagInput(e.target.value)}
            placeholder="例如：焊接过程中出现频繁断弧，焊缝表面有气孔..."
            className="w-full h-28 px-3 py-2 rounded-lg bg-industrial-bg border border-industrial-border text-sm text-industrial-text placeholder:text-industrial-text-muted focus:border-industrial-primary/50 focus:outline-none resize-none transition-colors"
          />
          <div className="flex gap-2 mt-3">
            {diaging ? (
              <button
                onClick={() => abortRef.current?.abort()}
                className="flex-1 flex items-center justify-center gap-1.5 rounded-lg bg-industrial-accent px-4 py-2 text-sm font-medium text-white hover:bg-industrial-accent-hover transition-colors"
              >
                停止
              </button>
            ) : (
              <button
                onClick={runDiagnosis}
                disabled={!diagInput.trim()}
                className="flex-1 flex items-center justify-center gap-1.5 rounded-lg bg-industrial-primary px-4 py-2 text-sm font-medium text-white hover:bg-industrial-primary-hover disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
              >
                <Search className="h-4 w-4" />
                开始诊断
              </button>
            )}
            <button
              onClick={() => navigate('/')}
              className="flex items-center gap-1.5 rounded-lg bg-industrial-card border border-industrial-border px-3 py-2 text-xs text-industrial-text-secondary hover:border-industrial-accent/50 hover:text-industrial-text transition-colors"
              title="前往 AI 对话获取更详细的诊断"
            >
              <MessageSquare className="h-3.5 w-3.5" />
              详细咨询
            </button>
          </div>

          {/* 思考中状态 */}
          {diagThinking && (
            <div className="mt-3 p-3 rounded-lg bg-industrial-primary/5 border border-industrial-primary/20">
              <div className="flex items-center gap-2 mb-2">
                <Loader2 className="h-3.5 w-3.5 text-industrial-primary animate-spin" />
                <span className="text-xs font-medium text-industrial-primary">思考中...</span>
              </div>
              <p className="text-xs text-industrial-text-muted">AI 正在分析故障原因，检索相关知识库...</p>
            </div>
          )}

          {/* 流式输出结果 */}
          {diagContent && (
            <div className="mt-3 p-3 rounded-lg bg-industrial-accent/10 border border-industrial-accent/30 flex-1 overflow-auto">
              <div className="flex items-center gap-1.5 mb-2">
                <Sparkles className="h-3.5 w-3.5 text-industrial-accent" />
                <span className="text-xs font-medium text-industrial-accent">诊断建议</span>
                {diaging && (
                  <span className="inline-block h-2.5 w-0.5 bg-industrial-accent/60 animate-blink ml-1" />
                )}
              </div>
              <p className="text-xs text-industrial-text leading-relaxed"><Markdown text={diagContent} /></p>
            </div>
          )}
        </div>

        {/* 故障库 */}
        <div className="glass-card rounded-xl flex flex-col lg:col-span-2 overflow-hidden">
          <div className="flex items-center justify-between px-4 py-3 border-b border-industrial-border">
            <div className="flex items-center gap-2">
              <Flame className="h-4 w-4 text-industrial-accent" />
              <span className="text-sm font-medium text-industrial-text">常见故障库</span>
              <span className="text-xs text-industrial-text-muted">({filteredFaults.length})</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="relative">
                <Search className="absolute left-2 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-industrial-text-muted" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="搜索故障..."
                  className="w-40 pl-7 pr-2 py-1.5 text-xs rounded-md bg-industrial-bg border border-industrial-border text-industrial-text placeholder:text-industrial-text-muted focus:border-industrial-primary/50 focus:outline-none"
                />
              </div>
              {selectedCategory !== 'all' && (
                <button
                  onClick={() => setSelectedCategory('all')}
                  className="flex items-center gap-1 text-xs text-industrial-accent hover:underline"
                >
                  清除筛选
                </button>
              )}
            </div>
          </div>

          <div className="flex-1 overflow-auto p-3 space-y-2">
            {filteredFaults.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-40 text-industrial-text-muted text-sm gap-2">
                <HelpCircle className="h-6 w-6 opacity-40" />
                <span>未找到匹配的故障，尝试调整搜索或前往 AI 对话</span>
              </div>
            ) : (
              filteredFaults.map(fault => (
                <div
                  key={fault.id}
                  className="group p-3 rounded-lg bg-industrial-bg/50 border border-industrial-border hover:border-industrial-primary/40 hover:bg-industrial-card-hover/30 transition-all cursor-pointer"
                >
                  <div className="flex items-start justify-between gap-3 mb-2">
                    <div className="flex items-center gap-2 flex-1 min-w-0">
                      <ChevronRight className="h-3.5 w-3.5 text-industrial-text-muted group-hover:text-industrial-accent shrink-0 transition-colors" />
                      <span className="text-sm font-medium text-industrial-text truncate">{fault.symptom}</span>
                    </div>
                    <span className={`text-[10px] px-1.5 py-0.5 rounded border shrink-0 ${severityConfig[fault.severity].color}`}>
                      {severityConfig[fault.severity].label}
                    </span>
                  </div>
                  <div className="ml-5 space-y-1.5">
                    <div className="flex gap-2 text-xs">
                      <span className="text-industrial-text-muted shrink-0">可能原因：</span>
                      <span className="text-industrial-text-secondary">{fault.cause}</span>
                    </div>
                    <div className="flex gap-2 text-xs">
                      <span className="text-industrial-text-muted shrink-0">解决方案：</span>
                      <span className="text-industrial-text">{fault.solution}</span>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  )
}