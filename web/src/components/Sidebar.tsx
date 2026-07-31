import { NavLink, useLocation } from 'react-router-dom'
import {
  MessageSquare,
  Activity,
  ClipboardList,
  PackageOpen,
  Warehouse,
  GitBranch,
  BookOpen,
  Wrench,
} from 'lucide-react'

const navItems = [
  { path: '/', label: 'AI 对话', icon: MessageSquare },
  { path: '/devices', label: '设备监控', icon: Activity },
  { path: '/production', label: '生产进度', icon: ClipboardList },
  { path: '/bom', label: 'BOM 管理', icon: PackageOpen },
  { path: '/inventory', label: '库存分析', icon: Warehouse },
  { path: '/trace', label: '执行轨迹', icon: GitBranch },
  { path: '/troubleshoot', label: '故障排查', icon: Wrench },
  { path: '/knowledge', label: '知识库', icon: BookOpen },
]

export default function Sidebar() {
  const location = useLocation()

  return (
    <aside className="flex w-60 flex-col border-r border-industrial-border bg-industrial-sidebar">
      {/* Logo 区域 */}
      <div className="flex flex-col items-center gap-2 border-b border-industrial-border px-4 py-3">
        <img
          src="/xg-logo.png"
          alt="XG Logo"
          className="h-9 w-full object-contain"
        />
        <div className="flex items-baseline gap-1.5 leading-tight">
          <span className="text-[13px] font-semibold text-industrial-text">XG Agent</span>
          <span className="text-[11px] text-industrial-accent font-medium">v2.1.0</span>
        </div>
      </div>

      {/* 导航菜单 */}
      <nav className="mt-4 flex-1 space-y-1 px-3">
        {navItems.map((item) => {
          const isActive = location.pathname === item.path || 
            (item.path !== '/' && location.pathname.startsWith(item.path))
          const Icon = item.icon

          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={`group flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-200 ${
                isActive
                  ? 'bg-gradient-to-r from-industrial-primary/15 to-industrial-accent/10 text-industrial-primary border-l-2 border-industrial-accent'
                  : 'text-industrial-text-secondary hover:bg-industrial-card hover:text-industrial-text border-l-2 border-transparent'
              }`}
            >
              <Icon className={`h-[18px] w-[18px] transition-colors ${
                isActive ? 'text-industrial-primary' : 'text-industrial-text-muted group-hover:text-industrial-text-secondary'
              }`} />
              <span>{item.label}</span>
            </NavLink>
          )
        })}
      </nav>

      {/* 底部状态 */}
      <div className="border-t border-industrial-border p-4">
        <div className="flex items-center gap-2 text-xs text-industrial-text-muted">
          <span className="relative flex h-2 w-2">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-industrial-success opacity-75"></span>
            <span className="relative inline-flex h-2 w-2 rounded-full bg-industrial-success"></span>
          </span>
          系统运行中
        </div>
      </div>
    </aside>
  )
}
