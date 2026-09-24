import { useState } from 'react'
import { Outlet } from 'react-router-dom'
import AppHeader from '../components/AppHeader'
import AppSidebar from '../components/AppSidebar'

export default function AppLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false)

  return (
    <div className="app-shell">
      <AppSidebar
        open={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />
      <div className="app-shell__main">
        <AppHeader
          onToggleSidebar={() => setSidebarOpen((current) => !current)}
        />
        <main className="app-content">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
