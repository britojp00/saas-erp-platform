import type { AsyncState } from '../../hooks/useDashboardData'
import { STATUS_PEDIDOS, ROTULOS_STATUS_PEDIDO } from '../../types/dashboard'
import type { PedidoResumo, StatusPedido } from '../../types/dashboard'
import { formatAmount, formatDateTime } from '../../utils/format'
import { SectionError, SectionLoading } from './SectionState'

interface PedidosRecentesProps {
  state: AsyncState<PedidoResumo[]>
  onRetry: () => void
}

function ehStatusPedido(value: string): value is StatusPedido {
  return (STATUS_PEDIDOS as readonly string[]).includes(value)
}

function statusLabel(status: string): string {
  return ehStatusPedido(status) ? ROTULOS_STATUS_PEDIDO[status] : status
}

function statusClass(status: string): string {
  return `badge badge--${status.toLowerCase()}`
}

export default function PedidosRecentes({ state, onRetry }: PedidosRecentesProps) {
  return (
    <section className="panel" aria-labelledby="pedidos-recentes-title">
      <h2 id="pedidos-recentes-title">Pedidos recentes</h2>
      {state.status === 'loading' && (
        <SectionLoading label="Carregando pedidos..." />
      )}
      {state.status === 'error' && (
        <SectionError message={state.message} onRetry={onRetry} />
      )}
      {state.status === 'ready' &&
        (state.data.length === 0 ? (
          <p className="empty-state">Nenhum pedido registrado.</p>
        ) : (
          <ul className="feed-list">
            {state.data.map((pedido) => (
              <li key={pedido.id} className="feed-item">
                <div className="feed-item__main">
                  <span className="feed-item__title">
                    Pedido #{pedido.numero_pedido}
                  </span>
                  <span className={statusClass(pedido.status)}>
                    {statusLabel(pedido.status)}
                  </span>
                </div>
                <div className="feed-item__meta">
                  <span>{formatDateTime(pedido.created_at)}</span>
                  <span>{formatAmount(pedido.total_amount)}</span>
                </div>
              </li>
            ))}
          </ul>
        ))}
    </section>
  )
}
