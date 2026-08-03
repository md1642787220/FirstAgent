import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { useState, useCallback, useEffect } from 'react'
import { ThemeProvider } from './contexts/ThemeContext'
import AppLayout from './components/AppLayout'
import ChatPage from './pages/ChatPage'
import DevicePage from './pages/DevicePage'
import ProductionPage from './pages/ProductionPage'
import BOMPage from './pages/BOMPage'
import InventoryPage from './pages/InventoryPage'
import TracePage from './pages/TracePage'
import KnowledgePage from './pages/KnowledgePage'
import TroubleShootPage from './pages/TroubleShootPage'
import api from './services/http'

export interface AppState {
  llmConnected: boolean
  deviceOnline: number
  alertCount: number
}

export default function App() {
  const [state, setState] = useState<AppState>({
    llmConnected: false,
    deviceOnline: 0,
    alertCount: 0,
  })

  const updateState = useCallback((updates: Partial<AppState>) => {
    setState(prev => ({ ...prev, ...updates }))
  }, [])

  // 检查后端连接状态（未连接时自动重试）
  useEffect(() => {
    let cancelled = false

    const checkHealth = async () => {
      try {
        await api.health()
        if (!cancelled) updateState({ llmConnected: true })
        return true
      } catch {
        if (!cancelled) updateState({ llmConnected: false })
        return false
      }
    }

    // 立即检查一次
    checkHealth()

    // 未连接时每 3 秒重试，连接成功后停止
    const timer = setInterval(async () => {
      const ok = await checkHealth()
      if (ok) clearInterval(timer)
    }, 3000)

    return () => {
      cancelled = true
      clearInterval(timer)
    }
  }, [updateState])

  return (
    <BrowserRouter>
      <ThemeProvider>
        <AppLayout appState={state} updateAppState={updateState}>
          <Routes>
            <Route path="/" element={<ChatPage updateAppState={updateState} />} />
            <Route path="/devices" element={<DevicePage updateAppState={updateState} />} />
            <Route path="/production" element={<ProductionPage />} />
            <Route path="/bom" element={<BOMPage />} />
            <Route path="/inventory" element={<InventoryPage />} />
            <Route path="/trace" element={<TracePage />} />
            <Route path="/troubleshoot" element={<TroubleShootPage />} />
            <Route path="/knowledge" element={<KnowledgePage />} />
          </Routes>
        </AppLayout>
      </ThemeProvider>
    </BrowserRouter>
  )
}
