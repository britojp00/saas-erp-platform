import type { AsyncState } from '../../hooks/useDashboardData'
import { ORDER_STATUSES, ORDER_STATUS_LABELS } from '../../types/dashboard'
import type { OrderListItem, OrderStatus } from '../../types/dashboard'
import { formatAmount, formatDateTime } from '../../utils/format'
import { SectionError, SectionLoading } from './SectionState'

interface RecentOrdersProps {
  state: AsyncState<OrderListItem[]>
  onRetry: () => void
}

function isOrderStatus(value: string): value is OrderStatus {
  return (ORDER_STATUSES as readonly string[]).includes(value)
}

function statusLabel(status: string): string {
  return isOrderStatus(status) ? ORDER_STATUS_LABELS[status] : status
}

function statusClass(status: string): string {
  return `badge badge--${status.toLowerCase()}`
}

export default function RecentOrders({ state, onRetry }: RecentOrdersProps) {
  return (
    <section className="panel" aria-labelledby="recent-orders-title">
      <h2 id="recent-orders-title">Pedidos recentes</h2>
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
            {state.data.map((order) => (
              <li key={order.id} className="feed-item">
                <div className="feed-item__main">
                  <span className="feed-item__title">
                    Pedido #{order.order_number}
                  </span>
                  <span className={statusClass(order.status)}>
                    {statusLabel(order.status)}
                  </span>
                </div>
                <div className="feed-item__meta">
                  <span>{formatDateTime(order.created_at)}</span>
                  <span>{formatAmount(order.total_amount)}</span>
                </div>
              </li>
            ))}
          </ul>
        ))}
    </section>
  )
}
