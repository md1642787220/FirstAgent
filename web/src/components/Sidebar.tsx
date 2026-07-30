import { NavLink, useLocation } from 'react-router-dom'
import { 
  MessageSquare, 
  Activity, 
  ClipboardList, 
  PackageOpen, 
  Warehouse, 
  GitBranch,
  Zap
} from 'lucide-react'

const navItems = [
  { path: '/', label: 'AI 对话', icon: MessageSquare },
  { path: '/devices', label: '设备监控', icon: Activity },
  { path: '/production', label: '生产进度', icon: ClipboardList },
  { path: '/bom', label: 'BOM 管理', icon: PackageOpen },
  { path: '/inventory', label: '库存分析', icon: Warehouse },
  { path: '/trace', label: '执行轨迹', icon: GitBranch },
]

export default function Sidebar() {
  const location = useLocation()

  return (
    <aside className="flex w-60 flex-col border-r border-industrial-border bg-industrial-sidebar">
      {/* Logo 区域 */}
      <div className="flex h-16 items-center gap-3 border-b border-industrial-border px-5">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-br from-industrial-primary to-blue-600 shadow-lg shadow-industrial-primary/20">
          <Zap className="h-5 w-5 text-white" />
        </div>
        <div className="flex flex-col">
          <span className="text-sm font-semibold text-industrial-text leading-tight">焊接设备AI平台</span>
          <span className="text-[11px] text-industrial-text-muted leading-tight">Welding Agent v1.0</span>
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
                  ? 'bg-industrial-primary/10 text-industrial-primary border-l-2 border-industrial-primary'
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
