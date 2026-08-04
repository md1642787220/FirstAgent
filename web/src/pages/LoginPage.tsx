import { useState, type FormEvent } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { User, Lock, Loader2, AlertCircle, Eye, EyeOff } from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'
import api from '../services/http'

interface LoginResult {
  token: string
  username: string
  expires_at: number
}

export default function LoginPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const { login } = useAuth()
  const from = (location.state as { from?: string })?.from || '/'

  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [showPwd, setShowPwd] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    if (loading) return
    setError('')
    setLoading(true)
    try {
      const result = await api.post<LoginResult>('/auth/login', {
        username: username.trim(),
        password,
      })
      login({
        token: result.token,
        username: result.username,
        expiresAt: result.expires_at,
      })
      navigate(from, { replace: true })
    } catch (err: any) {
      setError(err?.message || '登录失败，请检查账号密码')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="relative flex h-screen w-screen items-center justify-center overflow-hidden bg-industrial-bg">
      {/* 背景装饰光晕 */}
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute -top-40 -left-40 h-96 w-96 rounded-full bg-industrial-primary/10 blur-3xl" />
        <div className="absolute -bottom-40 -right-40 h-96 w-96 rounded-full bg-industrial-accent/10 blur-3xl" />
        <div className="absolute top-1/2 left-1/2 h-[600px] w-[600px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-industrial-primary/5 blur-3xl" />
      </div>

      {/* 登录卡片 */}
      <div className="relative z-10 w-full max-w-md px-4">
        <div className="glass-card rounded-2xl p-8 shadow-2xl">
          {/* Logo + 标题（与主页左上角保持一致） */}
          <div className="flex flex-col items-center gap-2 mb-8">
            <img
              src="/xg-logo.png"
              alt="XG Logo"
              className="h-12 w-48 object-contain"
              onError={(e) => {
                ;(e.target as HTMLImageElement).style.display = 'none'
              }}
            />
            <div className="flex items-baseline gap-1.5 leading-tight">
              <span className="text-sm font-semibold text-industrial-text">XG Agent</span>
              <span className="text-xs text-industrial-accent font-medium">v2.1.0</span>
            </div>
            <p className="text-xs text-industrial-text-muted mt-1">焊接设备 AI Agent 综合管理平台</p>
          </div>

          {/* 错误提示 */}
          {error && (
            <div className="mb-4 flex items-center gap-2 rounded-lg border border-industrial-danger/30 bg-industrial-danger/10 px-3 py-2 text-sm text-industrial-danger">
              <AlertCircle className="h-4 w-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* 登录表单 */}
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* 账号 */}
            <div>
              <label className="block text-xs font-medium text-industrial-text-secondary mb-1.5">账号</label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-industrial-text-muted" />
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="请输入账号"
                  autoComplete="username"
                  required
                  className="w-full pl-10 pr-3 py-2.5 rounded-lg bg-industrial-bg border border-industrial-border text-sm text-industrial-text placeholder:text-industrial-text-muted focus:border-industrial-primary/50 focus:outline-none focus:ring-2 focus:ring-industrial-primary/20 transition-all"
                />
              </div>
            </div>

            {/* 密码 */}
            <div>
              <label className="block text-xs font-medium text-industrial-text-secondary mb-1.5">密码</label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-industrial-text-muted" />
                <input
                  type={showPwd ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="请输入密码"
                  autoComplete="current-password"
                  required
                  className="w-full pl-10 pr-10 py-2.5 rounded-lg bg-industrial-bg border border-industrial-border text-sm text-industrial-text placeholder:text-industrial-text-muted focus:border-industrial-primary/50 focus:outline-none focus:ring-2 focus:ring-industrial-primary/20 transition-all"
                />
                <button
                  type="button"
                  onClick={() => setShowPwd(v => !v)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-industrial-text-muted hover:text-industrial-text-secondary transition-colors"
                  tabIndex={-1}
                >
                  {showPwd ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
            </div>

            {/* 登录按钮 */}
            <button
              type="submit"
              disabled={loading || !username.trim() || !password}
              className="w-full flex items-center justify-center gap-2 rounded-lg bg-gradient-to-r from-industrial-primary to-industrial-primary-hover px-4 py-2.5 text-sm font-medium text-white shadow-lg shadow-industrial-primary/20 hover:shadow-industrial-primary/40 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            >
              {loading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  登录中...
                </>
              ) : (
                '登 录'
              )}
            </button>
          </form>

          {/* 底部提示 */}
          <div className="mt-6 pt-4 border-t border-industrial-border text-center">
            <p className="text-xs text-industrial-text-muted">
              若忘记密码，请联系管理员
            </p>
          </div>
        </div>

        {/* 版权信息 */}
        <p className="mt-4 text-center text-xs text-industrial-text-muted">
          © 2026 焊接设备 AI Agent 综合管理平台 · v2.1.0
        </p>
      </div>
    </div>
  )
}
