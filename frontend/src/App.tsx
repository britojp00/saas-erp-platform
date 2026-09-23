import { useEffect, useState } from 'react'
import { api } from './services/api'

interface HealthResponse {
  status: string
  service: string
}

type ApiStatus = 'checking' | 'online' | 'offline'

export default function App() {
  const [apiStatus, setApiStatus] = useState<ApiStatus>('checking')

  useEffect(() => {
    let active = true

    api
      .get<HealthResponse>('/health')
      .then(() => {
        if (active) setApiStatus('online')
      })
      .catch(() => {
        if (active) setApiStatus('offline')
      })

    return () => {
      active = false
    }
  }, [])

  return (
    <main className="app">
      <h1>SaaS ERP Platform</h1>
      <p>Frontend inicial — React + TypeScript + Vite.</p>
      <p className="muted">Fase 2.2: API client e ambiente.</p>
      <p>
        API:{' '}
        {apiStatus === 'checking' && 'verificando...'}
        {apiStatus === 'online' && 'online'}
        {apiStatus === 'offline' && 'indisponível'}
      </p>
    </main>
  )
}
