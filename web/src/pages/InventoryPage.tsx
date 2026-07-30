import { useState, useEffect } from 'react'
import { Warehouse, Package, AlertTriangle, Clock, ShoppingCart, TrendingDown, Lightbulb } from 'lucide-react'
import api from '../services/http'

interface InventoryItem {
  material_code: string
  material_name: string
  quantity: number
  safety_stock: number
  status: 'normal' | 'low' | 'overstock'
  turnover_days: number
  unit: string
}

interface InventoryAlert {
  material_code: string
  material_name: string
  current_qty: number
  safety_stock: number
  shortage: number
}

interface InventorySummary {
  total_items: number
  normal_count: number
  shortage_count: number
  obsolete_count: number
}

type TabType = 'alerts' | 'obsolete'

export default function InventoryPage() {
  const [inventory, setInventory] = useState<InventoryItem[]>([])
  const [alerts, setAlerts] = useState<InventoryAlert[]>([])
  const [summary, setSummary] = useState<InventorySummary>({ total_items: 0, normal_count: 0, shortage_count: 0, obsolete_count: 0 })
  const [activeTab, setActiveTab] = useState<TabType>('alerts')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadData()
  }, [])

  async function loadData() {
    try {
      setLoading(true)
      const [invData, alertsData, summaryData] = await Promise.all([
        api.get<any[]>('/inventory'),
        api.get<any[]>('/inventory/alerts'),
        api.get<any>('/inventory/summary'),
      ])
      setInventory(invData as InventoryItem[])
      setAlerts(alertsData as InventoryAlert[])
      setSummary(summaryData as InventorySummary)
    } catch (err) {
      console.error('[Inventory] Load error:', err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex h-full flex-col gap-4">
      {/* 标题栏 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-emerald-500/20 to-teal-600/20 border border-emerald-500/30">
            <Warehouse className="h-5 w-5 text-emerald-400" />
          </div>
          <div>
            <h1 className="text-lg font-semibold text-industrial-text">库存分析看板</h1>
            <p className="text-xs text-industrial-text-muted">库存监控、短缺预警与采购建议</p>
          </div>
        </div>
        <button onClick={loadData} className="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs text-industrial-text-secondary bg-industrial-card border border-industrial-border hover:border-industrial-primary/50 transition-colors">
          刷新数据
        </button>
      </div>

      {/* 统计卡片 */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <InvStatCard title="物料总数" value={summary.total_items} icon={<Package className="h-5 w-5" />} color="blue" />
        <InvStatCard title="正常库存" value={summary.normal_count} icon={<Package className="h-5 w-5" />} color="green" />
        <InvStatCard title="短缺预警" value={summary.shortage_count} icon={<AlertTriangle className="h-5 w-5" />} color="orange" alert={summary.shortage_count > 0} />
        <InvStatCard title="呆滞物料" value={summary.obsolete_count} icon={<TrendingDown className="h-5 w-5" />} color="red" alert={summary.obsolete_count > 0} />
      </div>

      {/* 预警表格 */}
      <div className="flex-1 glass-card rounded-xl overflow-hidden flex flex-col min-h-0">
        <div className="flex items-center gap-4 px-4 py-3 border-b border-industrial-border">
          <span className="text-sm font-medium text-industrial-text">库存预警</span>
          <div className="flex gap-1">
            <button
              onClick={() => setActiveTab('alerts')}
              className={`rounded-md px-3 py-1 text-xs transition-colors ${
                activeTab === 'alerts' ? 'bg-orange-500/15 text-orange-400' : 'text-industrial-text-muted hover:text-industrial-text-secondary'
              }`}
            >
              短缺预警 ({alerts.length})
            </button>
            <button
              onClick={() => setActiveTab('obsolete')}
              className={`rounded-md px-3 py-1 text-xs transition-colors ${
                activeTab === 'obsolete' ? 'bg-red-500/15 text-red-400' : 'text-industrial-text-muted hover:text-industrial-text-secondary'
              }`}
            >
              呆滞物料
            </button>
          </div>
        </div>

        <div className="flex-1 overflow-auto">
          {loading ? (
            <div className="flex items-center justify-center h-40 text-industrial-text-muted text-sm">加载中...</div>
          ) : activeTab === 'alerts' && alerts.length === 0 ? (
            <div className="flex items-center justify-center h-40 text-industrial-text-muted text-sm">暂无短缺预警</div>
          ) : activeTab === 'alerts' ? (
            <table className="w-full text-sm">
              <thead className="sticky top-0 bg-industrial-sidebar">
                <tr className="text-left text-xs text-industrial-text-muted">
                  <th className="px-4 py-3 font-medium">物料编码</th>
                  <th className="px-4 py-3 font-medium">名称</th>
                  <th className="px-4 py-3 font-medium">当前库存</th>
                  <th className="px-4 py-3 font-medium">安全库存</th>
                  <th className="px-4 py-3 font-medium">缺口数量</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-industrial-border/50">
                {alerts.map(alert => (
                  <tr key={alert.material_code} className="hover:bg-industrial-card-hover/30 transition-colors">
                    <td className="px-4 py-2.5 font-mono text-xs text-industrial-primary">{alert.material_code}</td>
                    <td className="px-4 py-2.5 text-industrial-text">{alert.material_name}</td>
                    <td className="px-4 py-2.5 text-industrial-accent font-medium tabular-nums">{alert.current_qty}</td>
                    <td className="px-4 py-2.5 text-industrial-text-secondary tabular-nums">{alert.safety_stock}</td>
                    <td className="px-4 py-2.5 text-industrial-danger font-medium tabular-nums">-{alert.shortage}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            /* 呆滞物料表格 */
            <table className="w-full text-sm">
              <thead className="sticky top-0 bg-industrial-sidebar">
                <tr className="text-left text-xs text-industrial-text-muted">
                  <th className="px-4 py-3 font-medium">物料编码</th>
                  <th className="px-4 py-3 font-medium">名称</th>
                  <th className="px-4 py-3 font-medium">库存数量</th>
                  <th className="px-4 py-3 font-medium">周转天数</th>
                  <th className="px-4 py-3 font-medium">状态</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-industrial-border/50">
                {inventory.filter(i => i.turnover_days > 90).map(item => (
                  <tr key={item.material_code} className="hover:bg-industrial-card-hover/30 transition-colors">
                    <td className="px-4 py-2.5 font-mono text-xs text-industrial-primary">{item.material_code}</td>
                    <td className="px-4 py-2.5 text-industrial-text">{item.material_name}</td>
                    <td className="px-4 py-2.5 text-industrial-text-secondary tabular-nums">{item.quantity} {item.unit}</td>
                    <td className="px-4 py-2.5 text-industrial-danger font-medium tabular-nums">{item.turnover_days} 天</td>
                    <td className="px-4 py-2.5">
                      <span className="inline-flex items-center rounded-full px-2 py-0.5 text-[11px] bg-red-500/15 text-red-400 border border-red-500/30">
                        呆滞
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* AI 采购建议 */}
      {alerts.length > 0 && (
        <div className="glass-card rounded-xl p-4 border-l-2 border-l-industrial-primary/50">
          <div className="flex items-start gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-industrial-primary/15 shrink-0">
              <ShoppingCart className="h-4 w-4 text-industrial-primary" />
            </div>
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-1">
                <Lightbulb className="h-3.5 w-3.5 text-industrial-primary" />
                <p className="text-xs font-medium text-industrial-primary">AI 采购建议</p>
              </div>
              <div className="flex flex-wrap gap-2">
                {alerts.slice(0, 5).map(alert => (
                  <span key={alert.material_code} className="inline-flex items-center gap-1.5 rounded-md bg-industrial-bg px-2.5 py-1 text-xs text-industrial-text-secondary">
                    <span>{alert.material_name}</span>
                    <span className="text-industrial-accent">补货 {alert.shortage}</span>
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function InvStatCard({ title, value, icon, color, alert }: { title: string; value: number; icon: React.ReactNode; color: string; alert?: boolean }) {
  const colorMap: Record<string, { bg: string; text: string }> = {
    blue: { bg: 'bg-blue-500/10', text: 'text-blue-400' },
    green: { bg: 'bg-green-500/10', text: 'text-green-400' },
    orange: { bg: 'bg-orange-500/10', text: 'text-orange-400' },
    red: { bg: 'bg-red-500/10', text: 'text-red-400' },
  }
  const c = colorMap[color] || colorMap.blue

  return (
    <div className={`glass-card rounded-xl p-4 ${alert ? 'animate-pulse-slow' : ''}`}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs text-industrial-text-muted">{title}</span>
        <div className={`flex h-7 w-7 items-center justify-center rounded-md ${c.bg} ${c.text}`}>{icon}</div>
      </div>
      <p className={`text-2xl font-bold tabular-nums ${c.text}`}>{value}</p>
    </div>
  )
}
