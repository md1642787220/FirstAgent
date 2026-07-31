import { useState, useEffect, useRef, useCallback } from 'react'
import {
  BookOpen, Upload, Trash2, Search, RefreshCw,
  FileText, Database, File, Loader2, X, AlertCircle,
  CheckCircle2, HardDrive, FileSearch, Grid3X3, BrainCircuit, History
} from 'lucide-react'
import api, { apiUrl } from '../services/http'

// ============ 类型 ============
interface DocInfo {
  id: string
  name: string
  source: string
  size: number
  chunks: number
  chunk_count: number
  category: string
  upload_time: string
  summary?: string
}

interface KnowledgeStats {
  vector_store: string
  embedding_model: string
  total_documents: number
  total_chunks: number
  sources: Record<string, number>
  categories: Record<string, number>
  collection_name: string
  message: string
}

/** 流水线每一步的状态 */
type StepStatus = 'pending' | 'running' | 'success' | 'error'

interface PipelineStep {
  key: string
  icon: React.ReactNode
  label: string
  status: StepStatus
  message: string
}

// ============ 格式化 ============
function formatSize(bytes: number) {
  if (!bytes) return '-'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / 1048576).toFixed(1) + ' MB'
}

function formatTime(t: string) {
  if (!t) return '-'
  return new Date(t).toLocaleString('zh-CN')
}

// ============ 主组件 ============
export default function KnowledgePage() {
  const [stats, setStats] = useState<KnowledgeStats | null>(null)
  const [docs, setDocs] = useState<DocInfo[]>([])
  const [uploading, setUploading] = useState(false)
  const [rebuilding, setRebuilding] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState<any[]>([])
  const [searching, setSearching] = useState(false)
  const [message, setMessage] = useState<{ type: 'ok' | 'err'; text: string } | null>(null)
  const [dragOver, setDragOver] = useState(false)
  const [uploadFileName, setUploadFileName] = useState('')
  const fileRef = useRef<HTMLInputElement>(null)
  const abortRef = useRef<AbortController | null>(null)

  // ──── 流水线步骤状态 ────
  const initialSteps = (): PipelineStep[] => [
    { key: 'receive', icon: <File className="h-4 w-4" />, label: '接收文件', status: 'pending', message: '' },
    { key: 'parse', icon: <FileSearch className="h-4 w-4" />, label: '文档解析', status: 'pending', message: '' },
    { key: 'chunk', icon: <Grid3X3 className="h-4 w-4" />, label: '智能分片', status: 'pending', message: '' },
    { key: 'vectorize', icon: <BrainCircuit className="h-4 w-4" />, label: '向量化&写入', status: 'pending', message: '' },
    { key: 'cleanup', icon: <History className="h-4 w-4" />, label: '刷新缓存', status: 'pending', message: '' },
  ]
  const [pipeline, setPipeline] = useState<PipelineStep[]>(initialSteps())

  // 加载状态 & 文档列表
  const loadAll = useCallback(async () => {
    try {
      const [s, d] = await Promise.all([
        api.get('/knowledge/status'),
        api.get('/knowledge/documents'),
      ])
      setStats(s)
      setDocs(Array.isArray(d) ? d : d?.documents || [])
    } catch {
      // 静默失败
    }
  }, [])

  useEffect(() => { loadAll() }, [loadAll])

  // 上传（SSE 流式）
  const handleUpload = async (file: File) => {
    if (!file || uploading) return
    setUploading(true)
    setUploadFileName(file.name)
    setMessage(null)
    setPipeline(initialSteps())

    const form = new FormData()
    form.append('file', file)

    const controller = new AbortController()
    abortRef.current = controller

    try {
      const response = await fetch(apiUrl('/knowledge/documents/stream'), {
        method: 'POST',
        body: form,
        signal: controller.signal,
      })

      if (!response.ok) {
        let errMsg = `请求失败 (${response.status})`
        try {
          const body = await response.json()
          errMsg = body.detail || errMsg
        } catch {}
        throw new Error(errMsg)
      }

      if (!response.body) throw new Error('浏览器不支持流式响应')

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      let done = false

      while (!done) {
        const { done: streamDone, value } = await reader.read()
        if (streamDone) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          const trimmed = line.trim()
          if (!trimmed || trimmed.startsWith(':')) continue

          if (trimmed.startsWith('data:')) {
            const dataStr = trimmed.slice(5).trim()
            if (!dataStr) continue

            try {
              const event = JSON.parse(dataStr)
              handlePipelineEvent(event, file.name)

              if (event.step === 'done') {
                done = true
                if (event.message) {
                  setMessage({ type: 'ok', text: event.message })
                }
                loadAll()
              }
            } catch {
              // JSON 解析失败，忽略
            }
          }
        }
      }
    } catch (e: any) {
      if (e.name !== 'AbortError') {
        const errMsg = e?.message || '上传失败'
        setMessage({ type: 'err', text: errMsg })
        // 把当前 running 的步骤标为 error
        setPipeline(prev => prev.map(s =>
          s.status === 'running' ? { ...s, status: 'error' as StepStatus, message: errMsg } : s
        ))
      }
    } finally {
      setUploading(false)
      abortRef.current = null
    }
  }

  /** 根据 SSE 事件更新流水线状态 */
  const handlePipelineEvent = (event: { step: string; status: string; message: string }, _filename: string) => {
    setPipeline(prev => {
      // 将除当前步骤外所有 running 改为 success（处理上一步遗留）
      const updated = prev.map(s => ({
        ...s,
        status: s.key === event.step
          ? event.status as StepStatus
          : s.status === 'running' ? ('success' as StepStatus) : s.status,
        message: s.key === event.step ? event.message : s.message,
      }))

      // 如果遇到 error，将之后所有 pending 置为 pending（保持不变即可，实际上我们不改变后续）
      return updated
    })
  }

  // 取消上传
  const cancelUpload = () => {
    abortRef.current?.abort()
    setUploading(false)
    setPipeline(initialSteps())
  }

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault(); setDragOver(false)
    const f = e.dataTransfer.files[0]
    if (f) handleUpload(f)
  }

  // 删除
  const handleDelete = async (id: string) => {
    try {
      const res = await api.del(`/knowledge/documents/${id}`)
      setMessage({ type: 'ok', text: res.message || '已删除' })
      loadAll()
    } catch (e: any) {
      setMessage({ type: 'err', text: e?.message || '删除失败' })
    }
  }

  // 重建索引
  const handleRebuild = async () => {
    setRebuilding(true)
    try {
      const res = await api.post('/knowledge/rebuild')
      setMessage({ type: 'ok', text: `索引已重建: ${res.message}` })
      loadAll()
    } catch (e: any) {
      setMessage({ type: 'err', text: e?.message || '重建失败' })
    } finally {
      setRebuilding(false)
    }
  }

  // 检索
  const handleSearch = async () => {
    if (!searchQuery.trim()) return
    setSearching(true)
    try {
      const res = await api.post('/knowledge/search', {
        query: searchQuery,
        k: 5,
      })
      setSearchResults(res.results || res.documents || [])
    } catch {
      setSearchResults([])
    } finally {
      setSearching(false)
    }
  }

  return (
    <div className="flex h-full flex-col gap-6">
      {/* 头部 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-industrial-text">知识库管理</h1>
          <p className="text-sm text-industrial-text-muted">上传文档 · 管理索引 · 检索内容</p>
        </div>
        <button
          onClick={handleRebuild}
          disabled={rebuilding}
          className="flex items-center gap-2 rounded-lg bg-industrial-primary px-4 py-2 text-sm font-medium text-white hover:bg-industrial-primary/80 disabled:opacity-50"
        >
          {rebuilding ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
          重建索引
        </button>
      </div>

      {/* 状态卡片 */}
      <div className="grid grid-cols-4 gap-4">
        <StatCard icon={<Database />} label="向量存储" value={stats?.vector_store || '-'} />
        <StatCard icon={<HardDrive />} label="文档总数" value={stats?.total_documents || 0} />
        <StatCard icon={<FileText />} label="文档切片" value={stats?.total_chunks || 0} />
        <StatCard icon={<BookOpen />} label="模型" value={stats?.embedding_model || '-'} />
      </div>

      {/* 上传 + 文档列表 */}
      <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
        {/* 左侧：文档列表 */}
        <div className="flex flex-col gap-3 rounded-xl border border-industrial-border bg-industrial-sidebar p-5">
          <h2 className="flex items-center gap-2 text-sm font-semibold text-industrial-text">
            <FileText className="h-4 w-4" />
            已上传文档 ({docs.length})
          </h2>
          <div className="max-h-[360px] space-y-2 overflow-y-auto">
            {docs.length === 0 && (
              <p className="py-8 text-center text-sm text-industrial-text-muted">暂无文档，请在右侧上传</p>
            )}
            {docs.map((d) => {
              const chunkCount = d.chunk_count || d.chunks
              return (
                <div
                  key={d.id}
                  className="flex flex-col rounded-lg bg-industrial-bg px-4 py-3 hover:bg-industrial-card-hover/50 transition-colors"
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex min-w-0 items-start gap-3">
                      <File className="h-5 w-5 shrink-0 text-industrial-primary mt-0.5" />
                      <div className="min-w-0 flex-1">
                        <p className="truncate text-sm font-medium text-industrial-text">{d.name || d.source?.split(':').pop() || '未知文档'}</p>
                        <p className="text-xs text-industrial-text-muted">
                          {chunkCount} 切片 · {d.category || '未分类'} · {formatSize(d.size)}
                        </p>
                        {d.summary && (
                          <p className="mt-1.5 text-xs text-industrial-text-secondary line-clamp-2 leading-relaxed border-l-2 border-industrial-primary/30 pl-2">
                            {d.summary}
                          </p>
                        )}
                      </div>
                    </div>
                    <button
                      onClick={() => handleDelete(d.id)}
                      className="ml-2 shrink-0 rounded p-1.5 text-industrial-text-muted hover:bg-red-500/10 hover:text-red-400"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* 右侧：上传区域 + 搜索 */}
        <div className="flex flex-col gap-4">
          {/* 上传卡片 / 流水线进度 */}
          {uploading ? (
            <PipelineProgress pipeline={pipeline} fileName={uploadFileName} onCancel={cancelUpload} />
          ) : (
            <div
              onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
              onDragLeave={() => setDragOver(false)}
              onDrop={onDrop}
              onClick={() => fileRef.current?.click()}
              className={`flex cursor-pointer flex-col items-center justify-center gap-3 rounded-xl border-2 border-dashed p-8 transition-colors ${
                dragOver
                  ? 'border-industrial-primary bg-industrial-primary/5'
                  : 'border-industrial-border hover:border-industrial-primary/50'
              }`}
            >
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-industrial-primary/10">
                <Upload className="h-6 w-6 text-industrial-primary" />
              </div>
              <div className="text-center">
                <p className="text-sm font-medium text-industrial-text">拖拽文件到此处，或点击上传</p>
                <p className="mt-1 text-xs text-industrial-text-muted">
                  支持 PDF、Word、Excel、PPTX、CSV、JSON、Markdown、图片
                </p>
              </div>
              <input
                ref={fileRef}
                type="file"
                className="hidden"
                accept=".pdf,.docx,.doc,.xlsx,.xls,.pptx,.csv,.json,.xml,.md,.html,.htm,.eml,.msg,.png,.jpg,.jpeg,.gif,.bmp"
                onChange={(e) => {
                  const f = e.target.files?.[0]
                  if (f) handleUpload(f)
                  e.target.value = ''
                }}
              />
            </div>
          )}

          {/* 消息提示 */}
          {message && (
            <div
              className={`flex items-center gap-2 rounded-lg px-4 py-3 text-sm ${
                message.type === 'ok'
                  ? 'bg-green-500/10 text-green-400'
                  : 'bg-red-500/10 text-red-400'
              }`}
            >
              {message.type === 'ok' ? <CheckCircle2 className="h-4 w-4" /> : <AlertCircle className="h-4 w-4" />}
              {message.text}
              <button className="ml-auto" onClick={() => setMessage(null)}>
                <X className="h-4 w-4" />
              </button>
            </div>
          )}

          {/* 搜索卡片 */}
          <div className="rounded-xl border border-industrial-border bg-industrial-sidebar p-5">
            <h2 className="mb-3 flex items-center gap-2 text-sm font-semibold text-industrial-text">
              <Search className="h-4 w-4" />
              知识检索
            </h2>
            <div className="flex gap-2">
              <input
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                placeholder="输入关键词搜索知识库..."
                className="flex-1 rounded-lg border border-industrial-border bg-industrial-bg px-3 py-2 text-sm text-industrial-text placeholder:text-industrial-text-muted focus:border-industrial-primary focus:outline-none"
              />
              <button
                onClick={handleSearch}
                disabled={searching}
                className="rounded-lg bg-industrial-primary px-4 py-2 text-sm text-white hover:bg-industrial-primary/80 disabled:opacity-50"
              >
                {searching ? <Loader2 className="h-4 w-4 animate-spin" /> : '搜索'}
              </button>
            </div>
            {searchResults.length > 0 && (
              <div className="mt-3 space-y-2">
                {searchResults.map((r, i) => (
                  <div key={i} className="rounded-lg bg-industrial-bg p-3">
                    <p className="text-xs text-industrial-text leading-relaxed line-clamp-3">
                      {r.content || r.page_content || '无内容'}
                    </p>
                    {r.metadata?.source && (
                      <p className="mt-1 text-[11px] text-industrial-text-muted">
                        来源: {r.metadata.source} · 分数: {r.score?.toFixed(3) || '-'}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

// ============ 流水线进度组件 ============
function PipelineProgress({
  pipeline,
  fileName,
  onCancel,
}: {
  pipeline: PipelineStep[]
  fileName: string
  onCancel: () => void
}) {
  return (
    <div className="rounded-xl border border-industrial-border bg-industrial-sidebar p-5">
      {/* 标题 + 文件名 */}
      <div className="mb-4 flex items-center justify-between">
        <div className="flex items-center gap-2 min-w-0">
          <Loader2 className="h-4 w-4 shrink-0 animate-spin text-industrial-primary" />
          <span className="text-sm font-medium text-industrial-text truncate">{fileName}</span>
        </div>
        <button
          onClick={(e) => { e.stopPropagation(); onCancel() }}
          className="shrink-0 rounded px-2 py-1 text-xs text-industrial-text-muted hover:bg-red-500/10 hover:text-red-400 transition-colors"
        >
          取消
        </button>
      </div>

      {/* 步骤列表 */}
      <div className="space-y-0">
        {pipeline.map((step, i) => (
          <div key={step.key}>
            {/* 连接线 */}
            {i > 0 && (
              <div className="ml-[19px] h-5 w-px"
                style={{ backgroundColor: step.status === 'success' ? '#22c55e' : '#334155' }}
              />
            )}
            {/* 步骤行 */}
            <div className={`flex items-center gap-3 py-1.5 rounded-md transition-colors ${
              step.status === 'running' ? 'bg-industrial-primary/5 -mx-1 px-1' : ''
            }`}>
              {/* 状态图标 */}
              <div className={`flex h-[26px] w-[26px] shrink-0 items-center justify-center rounded-full ${
                step.status === 'success' ? 'bg-green-500/20 text-green-400' :
                step.status === 'running' ? 'bg-industrial-primary/20 text-industrial-primary' :
                step.status === 'error' ? 'bg-red-500/20 text-red-400' :
                'bg-industrial-bg text-industrial-text-muted'
              }`}>
                {step.status === 'running' ? (
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                ) : step.status === 'success' ? (
                  <CheckCircle2 className="h-3.5 w-3.5" />
                ) : step.status === 'error' ? (
                  <X className="h-3.5 w-3.5" />
                ) : (
                  <span className="text-[10px]">{step.icon}</span>
                )}
              </div>

              {/* 步骤标签 + 消息 */}
              <div className="min-w-0 flex-1">
                <p className={`text-xs font-medium truncate ${
                  step.status === 'success' ? 'text-green-400' :
                  step.status === 'running' ? 'text-industrial-primary' :
                  step.status === 'error' ? 'text-red-400' :
                  'text-industrial-text-muted'
                }`}>
                  {step.label}
                </p>
                {step.message && (
                  <p className={`text-[11px] truncate mt-0.5 ${
                    step.status === 'error' ? 'text-red-400/70' :
                    step.status === 'success' ? 'text-green-400/70' :
                    'text-industrial-text-muted'
                  }`}>
                    {step.message}
                  </p>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

// ============ 状态卡片子组件 ============
function StatCard({ icon, label, value }: { icon: React.ReactNode; label: string; value: React.ReactNode }) {
  return (
    <div className="flex items-center gap-3 rounded-xl border border-industrial-border bg-industrial-sidebar px-4 py-4">
      <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-industrial-primary/10">
        <span className="text-industrial-primary">{icon}</span>
      </div>
      <div>
        <p className="text-xs text-industrial-text-muted">{label}</p>
        <p className="text-lg font-semibold text-industrial-text">{value}</p>
      </div>
    </div>
  )
}
