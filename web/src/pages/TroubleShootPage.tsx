import { useState, useRef, useEffect } from 'react'
import {
  Wrench, Zap, Flame, AlertTriangle, Search, Lightbulb,
  ChevronRight, Wind, Settings2, Activity, Thermometer,
  HelpCircle, MessageSquare, Loader2, Sparkles, Cpu, Boxes,
  Plus, X, Trash2
} from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
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

// 设备/传感器类型图标映射
const deviceTypeIcons: Record<string, typeof Cpu> = {
  'MIG焊机': Cpu,
  'TIG焊机': Cpu,
  'MAG焊机': Cpu,
  '机器人焊机': Boxes,
  'MIG焊枪头': Wrench,
  'TIG焊枪头': Wrench,
}

// 设备类型颜色映射
const deviceTypeColors: Record<string, string> = {
  'MIG焊机': 'sky',
  'TIG焊机': 'violet',
  'MAG焊机': 'emerald',
  '机器人焊机': 'rose',
  'MIG焊枪头': 'amber',
  'TIG焊枪头': 'amber',
}

// 故障记录数据结构
interface FaultEntry {
  id: number
  symptom: string
  category: string
  device_type?: string | null
  cause?: string | null
  solution?: string | null
  severity: 'high' | 'medium' | 'low'
  recorder?: string
  created_at?: string
}

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
  sky: { bg: 'bg-sky-500/10', text: 'text-sky-400', border: 'border-sky-500/30' },
  violet: { bg: 'bg-violet-500/10', text: 'text-violet-400', border: 'border-violet-500/30' },
  emerald: { bg: 'bg-emerald-500/10', text: 'text-emerald-400', border: 'border-emerald-500/30' },
  rose: { bg: 'bg-rose-500/10', text: 'text-rose-400', border: 'border-rose-500/30' },
}

// 远端设备类型
interface DeviceInfo {
  id: string
  name: string
  type: string
  status: string
  parent_id: string | null
}

export default function TroubleShootPage() {
  const navigate = useNavigate()
  const { user } = useAuth()
  const [selectedCategory, setSelectedCategory] = useState<string>('all')
  const [searchQuery, setSearchQuery] = useState('')
  const [diagInput, setDiagInput] = useState('')
  const [diaging, setDiaging] = useState(false)
  const [diagThinking, setDiagThinking] = useState(false)
  const [diagContent, setDiagContent] = useState('')
  const [diagRefs, setDiagRefs] = useState<string[]>([])
  const abortRef = useRef<AbortController | null>(null)

  // 设备类型分类（新增）
  const [devices, setDevices] = useState<DeviceInfo[]>([])
  const [selectedDeviceType, setSelectedDeviceType] = useState<string>('all')
  const [selectedDeviceId, setSelectedDeviceId] = useState<string>('all')

  // 故障库（从后端拉取）
  const [faults, setFaults] = useState<FaultEntry[]>([])
  const [showFaultModal, setShowFaultModal] = useState(false)
  const [submitting, setSubmitting] = useState(false)

  // 拉取设备列表 + 故障库
  const loadFaults = () => {
    fetch('/api/faults')
      .then(r => r.json())
      .then(data => setFaults(data.faults || []))
      .catch(() => setFaults([]))
  }

  useEffect(() => {
    fetch('/api/devices')
      .then(r => r.json())
      .then(data => {
        const list: DeviceInfo[] = data.devices || data || []
        setDevices(list)
      })
      .catch(() => setDevices([]))
    loadFaults()
  }, [])

  // 派生：去重后的设备类型列表（含计数）
  const deviceTypes = (() => {
    const map = new Map<string, number>()
    for (const d of devices) {
      map.set(d.type, (map.get(d.type) || 0) + 1)
    }
    return Array.from(map.entries()).map(([type, count]) => ({ type, count }))
  })()

  // 派生：当前选中类型下的具体设备列表
  const devicesOfSelectedType = selectedDeviceType === 'all'
    ? []
    : devices.filter(d => d.type === selectedDeviceType)

  // 切换设备类型时重置具体设备选择
  function handleSelectDeviceType(type: string) {
    setSelectedDeviceType(prev => prev === type ? 'all' : type)
    setSelectedDeviceId('all')
  }

  const filteredFaults = faults.filter(f => {
    const matchCategory = selectedCategory === 'all' || f.category === selectedCategory
    const matchDeviceType = selectedDeviceType === 'all' || !f.device_type || f.device_type === selectedDeviceType
    const q = searchQuery.trim().toLowerCase()
    const matchSearch = !q ||
      f.symptom.toLowerCase().includes(q) ||
      (f.cause || '').toLowerCase().includes(q) ||
      (f.solution || '').toLowerCase().includes(q)
    return matchCategory && matchDeviceType && matchSearch
  })

  // 新增故障
  async function handleCreateFault(payload: Record<string, unknown>) {
    setSubmitting(true)
    try {
      const resp = await fetch('/api/faults', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...payload, recorder: user?.username || '匿名' }),
      })
      if (!resp.ok) throw new Error('新增失败')
      setShowFaultModal(false)
      loadFaults()
    } catch (e) {
      alert('新增故障失败，请稍后重试')
    } finally {
      setSubmitting(false)
    }
  }

  // 删除故障
  async function handleDeleteFault(id: number) {
    if (!confirm('确认删除这条故障记录？')) return
    try {
      const resp = await fetch(`/api/faults/${id}`, { method: 'DELETE' })
      if (!resp.ok) throw new Error('删除失败')
      loadFaults()
    } catch {
      alert('删除失败，请稍后重试')
    }
  }

  // AI 流式诊断 (调用 /api/chat，解析 event:/data: SSE)
  async function runDiagnosis() {
    if (!diagInput.trim() || diaging) return
    setDiaging(true)
    setDiagThinking(true)
    setDiagContent('')
    setDiagRefs([])

    const controller = new AbortController()
    abortRef.current = controller

    // 组装上下文：设备类型 + 具体设备 + 故障类别
    const ctxParts: string[] = []
    if (selectedDeviceType !== 'all') {
      ctxParts.push(`设备类型：${selectedDeviceType}`)
      if (selectedDeviceId !== 'all') {
        const dev = devices.find(d => d.id === selectedDeviceId)
        if (dev) ctxParts.push(`具体设备：${dev.name}（ID: ${dev.id}，状态: ${dev.status}）`)
      }
    }
    if (selectedCategory !== 'all') {
      ctxParts.push(`故障类别：${selectedCategory}`)
    }
    const ctxPrefix = ctxParts.length > 0
      ? `【诊断上下文】${ctxParts.join('；')}。\n`
      : ''
    const message = `${ctxPrefix}【故障诊断】请根据以下故障现象，结合焊接知识库与上述设备类型/传感器特性，给出精准定位与排查建议：${diagInput}`

    try {
      const resp = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message }),
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

      {/* 设备/传感器类型分类（可选筛选维度） */}
      <div>
        <div className="flex items-center gap-2 mb-2">
          <Cpu className="h-4 w-4 text-industrial-primary" />
          <h2 className="text-sm font-medium text-industrial-text">设备/传感器类型</h2>
          <span className="text-xs text-industrial-text-muted">（可选）用于聚焦某类设备相关的故障，便于模型精准定位传感器与故障点</span>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
          {deviceTypes.map(({ type, count }) => {
            const Icon = deviceTypeIcons[type] || Cpu
            const colorKey = deviceTypeColors[type] || 'sky'
            const c = colorMap[colorKey]
            const isActive = selectedDeviceType === type
            return (
              <button
                key={type}
                onClick={() => handleSelectDeviceType(type)}
                className={`glass-card rounded-xl p-3 text-left transition-all hover:scale-[1.02] ${isActive ? 'glow-border-accent' : ''}`}
              >
                <div className={`flex h-8 w-8 items-center justify-center rounded-lg ${c.bg} ${c.text} mb-2`}>
                  <Icon className="h-4 w-4" />
                </div>
                <p className="text-sm font-medium text-industrial-text">{type}</p>
                <p className={`text-[11px] mt-1.5 tabular-nums ${c.text}`}>{count} 台设备</p>
              </button>
            )
          })}
          {deviceTypes.length === 0 && (
            <div className="col-span-full text-xs text-industrial-text-muted py-3">设备列表加载中...</div>
          )}
        </div>

        {/* 选中类型后，可进一步指定具体设备（非步骤，仅细化） */}
        {selectedDeviceType !== 'all' && devicesOfSelectedType.length > 0 && (
          <div className="mt-3 flex items-center gap-3">
            <label className="text-xs text-industrial-text-muted shrink-0">指定具体设备（可选）：</label>
            <select
              value={selectedDeviceId}
              onChange={(e) => setSelectedDeviceId(e.target.value)}
              className="flex-1 max-w-xs px-3 py-1.5 rounded-md bg-industrial-bg border border-industrial-border text-sm text-industrial-text focus:border-industrial-primary/50 focus:outline-none"
            >
              <option value="all">全部 {selectedDeviceType}（不指定具体设备）</option>
              {devicesOfSelectedType.map(d => (
                <option key={d.id} value={d.id}>
                  {d.name}（{d.id}）{d.status === 'offline' ? ' [离线]' : ''}
                </option>
              ))}
            </select>
            {selectedDeviceId !== 'all' && (
              <button
                onClick={() => setSelectedDeviceId('all')}
                className="text-xs text-industrial-accent hover:underline"
              >
                清除
              </button>
            )}
          </div>
        )}
      </div>

      {/* 故障类别卡片（可选筛选维度） */}
      <div>
        <div className="flex items-center gap-2 mb-2">
          <AlertTriangle className="h-4 w-4 text-amber-400" />
          <h2 className="text-sm font-medium text-industrial-text">故障类别</h2>
          <span className="text-xs text-industrial-text-muted">（可选）过滤下方常见故障库，并作为上下文传给 AI</span>
        </div>
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
              <button
                onClick={() => setShowFaultModal(true)}
                className="flex items-center gap-1 text-xs px-2.5 py-1.5 rounded-md bg-industrial-primary/15 text-industrial-primary border border-industrial-primary/30 hover:bg-industrial-primary/25 transition-colors"
                title="记录一个常见故障到故障库"
              >
                <Plus className="h-3.5 w-3.5" />
                新增故障
              </button>
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
                  className="group p-3 rounded-lg bg-industrial-bg/50 border border-industrial-border hover:border-industrial-primary/40 hover:bg-industrial-card-hover/30 transition-all"
                >
                  <div className="flex items-start justify-between gap-3 mb-2">
                    <div className="flex items-center gap-2 flex-1 min-w-0">
                      <ChevronRight className="h-3.5 w-3.5 text-industrial-text-muted group-hover:text-industrial-accent shrink-0 transition-colors" />
                      <span className="text-sm font-medium text-industrial-text truncate">{fault.symptom}</span>
                    </div>
                    <div className="flex items-center gap-1.5 shrink-0">
                      {fault.device_type && (
                        <span className="text-[10px] px-1.5 py-0.5 rounded border border-industrial-primary/30 bg-industrial-primary/10 text-industrial-primary">
                          {fault.device_type}
                        </span>
                      )}
                      <span className={`text-[10px] px-1.5 py-0.5 rounded border ${severityConfig[fault.severity].color}`}>
                        {severityConfig[fault.severity].label}
                      </span>
                      <button
                        onClick={() => handleDeleteFault(fault.id)}
                        className="opacity-0 group-hover:opacity-100 text-industrial-text-muted hover:text-industrial-danger transition-all"
                        title="删除该故障记录"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  </div>
                  <div className="ml-5 space-y-1.5">
                    <div className="flex gap-2 text-xs">
                      <span className="text-industrial-text-muted shrink-0">可能原因：</span>
                      <span className="text-industrial-text-secondary">{fault.cause || '—'}</span>
                    </div>
                    <div className="flex gap-2 text-xs">
                      <span className="text-industrial-text-muted shrink-0">解决方案：</span>
                      <span className="text-industrial-text">{fault.solution || '—'}</span>
                    </div>
                    {(fault.recorder || fault.created_at) && (
                      <div className="flex gap-2 text-[10px] text-industrial-text-muted pt-1 border-t border-industrial-border/50">
                        {fault.recorder && <span>记录人：{fault.recorder}</span>}
                        {fault.created_at && <span>· {new Date(fault.created_at).toLocaleString('zh-CN')}</span>}
                      </div>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* 新增故障弹窗 */}
      {showFaultModal && (
        <AddFaultModal
          deviceTypes={deviceTypes.map(d => d.type)}
          defaultDeviceType={selectedDeviceType !== 'all' ? selectedDeviceType : ''}
          defaultCategory={selectedCategory !== 'all' ? selectedCategory : ''}
          submitting={submitting}
          onClose={() => setShowFaultModal(false)}
          onSubmit={handleCreateFault}
        />
      )}
    </div>
  )
}


// ============================================================
// 新增故障弹窗组件
// ============================================================

interface AddFaultModalProps {
  deviceTypes: string[]
  defaultDeviceType?: string
  defaultCategory?: string
  submitting: boolean
  onClose: () => void
  onSubmit: (payload: Record<string, unknown>) => void
}

function AddFaultModal({ deviceTypes, defaultDeviceType, defaultCategory, submitting, onClose, onSubmit }: AddFaultModalProps) {
  const [symptom, setSymptom] = useState('')
  const [category, setCategory] = useState(defaultCategory || '')
  const [deviceType, setDeviceType] = useState(defaultDeviceType || '')
  const [cause, setCause] = useState('')
  const [solution, setSolution] = useState('')
  const [severity, setSeverity] = useState<'high' | 'medium' | 'low'>('medium')

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!symptom.trim() || !category.trim()) return
    onSubmit({
      symptom: symptom.trim(),
      category: category.trim(),
      device_type: deviceType || null,
      cause: cause.trim() || null,
      solution: solution.trim() || null,
      severity,
    })
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4"
      onClick={onClose}
    >
      <div
        className="glass-card rounded-2xl w-full max-w-lg p-6 max-h-[90vh] overflow-auto"
        onClick={(e) => e.stopPropagation()}
      >
        {/* 头部 */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-industrial-primary/15">
              <Plus className="h-4 w-4 text-industrial-primary" />
            </div>
            <h3 className="text-base font-semibold text-industrial-text">新增故障记录</h3>
          </div>
          <button
            onClick={onClose}
            className="text-industrial-text-muted hover:text-industrial-text transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <p className="text-xs text-industrial-text-muted mb-4">
          记录日常遇到的常见故障，积累后供新人参考排查。带 <span className="text-industrial-accent">*</span> 为必填。
        </p>

        <form onSubmit={handleSubmit} className="space-y-3">
          {/* 故障现象 */}
          <div>
            <label className="block text-xs font-medium text-industrial-text-secondary mb-1">
              故障现象 <span className="text-industrial-accent">*</span>
            </label>
            <input
              type="text"
              value={symptom}
              onChange={(e) => setSymptom(e.target.value)}
              placeholder="例如：焊接过程中频繁断弧"
              required
              className="w-full px-3 py-2 rounded-lg bg-industrial-bg border border-industrial-border text-sm text-industrial-text placeholder:text-industrial-text-muted focus:border-industrial-primary/50 focus:outline-none"
            />
          </div>

          {/* 故障类别 + 设备类型 */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-industrial-text-secondary mb-1">
                故障类别 <span className="text-industrial-accent">*</span>
              </label>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                required
                className="w-full px-3 py-2 rounded-lg bg-industrial-bg border border-industrial-border text-sm text-industrial-text focus:border-industrial-primary/50 focus:outline-none"
              >
                <option value="">请选择</option>
                {faultCategories.map(c => (
                  <option key={c.id} value={c.name}>{c.name}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-industrial-text-secondary mb-1">
                设备/传感器类型（可选）
              </label>
              <select
                value={deviceType}
                onChange={(e) => setDeviceType(e.target.value)}
                className="w-full px-3 py-2 rounded-lg bg-industrial-bg border border-industrial-border text-sm text-industrial-text focus:border-industrial-primary/50 focus:outline-none"
              >
                <option value="">不指定</option>
                {deviceTypes.map(t => (
                  <option key={t} value={t}>{t}</option>
                ))}
              </select>
            </div>
          </div>

          {/* 可能原因 */}
          <div>
            <label className="block text-xs font-medium text-industrial-text-secondary mb-1">
              可能原因（可选）
            </label>
            <textarea
              value={cause}
              onChange={(e) => setCause(e.target.value)}
              placeholder="例如：电流设置过低 / 钨极氧化 / 接地不良"
              rows={2}
              className="w-full px-3 py-2 rounded-lg bg-industrial-bg border border-industrial-border text-sm text-industrial-text placeholder:text-industrial-text-muted focus:border-industrial-primary/50 focus:outline-none resize-none"
            />
          </div>

          {/* 解决方案 */}
          <div>
            <label className="block text-xs font-medium text-industrial-text-secondary mb-1">
              解决方案（可选）
            </label>
            <textarea
              value={solution}
              onChange={(e) => setSolution(e.target.value)}
              placeholder="例如：检查电流设置、清理钨极、确认工件接地良好"
              rows={2}
              className="w-full px-3 py-2 rounded-lg bg-industrial-bg border border-industrial-border text-sm text-industrial-text placeholder:text-industrial-text-muted focus:border-industrial-primary/50 focus:outline-none resize-none"
            />
          </div>

          {/* 严重程度 */}
          <div>
            <label className="block text-xs font-medium text-industrial-text-secondary mb-1">
              严重程度
            </label>
            <div className="flex gap-2">
              {(['high', 'medium', 'low'] as const).map(level => (
                <button
                  key={level}
                  type="button"
                  onClick={() => setSeverity(level)}
                  className={`flex-1 px-3 py-1.5 rounded-md text-xs border transition-all ${
                    severity === level
                      ? severityConfig[level].color + ' font-medium'
                      : 'bg-industrial-bg border-industrial-border text-industrial-text-muted hover:text-industrial-text'
                  }`}
                >
                  {severityConfig[level].label}
                </button>
              ))}
            </div>
          </div>

          {/* 操作按钮 */}
          <div className="flex gap-2 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 rounded-lg bg-industrial-card border border-industrial-border text-sm text-industrial-text-secondary hover:bg-industrial-card-hover transition-colors"
            >
              取消
            </button>
            <button
              type="submit"
              disabled={submitting || !symptom.trim() || !category.trim()}
              className="flex-1 flex items-center justify-center gap-1.5 px-4 py-2 rounded-lg bg-industrial-primary text-sm font-medium text-white hover:bg-industrial-primary-hover disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              {submitting ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  提交中...
                </>
              ) : (
                <>
                  <Plus className="h-4 w-4" />
                  保存到故障库
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}