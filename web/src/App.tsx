import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { useState, useCallback } from 'react'
import AppLayout from './components/AppLayout'
import ChatPage from './pages/ChatPage'
import DevicePage from './pages/DevicePage'
import ProductionPage from './pages/ProductionPage'
import BOMPage from './pages/BOMPage'
import InventoryPage from './pages/InventoryPage'
import TracePage from './pages/TracePage'

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

  return (
    <BrowserRouter>
      <AppLayout appState={state} updateAppState={updateState}>
        <Routes>
          <Route path="/" element={<ChatPage updateAppState={updateState} />} />
          <Route path="/devices" element={<DevicePage updateAppState={updateState} />} />
          <Route path="/production" element={<ProductionPage />} />
          <Route path="/bom" element={<BOMPage />} />
          <Route path="/inventory" element={<InventoryPage />} />
          <Route path="/trace" element={<TracePage />} />
        </Routes>
      </AppLayout>
    </BrowserRouter>
  )
}
