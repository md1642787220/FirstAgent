import { useState, useEffect } from 'react'
import { ClipboardList, TrendingUp, Clock, AlertCircle, Lightbulb } from 'lucide-react'
import api from '../services/http'

interface WorkOrder {
  id: string
  product_name: string
  quantity: number
  priority: 'high' | 'medium' | 'low'
  status: 'pending' | 'in_progress' | 'completed' | 'delayed'
  progress: number
  delay_days: number
  start_date: string
  end_date: string
}

interface ProductionSummary {
  total_orders: number
  in_progress: number
  completed: number
  delayed: number
}

export default function ProductionPage() {
  const [orders, setOrders] = useState<WorkOrder[]>([])
  const [summary, setSummary] = useState<ProductionSummary>({ total_orders: 0, in_progress: 0, completed: 0, delayed: 0 })
  const [loading, setLoading] = useState(true)
  const [statusFilter, setStatusFilter] = useState<string>('all')

  useEffect(() => {
    loadData()
  }, [])

  async function loadData() {
    try {
      setLoading(true)
      const [ordersData, summaryData] = await Promise.all([
        api.get<any[]>('/production/orders'),
        api.get<any>('/production/summary'),
      ])
      setOrders(ordersData as WorkOrder[])
      setSummary(summaryData as ProductionSummary)
    } catch (err) {
      console.error('[Production] Load error:', err)
    } finally {
      setLoading(false)
    }
  }

  const filteredOrders = statusFilter === 'all' ? orders : orders.filter(o => o.status === statusFilter)

  const statusConfig = {
    pending: { label: '待开始', color: 'bg-gray-500/15 text-gray-400 border-gray-500/30' },
    in_progress: { label: '进行中', color: 'bg-blue-500/15 text-blue-400 border-blue-500/30' },
    completed: { label: '已完成', color: 'bg-green-500/15 text-green-400 border-green-500/30' },
    delayed: { label: '已滞后', color: 'bg-orange-500/15 text-orange-400 border-orange-500/30' },
  }

  const priorityConfig = {
    high: { label: '高', color: 'text-red-400' },
    medium: { label: '中', color: 'text-yellow-400' },
    low: { label: '低', color: 'text-gray-400' },
  }

  return (
    <div className="flex h-full flex-col gap-4">
      {/* 标题栏 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-cyan-500/20 to-blue-600/20 border border-cyan-500/30">
            <ClipboardList className="h-5 w-5 text-cyan-400" />
          </div>
          <div>
            <h1 className="text-lg font-semibold text-industrial-text">生产进度看板</h1>
            <p className="text-xs text-industrial-text-muted">实时跟踪工单执行状态与进度</p>
          </div>
        </div>
        <button onClick={loadData} className="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs text-industrial-text-secondary bg-industrial-card border border-industrial-border hover:border-industrial-primary/50 transition-colors">
          刷新数据
        </button>
      </div>

      {/* 统计卡片 */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard title="工单总数" value={summary.total_orders} icon={<ClipboardList className="h-5 w-5" />} color="blue" />
        <StatCard title="进行中" value={summary.in_progress} icon={<TrendingUp className="h-5 w-5" />} color="cyan" glow={summary.delayed > 0} />
        <StatCard title="已完成" value={summary.completed} icon={<Clock className="h-5 w-5" />} color="green" />
        <StatCard title="滞后数" value={summary.delayed} icon={<AlertCircle className="h-5 w-5" />} color="orange" alert={summary.delayed > 0} />
      </div>

      {/* 工单列表 */}
      <div className="flex-1 glass-card rounded-xl overflow-hidden flex flex-col">
        <div className="flex items-center justify-between px-4 py-3 border-b border-industrial-border">
          <span className="text-sm font-medium text-industrial-text">工单列表</span>
          <div className="flex gap-1.5">
            {['all', 'in_progress', 'completed', 'delayed'].map(status => (
              <button
                key={status}
                onClick={() => setStatusFilter(status)}
                className={`rounded-md px-2.5 py-1 text-xs transition-colors ${
                  statusFilter === status
                    ? 'bg-industrial-primary/15 text-industrial-primary'
                    : 'text-industrial-text-muted hover:text-industrial-text-secondary'
                }`}
              >
                {status === 'all' ? '全部' : statusConfig[status as keyof typeof statusConfig]?.label || status}
              </button>
            ))}
          </div>
        </div>

        <div className="flex-1 overflow-auto">
          {loading ? (
            <div className="flex items-center justify-center h-40 text-industrial-text-muted text-sm">加载中...</div>
          ) : filteredOrders.length === 0 ? (
            <div className="flex items-center justify-center h-40 text-industrial-text-muted text-sm">暂无数据</div>
          ) : (
            <table className="w-full text-sm">
              <thead className="sticky top-0 bg-industrial-sidebar">
                <tr className="text-left text-xs text-industrial-text-muted">
                  <th className="px-4 py-3 font-medium">工单号</th>
                  <th className="px-4 py-3 font-medium">产品名称</th>
                  <th className="px-4 py-3 font-medium">数量</th>
                  <th className="px-4 py-3 font-medium">优先级</th>
                  <th className="px-4 py-3 font-medium">进度</th>
                  <th className="px-4 py-3 font-medium">状态</th>
                  <th className="px-4 py-3 font-medium">延迟天数</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-industrial-border/50">
                {filteredOrders.map(order => (
                  <tr key={order.id} className="hover:bg-industrial-card-hover/30 transition-colors">
                    <td className="px-4 py-3 font-mono text-xs text-industrial-primary">{order.id}</td>
                    <td className="px-4 py-3 text-industrial-text">{order.product_name}</td>
                    <td className="px-4 py-3 text-industrial-text-secondary tabular-nums">{order.quantity}</td>
                    <td className="px-4 py-3">
                      <span className={priorityConfig[order.priority]?.color || ''}>{priorityConfig[order.priority]?.label}</span>
                    </td>
                    <td className="px-4 py-3 w-36">
                      <ProgressBar value={order.progress} />
                    </td>
                    <td className="px-4 py-3">
                      <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-[11px] border ${statusConfig[order.status]?.color}`}>
                        {statusConfig[order.status]?.label}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      {order.delay_days > 0 ? (
                        <span className="text-industrial-accent font-medium tabular-nums">+{order.delay_days}天</span>
                      ) : (
                        <span className="text-industrial-text-muted tabular-nums">-</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* AI 洞察卡片 */}
      <div className="glass-card rounded-xl p-4 border-l-2 border-l-industrial-accent/50">
        <div className="flex items-start gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-industrial-accent/15 shrink-0">
            <Lightbulb className="h-4 w-4 text-industrial-accent" />
          </div>
          <div>
            <p className="text-xs font-medium text-industrial-accent mb-1">AI 智能洞察</p>
            <p className="text-xs text-industrial-text-secondary leading-relaxed">
              {summary.delayed > 0
                ? `当前有 ${summary.delayed} 个工单存在滞后风险，建议优先调配资源处理高优先级订单。`
                : summary.in_progress > 0
                ? `当前 ${summary.in_progress} 个工单正在按计划推进，整体生产节奏良好。`
                : '暂无进行中的工单，可安排新的生产计划。'}
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

function StatCard({ title, value, icon, color, glow, alert }: { title: string; value: number; icon: React.ReactNode; color: string; glow?: boolean; alert?: boolean }) {
  const colorMap: Record<string, { bg: string; text: string; border: string }> = {
    blue: { bg: 'bg-blue-500/10', text: 'text-blue-400', border: 'border-blue-500/20' },
    cyan: { bg: 'bg-cyan-500/10', text: 'text-cyan-400', border: 'border-cyan-500/20' },
    green: { bg: 'bg-green-500/10', text: 'text-green-400', border: 'border-green-500/20' },
    orange: { bg: 'bg-orange-500/10', text: 'text-orange-400', border: 'border-orange-500/20' },
  }
  const c = colorMap[color] || colorMap.blue

  return (
    <div className={`glass-card rounded-xl p-4 ${glow ? 'glow-border-accent' : 'glow-border'} ${alert ? 'animate-pulse-slow' : ''}`}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs text-industrial-text-muted">{title}</span>
        <div className={`flex h-7 w-7 items-center justify-center rounded-md ${c.bg} ${c.text}`}>{icon}</div>
      </div>
      <p className={`text-2xl font-bold tabular-nums ${c.text}`}>{value}</p>
    </div>
  )
}

function ProgressBar({ value }: { value: number }) {
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 rounded-full bg-industrial-bg overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-500"
          style={{ width: `${value}%`, background: value >= 80 ? '#10B981' : value >= 40 ? '#F59E0B' : '#EF4444' }}
        />
      </div>
      <span className="text-xs text-industrial-text-muted tabular-nums w-8 text-right">{value}%</span>
    </div>
  )
}
