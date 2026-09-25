import type { AsyncState } from '../../hooks/useDashboardData'
import type { AuditLogItem } from '../../types/dashboard'
import { formatDateTime } from '../../utils/format'
import { SectionError, SectionLoading } from './SectionState'

interface RecentActivityProps {
  state: AsyncState<AuditLogItem[]>
  onRetry: () => void
}

export default function RecentActivity({
  state,
  onRetry,
}: RecentActivityProps) {
  return (
    <section className="panel" aria-labelledby="recent-activity-title">
      <h2 id="recent-activity-title">Atividade recente</h2>
      {state.status === 'loading' && (
        <SectionLoading label="Carregando atividades..." />
      )}
      {state.status === 'error' && (
        <SectionError message={state.message} onRetry={onRetry} />
      )}
      {state.status === 'ready' &&
        (state.data.length === 0 ? (
          <p className="empty-state">Nenhuma atividade registrada.</p>
        ) : (
          <ul className="feed-list">
            {state.data.map((entry) => (
              <li key={entry.id} className="feed-item">
                <div className="feed-item__main">
                  <span className="feed-item__title">{entry.action}</span>
                  <span className="feed-item__tag">{entry.entity_type}</span>
                </div>
                <div className="feed-item__meta">
                  <span>{formatDateTime(entry.created_at)}</span>
                  {entry.user_id !== null && <span>Usuário {entry.user_id}</span>}
                </div>
              </li>
            ))}
          </ul>
        ))}
    </section>
  )
}
