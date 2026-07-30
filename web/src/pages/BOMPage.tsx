import { useState, useEffect } from 'react'
import { PackageOpen, CheckCircle, XCircle, Search, ChevronRight } from 'lucide-react'
import api from '../services/http'

interface BOMItem {
  id: string
  material_code: string
  material_name: string
  quantity: number
  unit: string
  material_type: string
  cost: number
}

interface BOM {
  id: string
  product_code: string
  version: string
  status: string
  items: BOMItem[]
}

interface AvailabilityResult {
  material_code: string
  material_name: string
  required: number
  available: number
  shortage: number
  status: 'ok' | 'shortage'
}

export default function BOMPage() {
  const [boms, setBoms] = useState<BOM[]>([])
  const [selectedBomId, setSelectedBomId] = useState<string>('')
  const [selectedBom, setSelectedBom] = useState<BOM | null>(null)
  const [availability, setAvailability] = useState<AvailabilityResult[]>([])
  const [checkingAvailability, setCheckingAvailability] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadBOMs()
  }, [])

  async function loadBOMs() {
    try {
      setLoading(true)
      const data = await api.get<any[]>('/bom')
      setBoms(data as BOM[])
      if ((data as BOM[]).length > 0 && !selectedBomId) {
        setSelectedBomId((data as BOM[])[0].id)
        loadBOMDetail((data as BOM[])[0].id)
      }
    } catch (err) {
      console.error('[BOM] Load error:', err)
    } finally {
      setLoading(false)
    }
  }

  async function loadBOMDetail(id: string) {
    try {
      const data = await api.get<any>(`/bom/${id}`)
      setSelectedBom(data as BOM)
      setAvailability([])
    } catch (err) {
      console.error('[BOM] Detail error:', err)
    }
  }

  function handleSelectBom(id: string) {
    setSelectedBomId(id)
    loadBOMDetail(id)
  }

  async function checkAvailability() {
    if (!selectedBomId) return
    try {
      setCheckingAvailability(true)
      const data = await api.post<any[]>('/bom/availability', { bom_id: selectedBomId })
      setAvailability(data as AvailabilityResult[])
    } catch (err) {
      console.error('[BOM] Availability error:', err)
    } finally {
      setCheckingAvailability(false)
    }
  }

  const typeColors: Record<string, string> = {
    raw_material: 'bg-amber-500/15 text-amber-400',
    component: 'bg-blue-500/15 text-blue-400',
    accessory: 'bg-purple-500/15 text-purple-400',
    consumable: 'bg-cyan-500/15 text-cyan-400',
  }

  return (
    <div className="flex h-full flex-col gap-4">
      {/* 标题栏 */}
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-purple-500/20 to-violet-600/20 border border-purple-500/30">
          <PackageOpen className="h-5 w-5 text-purple-400" />
        </div>
        <div>
          <h1 className="text-lg font-semibold text-industrial-text">BOM 齐套管理</h1>
          <p className="text-xs text-industrial-text-muted">物料清单管理与库存齐套分析</p>
        </div>
      </div>

      <div className="flex flex-1 gap-4 min-h-0">
        {/* 左侧：产品选择器 + BOM树 */}
        <div className="w-72 flex flex-col gap-3">
          <div className="glass-card rounded-xl p-4">
            <label className="block text-xs text-industrial-text-muted mb-2">选择产品 BOM</label>
            <select
              value={selectedBomId}
              onChange={(e) => handleSelectBom(e.target.value)}
              className="w-full rounded-lg bg-industrial-bg border border-industrial-border px-3 py-2 text-sm text-industrial-text outline-none focus:border-industrial-primary"
            >
              {boms.map(bom => (
                <option key={bom.id} value={bom.id}>{bom.product_code} v{bom.version}</option>
              ))}
            </select>
          </div>

          {/* BOM 物料树形结构 */}
          <div className="flex-1 glass-card rounded-xl p-4 overflow-auto">
            <p className="text-xs text-industrial-text-muted mb-3">物料清单</p>
            {selectedBom?.items ? (
              <div className="space-y-1">
                {selectedBom.items.map(item => (
                  <div
                    key={item.id}
                    className="flex items-center gap-2 rounded-md px-2.5 py-2 text-sm hover:bg-industrial-card-hover/50 cursor-pointer group transition-colors"
                  >
                    <ChevronRight className="h-3.5 w-3.5 text-industrial-text-muted group-hover:text-industrial-text-secondary shrink-0" />
                    <span className="flex-1 truncate text-industrial-text-secondary group-hover:text-industrial-text">{item.material_name}</span>
                    <span className="text-xs text-industrial-text-muted tabular-nums">{item.quantity}{item.unit}</span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-industrial-text-muted text-center py-8">请选择一个 BOM</p>
            )}
          </div>
        </div>

        {/* 右侧：物料明细 + 齐套分析 */}
        <div className="flex-1 flex flex-col gap-4 min-w-0">
          {/* 物料明细表格 */}
          <div className="glass-card rounded-xl overflow-hidden flex-1 flex flex-col min-h-0">
            <div className="px-4 py-3 border-b border-industrial-border flex items-center justify-between">
              <span className="text-sm font-medium text-industrial-text">物料明细</span>
              {selectedBom && (
                <span className="text-xs text-industrial-text-muted">
                  版本 {selectedBom.version} · 共 {selectedBom.items.length} 项物料
                </span>
              )}
            </div>

            <div className="flex-1 overflow-auto">
              {selectedBom?.items ? (
                <table className="w-full text-sm">
                  <thead className="sticky top-0 bg-industrial-sidebar">
                    <tr className="text-left text-xs text-industrial-text-muted">
                      <th className="px-4 py-3 font-medium">物料编码</th>
                      <th className="px-4 py-3 font-medium">名称</th>
                      <th className="px-4 py-3 font-medium">用量</th>
                      <th className="px-4 py-3 font-medium">类型</th>
                      <th className="px-4 py-3 font-medium">单价</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-industrial-border/50">
                    {selectedBom.items.map(item => (
                      <tr key={item.id} className="hover:bg-industrial-card-hover/30 transition-colors">
                        <td className="px-4 py-2.5 font-mono text-xs text-industrial-primary">{item.material_code}</td>
                        <td className="px-4 py-2.5 text-industrial-text">{item.material_name}</td>
                        <td className="px-4 py-2.5 text-industrial-text-secondary tabular-nums">{item.quantity} {item.unit}</td>
                        <td className="px-4 py-2.5">
                          <span className={`rounded px-1.5 py-0.5 text-[11px] ${typeColors[item.material_type] || 'bg-gray-500/15 text-gray-400'}`}>
                            {item.material_type}
                          </span>
                        </td>
                        <td className="px-4 py-2.5 text-industrial-text-secondary tabular-nums">¥{item.cost.toFixed(2)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <div className="flex items-center justify-center h-32 text-industrial-text-muted text-sm">暂无数据</div>
              )}
            </div>
          </div>

          {/* 齐套分析按钮 + 结果 */}
          <div className="space-y-3">
            <button
              onClick={checkAvailability}
              disabled={!selectedBomId || checkingAvailability}
              className="flex items-center justify-center gap-2 w-full rounded-xl bg-industrial-primary/10 hover:bg-industrial-primary/20 border border-industrial-primary/30 text-industrial-primary py-2.5 text-sm font-medium transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
            >
              <Search className="h-4 w-4" />
              {checkingAvailability ? '分析中...' : '开始齐套分析'}
            </button>

            {availability.length > 0 && (
              <div className="glass-card rounded-xl p-4">
                <p className="text-xs font-medium text-industrial-text mb-3">齐套分析结果</p>
                <div className="space-y-2 max-h-40 overflow-auto">
                  {availability.map(item => (
                    <div key={item.material_code} className={`flex items-center gap-3 rounded-lg px-3 py-2 ${
                      item.status === 'ok' ? 'bg-green-500/5' : 'bg-red-500/5'
                    }`}>
                      {item.status === 'ok' ? (
                        <CheckCircle className="h-4 w-4 text-industrial-success shrink-0" />
                      ) : (
                        <XCircle className="h-4 w-4 text-industrial-danger shrink-0" />
                      )}
                      <span className="flex-1 text-sm text-industrial-text truncate">{item.material_name}</span>
                      <span className="text-xs text-industrial-text-muted tabular-nums">
                        需 {item.required} / 有 {item.available}
                      </span>
                      {item.shortage > 0 && (
                        <span className="text-xs text-industrial-danger font-medium tabular-nums">
                          缺 {item.shortage}
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
