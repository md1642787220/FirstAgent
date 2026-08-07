import { useState, useEffect } from 'react'
import { PackageOpen, Plus, Save, X, Trash2, Pencil, Search, RotateCw } from 'lucide-react'
import api from '../services/http'

/* ---- 类型 ---- */
interface BOMItem {
  id: number
  bom_id: string
  material_code: string
  material_name: string
  specification: string | null
  quantity: number
  unit: string | null
  material_type: string | null
  source_supplier: string | null
  cost: number
  lead_time: number
  remark: string | null
}

interface BOM {
  id: string
  product_code: string
  product_name: string
  version: string
  status: string
  items: BOMItem[]
  total_cost?: number
}

const DEFAULT_ITEM: Omit<BOMItem, 'id' | 'bom_id'> = {
  material_code: '',
  material_name: '',
  specification: '',
  quantity: 1,
  unit: '',
  material_type: 'component',
  source_supplier: '',
  cost: 0,
  lead_time: 0,
  remark: '',
}

/* ---- 组件 ---- */
export default function BOMPage() {
  const [boms, setBoms] = useState<BOM[]>([])
  const [selectedBomId, setSelectedBomId] = useState('')
  const [selectedBom, setSelectedBom] = useState<BOM | null>(null)
  const [loading, setLoading] = useState(true)

  // 编辑状态
  const [editingId, setEditingId] = useState<number | 'new' | null>(null)
  const [editData, setEditData] = useState<Partial<BOMItem>>({})
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  // 搜索
  const [search, setSearch] = useState('')

  /* ---- 加载 BOM 列表 ---- */
  useEffect(() => { loadBOMs() }, [])

  async function loadBOMs() {
    try {
      setLoading(true)
      const res = await api.get<{ boms: BOM[]; count: number }>('/bom')
      const list = res.boms || []
      setBoms(list)
      if (list.length > 0 && !selectedBomId) {
        setSelectedBomId(list[0].id)
        loadBOMDetail(list[0].id)
      }
    } catch (err) {
      console.error('[BOM] loadBOMs error:', err)
    } finally {
      setLoading(false)
    }
  }

  async function loadBOMDetail(id: string) {
    try {
      setSelectedBom(null)
      const data = await api.get<BOM>(`/bom/${id}`)
      setSelectedBom(data)
      setEditingId(null)
      setError('')
    } catch (err) {
      console.error('[BOM] Detail error:', err)
    }
  }

  function handleSelectBom(id: string) {
    setSelectedBomId(id)
    loadBOMDetail(id)
  }

  /* ---- 搜索过滤 ---- */
  const filteredItems = selectedBom?.items.filter(item => {
    if (!search) return true
    const s = search.toLowerCase()
    return (
      item.material_code.toLowerCase().includes(s) ||
      item.material_name.toLowerCase().includes(s) ||
      (item.specification ?? '').toLowerCase().includes(s) ||
      (item.material_type ?? '').toLowerCase().includes(s)
    )
  }) ?? []

  /* ---- 行编辑 ---- */
  function startEdit(item: BOMItem) {
    setEditingId(item.id)
    setEditData({ ...item })
    setError('')
  }

  function startNew() {
    setEditingId('new')
    setEditData({ ...DEFAULT_ITEM })
    setError('')
  }

  function cancelEdit() {
    setEditingId(null)
    setEditData({})
    setError('')
  }

  function updateField(field: keyof BOMItem, value: string | number) {
    setEditData(prev => ({ ...prev, [field]: value }))
  }

  async function saveEdit() {
    if (!selectedBomId) return
    setSaving(true)
    setError('')
    try {
      if (editingId === 'new') {
        // 新增
        await api.post(`/bom/${selectedBomId}/items`, {
          material_code: editData.material_code || '',
          material_name: editData.material_name || '',
          specification: editData.specification || null,
          quantity: Number(editData.quantity) || 0,
          unit: editData.unit || null,
          material_type: editData.material_type || 'component',
          source_supplier: editData.source_supplier || null,
          cost: Number(editData.cost) || 0,
          lead_time: Number(editData.lead_time) || 0,
          remark: editData.remark || null,
        })
      } else {
        // 修改已有
        await api.put(`/bom/${selectedBomId}/items/${editingId}`, {
          material_code: editData.material_code,
          material_name: editData.material_name,
          specification: editData.specification,
          quantity: editData.quantity != null ? Number(editData.quantity) : undefined,
          unit: editData.unit,
          material_type: editData.material_type,
          source_supplier: editData.source_supplier,
          cost: editData.cost != null ? Number(editData.cost) : undefined,
          lead_time: editData.lead_time != null ? Number(editData.lead_time) : undefined,
          remark: editData.remark,
        })
      }
      await loadBOMDetail(selectedBomId)
      setEditingId(null)
      setEditData({})
    } catch (e: any) {
      setError(e?.message || '保存失败')
    } finally {
      setSaving(false)
    }
  }

  async function deleteItem(itemId: number) {
    if (!selectedBomId || !confirm('确定删除此物料？')) return
    try {
      await api.del(`/bom/${selectedBomId}/items/${itemId}`)
      await loadBOMDetail(selectedBomId)
    } catch (e: any) {
      setError(e?.message || '删除失败')
    }
  }

  /* ---- 渲染 ---- */
  return (
    <div className="flex h-full flex-col gap-4">
      {/* 标题栏 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-purple-500/20 to-violet-600/20 border border-purple-500/30">
            <PackageOpen className="h-5 w-5 text-purple-400" />
          </div>
          <div>
            <h1 className="text-lg font-semibold text-industrial-text">传感器BOM 管理</h1>
            <p className="text-xs text-industrial-text-muted">
              {selectedBom ? `${selectedBom.product_name} (v${selectedBom.version}) · ${selectedBom.items.length} 项物料` : '请选择产品'}
            </p>
          </div>
        </div>
        <button onClick={loadBOMs} className="flex items-center gap-1.5 rounded-lg border border-industrial-border px-3 py-2 text-xs text-industrial-text-secondary hover:text-industrial-text hover:bg-industrial-card transition-colors">
          <RotateCw className="h-3.5 w-3.5" /> 刷新
        </button>
      </div>

      <div className="flex flex-1 gap-4 min-h-0">
        {/* 左侧：产品列表 */}
        <div className="w-72 flex flex-col gap-3">
          <div className="glass-card rounded-xl p-4">
            <label className="block text-xs text-industrial-text-muted mb-2">选择产品</label>
            <select
              value={selectedBomId}
              onChange={e => handleSelectBom(e.target.value)}
              className="w-full rounded-lg bg-industrial-bg border border-industrial-border px-3 py-2 text-sm text-industrial-text outline-none focus:border-industrial-primary"
            >
              {boms.map(bom => (
                <option key={bom.id} value={bom.id}>
                  {bom.product_code} — {bom.product_name}
                </option>
              ))}
            </select>
          </div>

          {/* BOM 物料统计 */}
          {selectedBom && (
            <div className="glass-card rounded-xl p-4">
              <p className="text-xs text-industrial-text-muted mb-3">物料类型分布</p>
              <div className="space-y-2">
                {typeStats(selectedBom.items).map(({ type, count }) => (
                  <div key={type} className="flex items-center justify-between text-xs">
                    <span className="text-industrial-text-secondary">{typeLabels[type] || type}</span>
                    <span className="text-industrial-text tabular-nums">{count} 项</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* 右侧：物料表格 */}
        <div className="flex-1 flex flex-col gap-3 min-w-0">
          {/* 搜索 + 操作 */}
          <div className="flex items-center gap-3">
            <div className="relative flex-1 max-w-xs">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-industrial-text-muted" />
              <input
                type="text"
                placeholder="搜索物料编码 / 名称..."
                value={search}
                onChange={e => setSearch(e.target.value)}
                className="w-full rounded-lg bg-industrial-bg border border-industrial-border pl-9 pr-3 py-2 text-sm text-industrial-text outline-none focus:border-industrial-primary"
              />
            </div>
            {error && <span className="text-xs text-industrial-danger">{error}</span>}
            <div className="flex-1" />
            {selectedBom && (
              <button
                onClick={startNew}
                disabled={editingId !== null}
                className="flex items-center gap-1.5 rounded-lg bg-industrial-primary/10 hover:bg-industrial-primary/20 border border-industrial-primary/30 text-industrial-primary px-3 py-2 text-sm font-medium transition-colors disabled:opacity-40"
              >
                <Plus className="h-4 w-4" /> 新增物料
              </button>
            )}
          </div>

          {/* 表格 */}
          <div className="glass-card rounded-xl overflow-hidden flex-1 flex flex-col min-h-0">
            <div className="flex-1 overflow-auto">
              {selectedBom ? (
                <table className="w-full text-sm">
                  <thead className="sticky top-0 z-10 bg-industrial-sidebar">
                    <tr className="text-left text-xs text-industrial-text-muted">
                      <th className="px-4 py-3 font-medium w-28">物料编码</th>
                      <th className="px-4 py-3 font-medium min-w-[160px]">名称</th>
                      <th className="px-4 py-3 font-medium w-16">用量</th>
                      <th className="px-4 py-3 font-medium w-16">单位</th>
                      <th className="px-4 py-3 font-medium w-20">类型</th>
                      <th className="px-4 py-3 font-medium w-28">版本/规格</th>
                      <th className="px-4 py-3 font-medium w-20">单价</th>
                      <th className="px-4 py-3 font-medium w-24">操作</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-industrial-border/50">
                    {filteredItems.map(item => (
                      editingId === item.id ? renderEditRow(item) : renderViewRow(item)
                    ))}
                    {editingId === 'new' && renderNewRow()}
                  </tbody>
                </table>
              ) : (
                <div className="flex items-center justify-center h-32 text-industrial-text-muted text-sm">
                  {loading ? '加载中...' : '请选择一个产品'}
                </div>
              )}
            </div>
            {/* 底部统计 */}
            {selectedBom && (
              <div className="border-t border-industrial-border px-4 py-2 text-xs text-industrial-text-muted">
                显示 {filteredItems.length} / {selectedBom.items.length} 项
                {selectedBom.total_cost != null && (
                  <span className="ml-4">总成本 ¥{selectedBom.total_cost.toFixed(2)}</span>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )

  /* ---- 行渲染函数 ---- */

  function renderViewRow(item: BOMItem) {
    const typeLabel = typeLabels[item.material_type ?? ''] ?? (item.material_type || '-')
    return (
      <tr key={item.id} className="hover:bg-industrial-card-hover/30 transition-colors group">
        <td className="px-4 py-2.5 font-mono text-xs text-industrial-primary">{item.material_code}</td>
        <td className="px-4 py-2.5 text-industrial-text">{item.material_name}</td>
        <td className="px-4 py-2.5 text-industrial-text-secondary tabular-nums">{item.quantity}</td>
        <td className="px-4 py-2.5 text-industrial-text-muted">{item.unit || '-'}</td>
        <td className="px-4 py-2.5">
          <span className={`rounded px-1.5 py-0.5 text-[11px] ${typeColor(item.material_type ?? '')}`}>
            {typeLabel}
          </span>
        </td>
        <td className="px-4 py-2.5 text-xs text-industrial-text-muted">{item.specification || '-'}</td>
        <td className="px-4 py-2.5 text-industrial-text-secondary tabular-nums">
          {item.cost > 0 ? `¥${item.cost.toFixed(2)}` : '-'}
        </td>
        <td className="px-4 py-2.5">
          <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
            <button
              onClick={() => startEdit(item)}
              disabled={editingId !== null}
              className="flex h-7 w-7 items-center justify-center rounded hover:bg-industrial-card text-industrial-text-muted hover:text-industrial-neutral transition-colors disabled:opacity-30"
            >
              <Pencil className="h-3.5 w-3.5" />
            </button>
            <button
              onClick={() => deleteItem(item.id)}
              disabled={editingId !== null}
              className="flex h-7 w-7 items-center justify-center rounded hover:bg-red-500/15 text-industrial-text-muted hover:text-industrial-danger transition-colors disabled:opacity-30"
            >
              <Trash2 className="h-3.5 w-3.5" />
            </button>
          </div>
        </td>
      </tr>
    )
  }

  function renderEditRow(item: BOMItem) {
    return (
      <tr key={item.id} className="bg-industrial-primary/5">
        <td className="px-4 py-1.5">
          <input value={editData.material_code ?? ''} onChange={e => updateField('material_code', e.target.value)}
            className="w-full rounded bg-industrial-bg border border-industrial-border px-2 py-1.5 text-xs text-industrial-text outline-none focus:border-industrial-primary" />
        </td>
        <td className="px-4 py-1.5">
          <input value={editData.material_name ?? ''} onChange={e => updateField('material_name', e.target.value)}
            className="w-full rounded bg-industrial-bg border border-industrial-border px-2 py-1.5 text-xs text-industrial-text outline-none focus:border-industrial-primary" />
        </td>
        <td className="px-4 py-1.5">
          <input type="number" value={editData.quantity ?? 0} onChange={e => updateField('quantity', e.target.value)}
            className="w-full rounded bg-industrial-bg border border-industrial-border px-2 py-1.5 text-xs text-industrial-text outline-none focus:border-industrial-primary" />
        </td>
        <td className="px-4 py-1.5">
          <input value={editData.unit ?? ''} onChange={e => updateField('unit', e.target.value)}
            className="w-full rounded bg-industrial-bg border border-industrial-border px-2 py-1.5 text-xs text-industrial-text outline-none focus:border-industrial-primary" />
        </td>
        <td className="px-4 py-1.5">
          <select value={editData.material_type ?? 'component'} onChange={e => updateField('material_type', e.target.value)}
            className="w-full rounded bg-industrial-bg border border-industrial-border px-2 py-1.5 text-xs text-industrial-text outline-none focus:border-industrial-primary">
            <option value="raw_material">原材料</option>
            <option value="component">组件</option>
            <option value="accessory">配件</option>
            <option value="consumable">耗材</option>
            <option value="semi_finished">半成品</option>
            <option value="finished">成品</option>
          </select>
        </td>
        <td className="px-4 py-1.5">
          <input value={editData.specification ?? ''} onChange={e => updateField('specification', e.target.value)}
            className="w-full rounded bg-industrial-bg border border-industrial-border px-2 py-1.5 text-xs text-industrial-text outline-none focus:border-industrial-primary" />
        </td>
        <td className="px-4 py-1.5">
          <input type="number" step="0.01" value={editData.cost ?? 0} onChange={e => updateField('cost', e.target.value)}
            className="w-full rounded bg-industrial-bg border border-industrial-border px-2 py-1.5 text-xs text-industrial-text outline-none focus:border-industrial-primary" />
        </td>
        <td className="px-4 py-1.5">
          <div className="flex items-center gap-1">
            <button onClick={saveEdit} disabled={saving}
              className="flex h-7 w-7 items-center justify-center rounded bg-green-500/15 text-green-400 hover:bg-green-500/25 transition-colors disabled:opacity-40">
              <Save className="h-3.5 w-3.5" />
            </button>
            <button onClick={cancelEdit} disabled={saving}
              className="flex h-7 w-7 items-center justify-center rounded bg-red-500/15 text-red-400 hover:bg-red-500/25 transition-colors disabled:opacity-40">
              <X className="h-3.5 w-3.5" />
            </button>
          </div>
        </td>
      </tr>
    )
  }

  function renderNewRow() {
    return (
      <tr className="bg-industrial-primary/10">
        <td className="px-4 py-1.5">
          <input value={editData.material_code ?? ''} onChange={e => updateField('material_code', e.target.value)}
            className="w-full rounded bg-industrial-bg border border-industrial-border px-2 py-1.5 text-xs text-industrial-text outline-none focus:border-industrial-primary" />
        </td>
        <td className="px-4 py-1.5">
          <input value={editData.material_name ?? ''} onChange={e => updateField('material_name', e.target.value)}
            className="w-full rounded bg-industrial-bg border border-industrial-border px-2 py-1.5 text-xs text-industrial-text outline-none focus:border-industrial-primary" />
        </td>
        <td className="px-4 py-1.5">
          <input type="number" value={editData.quantity ?? 1} onChange={e => updateField('quantity', e.target.value)}
            className="w-full rounded bg-industrial-bg border border-industrial-border px-2 py-1.5 text-xs text-industrial-text outline-none focus:border-industrial-primary" />
        </td>
        <td className="px-4 py-1.5">
          <input value={editData.unit ?? ''} onChange={e => updateField('unit', e.target.value)}
            className="w-full rounded bg-industrial-bg border border-industrial-border px-2 py-1.5 text-xs text-industrial-text outline-none focus:border-industrial-primary" />
        </td>
        <td className="px-4 py-1.5">
          <select value={editData.material_type ?? 'component'} onChange={e => updateField('material_type', e.target.value)}
            className="w-full rounded bg-industrial-bg border border-industrial-border px-2 py-1.5 text-xs text-industrial-text outline-none focus:border-industrial-primary">
            <option value="raw_material">原材料</option>
            <option value="component">组件</option>
            <option value="accessory">配件</option>
            <option value="consumable">耗材</option>
            <option value="semi_finished">半成品</option>
            <option value="finished">成品</option>
          </select>
        </td>
        <td className="px-4 py-1.5">
          <input value={editData.specification ?? ''} onChange={e => updateField('specification', e.target.value)}
            className="w-full rounded bg-industrial-bg border border-industrial-border px-2 py-1.5 text-xs text-industrial-text outline-none focus:border-industrial-primary" />
        </td>
        <td className="px-4 py-1.5">
          <input type="number" step="0.01" value={editData.cost ?? 0} onChange={e => updateField('cost', e.target.value)}
            className="w-full rounded bg-industrial-bg border border-industrial-border px-2 py-1.5 text-xs text-industrial-text outline-none focus:border-industrial-primary" />
        </td>
        <td className="px-4 py-1.5">
          <div className="flex items-center gap-1">
            <button onClick={saveEdit} disabled={saving}
              className="flex h-7 w-7 items-center justify-center rounded bg-green-500/15 text-green-400 hover:bg-green-500/25 transition-colors disabled:opacity-40">
              <Save className="h-3.5 w-3.5" />
            </button>
            <button onClick={cancelEdit} disabled={saving}
              className="flex h-7 w-7 items-center justify-center rounded bg-red-500/15 text-red-400 hover:bg-red-500/25 transition-colors disabled:opacity-40">
              <X className="h-3.5 w-3.5" />
            </button>
          </div>
        </td>
      </tr>
    )
  }
}

/* ---- 工具函数 ---- */

const typeLabels: Record<string, string> = {
  raw_material: '原材料',
  component: '组件',
  accessory: '配件',
  consumable: '耗材',
  semi_finished: '半成品',
  finished: '成品',
}

function typeColor(t: string): string {
  const m: Record<string, string> = {
    raw_material: 'bg-amber-500/15 text-amber-400',
    component: 'bg-blue-500/15 text-blue-400',
    accessory: 'bg-purple-500/15 text-purple-400',
    consumable: 'bg-cyan-500/15 text-cyan-400',
    semi_finished: 'bg-emerald-500/15 text-emerald-400',
    finished: 'bg-indigo-500/15 text-indigo-400',
  }
  return m[t] || 'bg-gray-500/15 text-gray-400'
}

function typeStats(items: BOMItem[]) {
  const map: Record<string, number> = {}
  items.forEach(i => {
    const t = i.material_type || 'other'
    map[t] = (map[t] || 0) + 1
  })
  return Object.entries(map)
    .sort((a, b) => b[1] - a[1])
    .map(([type, count]) => ({ type, count }))
}
