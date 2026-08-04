import { useState, useEffect, useRef } from 'react'
import { Activity, AlertTriangle, Thermometer, Gauge, Wind, Zap, Droplets, ChevronRight, ChevronDown, Power, PowerOff, RefreshCw } from 'lucide-react'
import wsService from '../services/websocket'
import api from '../services/http'
import type { AppState } from '../App'

interface Props {
  updateAppState: (updates: Partial<AppState>) => void
}

interface DeviceMetric {
  device_id: string
  name: string
  type: string
  status: 'online' | 'offline'
  parent_id: string | null
  metrics: Record<string, number>
  updated_at: string
}

interface MetricConfig {
  key: string
  label: string
  unit: string
  icon: React.ReactNode
  min: number
  max: number
  normalMin: number
  normalMax: number
  color: string
}

const METRIC_CONFIGS: MetricConfig[] = [
  { key: 'current', label: '焊接电流', unit: 'A', icon: <Zap className="h-4 w-4" />, min: 0, max: 350, normalMin: 100, normalMax: 300, color: '#3B82F6' },
  { key: 'voltage', label: '焊接电压', unit: 'V', icon: <Gauge className="h-4 w-4" />, min: 0, max: 45, normalMin: 20, normalMax: 35, color: '#10B981' },
  { key: 'speed', label: '焊接速度', unit: 'mm/min', icon: <Activity className="h-4 w-4" />, min: 200, max: 900, normalMin: 300, normalMax: 800, color: '#F59E0B' },
  { key: 'wire_speed', label: '送丝速度', unit: 'm/min', icon: <Wind className="h-4 w-4" />, min: 0, max: 18, normalMin: 3, normalMax: 15, color: '#06B6D4' },
  { key: 'gas_flow', label: '气体流量', unit: 'L/min', icon: <Droplets className="h-4 w-4" />, min: 0, max: 30, normalMin: 15, normalMax: 25, color: '#8B5CF6' },
  { key: 'temperature', label: '设备温度', unit: '℃', icon: <Thermometer className="h-4 w-4" />, min: 0, max: 100, normalMin: 0, normalMax: 75, color: '#EF4444' },
]

export default function DevicePage({ updateAppState }: Props) {
  const [devices, setDevices] = useState<DeviceMetric[]>([])
  const [selectedDevice, setSelectedDevice] = useState<string | null>(null)
  const [metricsHistory, setMetricsHistory] = useState<Record<string, Array<{ time: number; value: number }>>>({})
  const [wsConnected, setWsConnected] = useState(false)
  const [collapsedGroups, setCollapsedGroups] = useState<Set<string>>(new Set())
  const [refreshing, setRefreshing] = useState(false)

  // 解析设备列表数据
  const parseDevices = (raw: any): DeviceMetric[] => {
    const rawDevices = raw.devices || raw
    return (rawDevices as any[]).map(d => ({
      device_id: d.id || d.device_id,
      name: d.name || `设备-${d.id}`,
      type: d.type || '未知',
      status: d.status === 'online' ? 'online' : 'offline',
      parent_id: d.parent_id ?? null,
      metrics: d.metrics || {},
      updated_at: d.updated_at || new Date().toISOString(),
    }))
  }

  // 加载设备列表
  useEffect(() => {
    api.get<{ devices: any[] }>('/devices').then(data => {
      const deviceList = parseDevices(data)
      setDevices(deviceList)
      // 默认选中第一个在线的顶级设备
      const firstOnline = deviceList.find(d => d.status === 'online' && d.parent_id === null) || deviceList[0]
      if (firstOnline && !selectedDevice) {
        setSelectedDevice(firstOnline.device_id)
      }
      updateAppState({ deviceOnline: deviceList.filter(d => d.status === 'online').length })
    }).catch(console.error)
  }, [])

  // 刷新设备状态
  const handleRefresh = async () => {
    if (refreshing) return
    setRefreshing(true)
    try {
      const data = await api.post<{ devices: any[] }>('/devices/refresh', {})
      const deviceList = parseDevices(data)
      setDevices(deviceList)
      updateAppState({ deviceOnline: deviceList.filter(d => d.status === 'online').length })
    } catch (e) {
      console.error(e)
    } finally {
      setRefreshing(false)
    }
  }

  // WebSocket 实时数据
  useEffect(() => {
    const unsubConn = wsService.onConnectionChange(setWsConnected)

    const unsubMsg = wsService.onMessage((data) => {
      if (data.type === 'metrics:update' && data.device_id) {
        setDevices(prev => prev.map(d =>
          d.device_id === data.device_id
            ? {
                ...d,
                status: data.status === 'offline' ? 'offline' : 'online',
                metrics: data.metrics ? { ...d.metrics, ...data.metrics } : {},
                updated_at: data.updated_at || new Date().toISOString(),
              }
            : d
        ))

        // 更新历史数据（保留最近60个点）—— 仅在线设备
        if (data.metrics) {
          setMetricsHistory(prev => {
            const next = { ...prev }
            Object.entries(data.metrics).forEach(([key, value]) => {
              const historyKey = `${data.device_id}_${key}`
              const prevHistory = next[historyKey] || []
              next[historyKey] = [...prevHistory.slice(-59), { time: Date.now(), value: Number(value) }]
            })
            return next
          })
        }
      }
    })

    wsService.connect('/ws/realtime')

    return () => {
      unsubConn()
      unsubMsg()
      wsService.disconnect()
    }
  }, [])

  // 分组：顶级设备 + 子设备
  const topDevices = devices.filter(d => d.parent_id === null)
  const childrenOf = (parentId: string) => devices.filter(d => d.parent_id === parentId)

  const toggleGroup = (id: string) => {
    setCollapsedGroups(prev => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const currentDevice = devices.find(d => d.device_id === selectedDevice)
  const onlineCount = devices.filter(d => d.status === 'online').length
  const offlineCount = devices.length - onlineCount

  return (
    <div className="flex h-full flex-col gap-4">
      {/* 标题栏 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-green-500/20 to-emerald-600/20 border border-green-500/30">
            <Activity className="h-5 w-5 text-green-400" />
          </div>
          <div>
            <h1 className="text-lg font-semibold text-industrial-text">设备实时监控</h1>
            <p className="text-xs text-industrial-text-muted">WebSocket 实时推送 · 每 2 秒刷新</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {/* 在线/离线统计 */}
          <div className="flex items-center gap-2 text-xs">
            <span className="flex items-center gap-1 rounded-full bg-green-500/10 px-2.5 py-1 text-green-400">
              <Power className="h-3 w-3" /> 在线 {onlineCount}
            </span>
            <span className="flex items-center gap-1 rounded-full bg-gray-500/10 px-2.5 py-1 text-gray-400">
              <PowerOff className="h-3 w-3" /> 离线 {offlineCount}
            </span>
          </div>

          {/* 连接状态 */}
          <div className={`flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs ${
            wsConnected ? 'bg-green-500/10 text-green-400' : 'bg-red-500/10 text-red-400'
          }`}>
            <span className={`h-1.5 w-1.5 rounded-full ${wsConnected ? 'bg-green-400 animate-pulse' : 'bg-red-400'}`} />
            {wsConnected ? '实时连接中' : '已断开'}
          </div>

          <div className="h-4 w-px bg-industrial-border"></div>

          {/* 刷新设备状态 */}
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="flex items-center gap-1.5 rounded-lg border border-industrial-border bg-industrial-bg/40 px-3 py-1.5 text-xs text-industrial-text-secondary transition-colors hover:bg-industrial-card-hover hover:text-industrial-primary disabled:opacity-50 disabled:cursor-not-allowed"
            title="刷新设备状态"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${refreshing ? 'animate-spin' : ''}`} />
            刷新设备状态
          </button>
        </div>
      </div>

      <div className="flex flex-1 gap-4 min-h-0">
        {/* 左侧：设备树 */}
        <div className="w-64 flex-shrink-0 glass-card rounded-xl p-3 overflow-y-auto">
          <div className="text-xs font-medium text-industrial-text-secondary mb-2 px-2">设备列表</div>
          <div className="space-y-1">
            {topDevices.map(dev => {
              const children = childrenOf(dev.device_id)
              const hasChildren = children.length > 0
              const collapsed = collapsedGroups.has(dev.device_id)
              const isSelected = selectedDevice === dev.device_id

              return (
                <div key={dev.device_id}>
                  {/* 顶级设备 */}
                  <button
                    onClick={() => hasChildren ? toggleGroup(dev.device_id) : setSelectedDevice(dev.device_id)}
                    className={`w-full flex items-center gap-2 rounded-lg px-2 py-2 text-left transition-colors ${
                      isSelected ? 'bg-industrial-primary/20 text-industrial-primary' : 'hover:bg-industrial-bg/50 text-industrial-text'
                    }`}
                  >
                    {hasChildren ? (
                      collapsed ? <ChevronRight className="h-3.5 w-3.5 flex-shrink-0" /> : <ChevronDown className="h-3.5 w-3.5 flex-shrink-0" />
                    ) : (
                      <span className="w-3.5 flex-shrink-0" />
                    )}
                    <StatusDot status={dev.status} />
                    <div className="flex-1 min-w-0">
                      <div className="text-sm truncate">{dev.name}</div>
                      <div className="text-[10px] text-industrial-text-muted truncate">{dev.type}</div>
                    </div>
                  </button>

                  {/* 子设备列表 */}
                  {hasChildren && !collapsed && (
                    <div className="ml-5 mt-0.5 space-y-1 border-l border-industrial-border/50 pl-2">
                      {children.map(child => {
                        const childSelected = selectedDevice === child.device_id
                        return (
                          <button
                            key={child.device_id}
                            onClick={() => setSelectedDevice(child.device_id)}
                            className={`w-full flex items-center gap-2 rounded-lg px-2 py-1.5 text-left transition-colors ${
                              childSelected ? 'bg-industrial-primary/20 text-industrial-primary' : 'hover:bg-industrial-bg/50 text-industrial-text'
                            }`}
                          >
                            <StatusDot status={child.status} />
                            <div className="flex-1 min-w-0">
                              <div className="text-xs truncate">{child.name}</div>
                              <div className="text-[10px] text-industrial-text-muted truncate">{child.type}</div>
                            </div>
                          </button>
                        )
                      })}
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </div>

        {/* 右侧：设备详情 */}
        <div className="flex-1 min-w-0 flex flex-col gap-4 overflow-y-auto">
          {currentDevice ? (
            <>
              {/* 设备头部信息 */}
              <div className="glass-card rounded-xl p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="text-base font-semibold text-industrial-text">{currentDevice.name}</h2>
                    <p className="text-xs text-industrial-text-muted mt-0.5">
                      ID: {currentDevice.device_id} · 类型: {currentDevice.type}
                    </p>
                  </div>
                  <StatusBadge status={currentDevice.status} />
                </div>
              </div>

              {/* 离线提示 */}
              {currentDevice.status === 'offline' ? (
                <div className="glass-card rounded-xl p-8 flex flex-col items-center justify-center text-center">
                  <PowerOff className="h-10 w-10 text-gray-500 mb-3" />
                  <div className="text-sm text-industrial-text-secondary">设备离线</div>
                  <div className="text-xs text-industrial-text-muted mt-1">该设备当前未连接，无实时数据</div>
                </div>
              ) : (
                <>
                  {/* 参数卡片网格 */}
                  <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
                    {METRIC_CONFIGS.map(config => {
                      const value = currentDevice.metrics[config.key] ?? '--'
                      const numValue = typeof value === 'number' ? value : null
                      const isAbnormal = numValue !== null && (numValue < config.normalMin || numValue > config.normalMax)
                      const percentage = numValue !== null ? ((numValue - config.min) / (config.max - config.min)) * 100 : 0

                      return (
                        <div key={config.key} className={`glass-card rounded-xl p-4 transition-all duration-300 ${isAbnormal ? 'glow-border-accent' : 'glow-border'}`}>
                          <div className="flex items-start justify-between mb-3">
                            <div className="flex items-center gap-2">
                              <div className="flex h-7 w-7 items-center justify-center rounded-md" style={{ backgroundColor: `${config.color}15`, color: config.color }}>
                                {config.icon}
                              </div>
                              <span className="text-xs text-industrial-text-secondary">{config.label}</span>
                            </div>
                            {isAbnormal && <AlertTriangle className="h-4 w-4 text-industrial-accent" />}
                          </div>

                          <div className="flex items-baseline gap-1.5 mb-3">
                            <span className={`text-2xl font-bold tabular-nums ${isAbnormal ? 'text-industrial-accent' : 'text-industrial-text'}`}>
                              {typeof value === 'number' ? value.toFixed(1) : value}
                            </span>
                            <span className="text-xs text-industrial-text-muted">{config.unit}</span>
                          </div>

                          {/* 范围指示条 */}
                          <div className="relative h-1.5 rounded-full bg-industrial-bg overflow-hidden">
                            <div
                              className="absolute left-0 top-0 h-full rounded-full transition-all duration-300"
                              style={{
                                width: `${Math.min(100, Math.max(0, percentage))}%`,
                                background: isAbnormal
                                  ? 'linear-gradient(90deg, #FA8C16, #EF4444)'
                                  : `linear-gradient(90deg, ${config.color}80, ${config.color})`,
                              }}
                            />
                            <div
                              className="absolute top-[-2px] h-[10px] w-0.5 bg-industrial-success/50"
                              style={{ left: `${((config.normalMin - config.min) / (config.max - config.min)) * 100}%` }}
                            />
                            <div
                              className="absolute top-[-2px] h-[10px] w-0.5 bg-industrial-success/50"
                              style={{ left: `${((config.normalMax - config.min) / (config.max - config.min)) * 100}%` }}
                            />
                          </div>

                          <div className="flex justify-between mt-1.5 text-[10px] text-industrial-text-muted">
                            <span>{config.min}{config.unit}</span>
                            <span className="text-industrial-success">正常: {config.normalMin}-{config.normalMax}</span>
                            <span>{config.max}{config.unit}</span>
                          </div>
                        </div>
                      )
                    })}
                  </div>

                  {/* 实时曲线图区域 */}
                  <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4">
                    {METRIC_CONFIGS.slice(0, 6).map(config => {
                      const historyKey = `${selectedDevice}_${config.key}`
                      const history = metricsHistory[historyKey] || []
                      return (
                        <div key={config.key} className="glass-card rounded-xl p-4">
                          <div className="flex items-center justify-between mb-3">
                            <span className="text-xs font-medium text-industrial-text-secondary">{config.label} 趋势</span>
                            <span className="text-[10px] text-industrial-text-muted">最近 60 秒</span>
                          </div>
                          <MiniChart data={history} color={config.color} minY={config.min} maxY={config.max} />
                        </div>
                      )
                    })}
                  </div>
                </>
              )}
            </>
          ) : (
            <div className="glass-card rounded-xl p-8 flex items-center justify-center text-sm text-industrial-text-muted">
              请从左侧选择设备查看详情
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

// 状态圆点
function StatusDot({ status }: { status: 'online' | 'offline' }) {
  return (
    <span className={`h-2 w-2 rounded-full flex-shrink-0 ${
      status === 'online' ? 'bg-green-400' : 'bg-gray-500'
    }`} />
  )
}

// 状态徽章
function StatusBadge({ status }: { status: 'online' | 'offline' }) {
  return status === 'online' ? (
    <span className="flex items-center gap-1.5 rounded-full bg-green-500/10 px-3 py-1 text-xs text-green-400 border border-green-500/30">
      <Power className="h-3 w-3" /> 在线
    </span>
  ) : (
    <span className="flex items-center gap-1.5 rounded-full bg-gray-500/10 px-3 py-1 text-xs text-gray-400 border border-gray-500/30">
      <PowerOff className="h-3 w-3" /> 离线
    </span>
  )
}

// 简单的 SVG 迷你图表
function MiniChart({ data, color, minY, maxY }: { data: Array<{ time: number; value: number }>; color: string; minY: number; maxY: number }) {
  if (data.length < 2) {
    return (
      <div className="flex items-center justify-center h-24 text-xs text-industrial-text-muted">
        等待数据...
      </div>
    )
  }

  const width = 280
  const height = 96
  const padding = 4

  const xStep = (width - padding * 2) / Math.max(1, data.length - 1)
  const yRange = maxY - minY

  const points = data.map((d, i) => ({
    x: padding + i * xStep,
    y: height - padding - ((d.value - minY) / yRange) * (height - padding * 2),
  }))

  const linePath = points.map((p, i) => `${i === 0 ? 'M' : 'L'}${p.x},${p.y}`).join(' ')
  const areaPath = `${linePath} L${points[points.length - 1].x},${height - padding} L${padding},${height - padding} Z`

  return (
    <svg width="100%" height={height} viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none">
      <defs>
        <linearGradient id={`grad-${color.replace('#', '')}`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.3" />
          <stop offset="100%" stopColor={color} stopOpacity="0" />
        </linearGradient>
      </defs>
      <path d={areaPath} fill={`url(#grad-${color.replace('#', '')})`} />
      <path d={linePath} fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
      {points.length > 0 && (
        <circle cx={points[points.length - 1].x} cy={points[points.length - 1].y} r="3" fill={color} opacity="0.9">
          <animate attributeName="r" values="3;5;3" dur="1.5s" repeatCount="indefinite" />
          <animate attributeName="opacity" values="0.9;0.4;0.9" dur="1.5s" repeatCount="indefinite" />
        </circle>
      )}
    </svg>
  )
}
