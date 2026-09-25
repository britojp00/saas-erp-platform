import RecentActivity from '../components/dashboard/RecentActivity'
import RecentOrders from '../components/dashboard/RecentOrders'
import SummaryPanel from '../components/dashboard/SummaryPanel'
import { useAuth } from '../contexts/AuthContext'
import { useDashboardData } from '../hooks/useDashboardData'

export default function DashboardPage() {
  const { user } = useAuth()
  const { summary, recentOrders, recentActivity, retry } = useDashboardData()

  const contextLabel =
    user === null
      ? 'Visão geral da operação'
      : `Tenant ${user.tenant_id}${
          user.roles.length > 0 ? ` · ${user.roles.join(', ')}` : ''
        }`

  return (
    <section className="dashboard-page">
      <header className="page-header">
        <div>
          <h1>Dashboard</h1>
          <p className="muted">{contextLabel}</p>
        </div>
      </header>

      <SummaryPanel state={summary} onRetry={() => retry('summary')} />

      <div className="panel-grid">
        <RecentOrders state={recentOrders} onRetry={() => retry('orders')} />
        <RecentActivity
          state={recentActivity}
          onRetry={() => retry('activity')}
        />
      </div>
    </section>
  )
}
