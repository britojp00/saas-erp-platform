import type { AsyncState } from '../../hooks/useDashboardData'
import {
  ORDER_STATUSES,
  ORDER_STATUS_LABELS,
} from '../../types/dashboard'
import type { DashboardSummary } from '../../types/dashboard'
import { formatNumber, formatPercent } from '../../utils/format'
import { SectionError, SectionLoading } from './SectionState'
import StatCard from './StatCard'

interface SummaryPanelProps {
  state: AsyncState<DashboardSummary>
  onRetry: () => void
}

export default function SummaryPanel({ state, onRetry }: SummaryPanelProps) {
  if (state.status === 'loading') {
    return <SectionLoading label="Carregando indicadores..." />
  }

  if (state.status === 'error') {
    return <SectionError message={state.message} onRetry={onRetry} />
  }

  const data = state.data
  const { inventory } = data

  return (
    <>
      <div className="stat-grid">
        <StatCard
          label="Clientes"
          value={formatNumber(data.customersTotal)}
        />
        <StatCard
          label="Produtos"
          value={formatNumber(data.productsTotal)}
          hint={`${formatNumber(data.activeProductsTotal)} ativos`}
        />
        <StatCard
          label="Pedidos"
          value={formatNumber(data.ordersTotal)}
          hint={`${formatNumber(data.ordersByStatus.DRAFT)} em rascunho`}
        />
        <StatCard
          label="Registros de estoque"
          value={formatNumber(inventory.total)}
          hint={
            inventory.available !== null
              ? `${formatNumber(inventory.available)} disponíveis`
              : 'somas indisponíveis'
          }
        />
      </div>

      <div className="panel-grid">
        <section className="panel" aria-labelledby="orders-by-status-title">
          <h2 id="orders-by-status-title">Pedidos por situação</h2>
          <ul className="status-list">
            {ORDER_STATUSES.map((status) => {
              const count = data.ordersByStatus[status]
              const ratio =
                data.ordersTotal > 0 ? count / data.ordersTotal : 0
              return (
                <li key={status} className="status-row">
                  <div className="status-row__head">
                    <span>{ORDER_STATUS_LABELS[status]}</span>
                    <span className="status-row__count">
                      {formatNumber(count)}
                      <span className="status-row__percent">
                        {formatPercent(ratio)}
                      </span>
                    </span>
                  </div>
                  <div
                    className="status-row__track"
                    role="presentation"
                    aria-hidden="true"
                  >
                    <div
                      className={`status-row__fill status-row__fill--${status.toLowerCase()}`}
                      style={{ width: `${Math.round(ratio * 100)}%` }}
                    />
                  </div>
                </li>
              )
            })}
            {data.ordersUnclassified > 0 && (
              <li className="status-row">
                <div className="status-row__head">
                  <span>Outros</span>
                  <span className="status-row__count">
                    {formatNumber(data.ordersUnclassified)}
                  </span>
                </div>
              </li>
            )}
          </ul>
        </section>

        <section className="panel" aria-labelledby="stock-title">
          <h2 id="stock-title">Estoque</h2>
          <dl className="metric-list">
            <dt>Registros</dt>
            <dd>{formatNumber(inventory.total)}</dd>
            <dt>Em estoque</dt>
            <dd>
              {inventory.quantity !== null
                ? formatNumber(inventory.quantity)
                : '—'}
            </dd>
            <dt>Reservado</dt>
            <dd>
              {inventory.reserved !== null
                ? formatNumber(inventory.reserved)
                : '—'}
            </dd>
            <dt>Disponível</dt>
            <dd>
              {inventory.available !== null
                ? formatNumber(inventory.available)
                : '—'}
            </dd>
            <dt>Movimentações</dt>
            <dd>{formatNumber(data.movementsTotal)}</dd>
            <dt>Reservas</dt>
            <dd>{formatNumber(data.reservationsTotal)}</dd>
          </dl>
          {!inventory.complete && (
            <p className="muted section-note">
              Somas de quantidade não exibidas: a lista de estoque excede o
              limite de leitura do dashboard.
            </p>
          )}
        </section>
      </div>
    </>
  )
}
