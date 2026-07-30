import { ReactNode } from 'react'
import Sidebar from './Sidebar'
import TopBar from './TopBar'
import type { AppState } from '../App'

interface Props {
  children: ReactNode
  appState: AppState
  updateAppState: (updates: Partial<AppState>) => void
}

export default function AppLayout({ children, appState, updateAppState }: Props) {
  return (
    <div className="flex h-screen w-screen overflow-hidden bg-industrial-bg">
      {/* 左侧导航栏 */}
      <Sidebar />
      {/* 右侧主区域 */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* 顶部状态栏 */}
        <TopBar appState={appState} />
        {/* 内容区 */}
        <main className="flex-1 overflow-auto p-6 pt-[72px]">
          {children}
        </main>
      </div>
    </div>
  )
}
