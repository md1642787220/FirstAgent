import type { AppState } from '../App'
import { Wifi, WifiOff, AlertTriangle, Cpu, Clock, Sun, Moon, LogOut, UserCircle } from 'lucide-react'
import { useTheme } from '../contexts/ThemeContext'
import { useAuth } from '../contexts/AuthContext'

interface Props {
  appState: AppState
}

export default function TopBar({ appState }: Props) {
  const { theme, toggle } = useTheme()
  const { user, logout } = useAuth()

  return (
    <header className="fixed top-0 right-0 z-10 flex h-[52px] items-center justify-between border-b border-industrial-border bg-industrial-sidebar/80 backdrop-blur-md px-6 transition-colors duration-300" style={{ left: '240px' }}>
      {/* 左侧：LLM 连接状态 */}
      <div className="flex items-center gap-6">
        <div className="flex items-center gap-2">
          {appState.llmConnected ? (
            <>
              <Wifi className="h-4 w-4 text-industrial-success" />
              <span className="text-xs text-industrial-text-secondary">LLM 已连接</span>
            </>
          ) : (
            <>
              <WifiOff className="h-4 w-4 text-industrial-text-muted" />
              <span className="text-xs text-industrial-text-muted">LLM 未连接</span>
            </>
          )}
        </div>

        <div className="h-4 w-px bg-industrial-border"></div>

        <div className="flex items-center gap-2">
          <Cpu className="h-4 w-4 text-industrial-info" />
          <span className="text-xs text-industrial-text-secondary">
            在线设备：<span className="font-medium text-industrial-text">{appState.deviceOnline}</span> 台
          </span>
        </div>
      </div>

      {/* 右侧：当前用户 + 主题切换 + 告警数 + 时间 + 退出 */}
      <div className="flex items-center gap-6">
        {/* 当前登录用户 */}
        {user && (
          <div className="flex items-center gap-1.5">
            <UserCircle className="h-4 w-4 text-industrial-primary" />
            <span className="text-xs text-industrial-text-secondary">{user.username}</span>
          </div>
        )}

        <div className="h-4 w-px bg-industrial-border"></div>

        {/* 主题切换 */}
        <button
          onClick={toggle}
          title={theme === 'dark' ? '切换日间模式' : '切换夜间模式'}
          className="flex h-7 w-7 items-center justify-center rounded-md text-industrial-text-muted hover:bg-industrial-card-hover hover:text-industrial-accent transition-all duration-200"
        >
          {theme === 'dark' ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
        </button>

        <div className="h-4 w-px bg-industrial-border"></div>

        <div className="flex items-center gap-2">
          <AlertTriangle className={`h-4 w-4 ${appState.alertCount > 0 ? 'text-industrial-accent' : 'text-industrial-text-muted'}`} />
          <span className={`text-xs ${appState.alertCount > 0 ? 'text-industrial-accent font-medium' : 'text-industrial-text-muted'}`}>
            活跃告警：<span>{appState.alertCount}</span>
          </span>
        </div>

        <div className="h-4 w-px bg-industrial-border"></div>

        <div className="flex items-center gap-2">
          <Clock className="h-4 w-4 text-industrial-text-muted" />
          <TopBarTime />
        </div>

        <div className="h-4 w-px bg-industrial-border"></div>

        {/* 退出登录 */}
        <button
          onClick={logout}
          title="退出登录"
          className="flex h-7 w-7 items-center justify-center rounded-md text-industrial-text-muted hover:bg-industrial-danger/10 hover:text-industrial-danger transition-all duration-200"
        >
          <LogOut className="h-4 w-4" />
        </button>
      </div>
    </header>
  )
}

function TopBarTime() {
  const [time, setTime] = React.useState(new Date())

  React.useEffect(() => {
    const timer = setInterval(() => setTime(new Date()), 1000)
    return () => clearInterval(timer)
  }, [])

  return (
    <span className="text-xs text-industrial-text-secondary tabular-nums">
      {time.toLocaleTimeString('zh-CN', { hour12: false })}
    </span>
  )
}

import React from 'react'
