import RecentActivity from '../components/dashboard/RecentActivity'
import PedidosRecentes from '../components/dashboard/PedidosRecentes'
import SummaryPanel from '../components/dashboard/SummaryPanel'
import { useAuth } from '../contexts/AuthContext'
import { useDashboardData } from '../hooks/useDashboardData'

export default function DashboardPage() {
  const { user } = useAuth()
  const { summary, pedidosRecentes, recentActivity, retry } = useDashboardData()

  const contextLabel =
    user === null
      ? 'Visão geral da operação'
      : `Empresa ${user.empresa_id}${
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
        <PedidosRecentes
          state={pedidosRecentes}
          onRetry={() => retry('pedidos')}
        />
        <RecentActivity
          state={recentActivity}
          onRetry={() => retry('activity')}
        />
      </div>
    </section>
  )
}
