import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { IconCheck, IconEdit, IconEye, IconX } from '@tabler/icons-react'
import type { Cliente } from '../../types/clientes'
import type {
  AcaoPedido,
  CampoOrdenacaoPedido,
  PedidoResumo,
  SortOrder,
} from '../../types/pedidos'
import {
  ROTULOS_ACAO_PEDIDO,
  SUBSTANTIVOS_ACAO_PEDIDO,
  acoesDoPedido,
  badgeStatusPedido,
  rotuloStatusPedido,
} from '../../types/pedidos'
import { formatAmount, formatDateTime } from '../../utils/format'

interface ListaPedidosProps {
  items: PedidoResumo[]
  clientes: Cliente[]
  sort: CampoOrdenacaoPedido
  order: SortOrder
  onSort: (field: CampoOrdenacaoPedido) => void
  actingId: number | null
  onAcao: (pedido: PedidoResumo, acao: AcaoPedido) => void
}

interface SortableHeaderProps {
  field: CampoOrdenacaoPedido
  label: string
  sort: CampoOrdenacaoPedido
  order: SortOrder
  onSort: (field: CampoOrdenacaoPedido) => void
}

function SortableHeader({
  field,
  label,
  sort,
  order,
  onSort,
}: SortableHeaderProps) {
  const active = sort === field
  const ariaSort = active
    ? order === 'asc'
      ? 'ascending'
      : 'descending'
    : 'none'

  return (
    <th scope="col" aria-sort={ariaSort}>
      <button
        type="button"
        className="pedidos-table__sort"
        aria-label={`Ordenar por ${label}`}
        onClick={() => onSort(field)}
      >
        {label}
        {active && (
          <span className="pedidos-table__sort-mark" aria-hidden="true">
            {order === 'asc' ? '↑' : '↓'}
          </span>
        )}
      </button>
    </th>
  )
}

function clienteLabel(pedido: PedidoResumo, clientes: Cliente[]): string {
  const cliente = clientes.find((item) => item.id === pedido.cliente_id)
  return cliente?.name ?? `Cliente #${pedido.cliente_id}`
}

export default function ListaPedidos({
  items,
  clientes,
  sort,
  order,
  onSort,
  actingId,
  onAcao,
}: ListaPedidosProps) {
  const [confirmation, setConfirmation] = useState<{
    id: number
    acao: AcaoPedido
  } | null>(null)
  const confirmButtonRef = useRef<HTMLButtonElement | null>(null)

  useEffect(() => {
    setConfirmation(null)
  }, [items])

  useEffect(() => {
    if (confirmation !== null) {
      confirmButtonRef.current?.focus()
    }
  }, [confirmation])

  function restoreFocus(container: HTMLElement | null) {
    requestAnimationFrame(() => {
      container
        ?.querySelector<HTMLButtonElement>('button:last-of-type')
        ?.focus()
    })
  }

  return (
    <div className="table-wrap">
      <table className="pedidos-table">
        <thead>
          <tr>
            <th scope="col">Ações</th>
            <SortableHeader
              field="numero_pedido"
              label="Número"
              sort={sort}
              order={order}
              onSort={onSort}
            />
            <th scope="col">Cliente</th>
            <SortableHeader
              field="status"
              label="Status"
              sort={sort}
              order={order}
              onSort={onSort}
            />
            <SortableHeader
              field="total_amount"
              label="Total"
              sort={sort}
              order={order}
              onSort={onSort}
            />
            <SortableHeader
              field="created_at"
              label="Criado em"
              sort={sort}
              order={order}
              onSort={onSort}
            />
          </tr>
        </thead>
        <tbody>
          {items.map((pedido) => {
            const acoes = acoesDoPedido(pedido.status)
            const rascunho = pedido.status === 'RASCUNHO'
            const aguardando = actingId === pedido.id
            const confirmando = confirmation?.id === pedido.id
            const acao = confirmando ? confirmation.acao : null

            return (
              <tr key={pedido.id}>
                <td>
                  <div
                    className="pedidos-table__actions"
                    role="group"
                    aria-label={`Ações do pedido #${pedido.numero_pedido}`}
                  >
                    {confirmando && acao !== null ? (
                      <>
                        <span
                          className="pedidos-table__confirm-text"
                          role="status"
                        >
                          {ROTULOS_ACAO_PEDIDO[acao]} pedido #{pedido.numero_pedido}?
                        </span>
                        <button
                          ref={confirmButtonRef}
                          type="button"
                          className={
                            acao === 'cancelar'
                              ? 'pedidos-table__action pedidos-table__action--danger'
                              : 'pedidos-table__action'
                          }
                          aria-label={`Confirmar a ${SUBSTANTIVOS_ACAO_PEDIDO[acao]} do pedido ${pedido.numero_pedido}`}
                          onClick={(event) => {
                            const container =
                              event.currentTarget.closest<HTMLElement>(
                                '.pedidos-table__actions',
                              )
                            setConfirmation(null)
                            onAcao(pedido, acao)
                            restoreFocus(container)
                          }}
                        >
                          <IconCheck size={16} aria-hidden="true" />
                          Confirmar
                        </button>
                        <button
                          type="button"
                          className="pedidos-table__action"
                          aria-label={`Descartar a ${SUBSTANTIVOS_ACAO_PEDIDO[acao]} do pedido ${pedido.numero_pedido}`}
                          onClick={(event) => {
                            const container =
                              event.currentTarget.closest<HTMLElement>(
                                '.pedidos-table__actions',
                              )
                            setConfirmation(null)
                            restoreFocus(container)
                          }}
                        >
                          <IconX size={16} aria-hidden="true" />
                          Cancelar
                        </button>
                      </>
                    ) : (
                      <>
                        <Link
                          className="pedidos-table__action"
                          to={`/pedidos/${pedido.id}`}
                        >
                          {rascunho ? (
                            <>
                              <IconEdit size={16} aria-hidden="true" />
                              Editar
                            </>
                          ) : (
                            <>
                              <IconEye size={16} aria-hidden="true" />
                              Abrir
                            </>
                          )}
                        </Link>
                        {acoes.map((item) => (
                          <button
                            key={item}
                            type="button"
                            className={
                              item === 'cancelar'
                                ? 'pedidos-table__action pedidos-table__action--danger'
                                : 'pedidos-table__action'
                            }
                            disabled={aguardando}
                            aria-busy={aguardando}
                            aria-label={`${ROTULOS_ACAO_PEDIDO[item]} pedido ${pedido.numero_pedido}`}
                            onClick={() =>
                              setConfirmation({ id: pedido.id, acao: item })
                            }
                          >
                            {aguardando ? (
                              <>
                                <span
                                  className="pedidos-table__spinner"
                                  aria-hidden="true"
                                />
                                Processando...
                              </>
                            ) : item === 'cancelar' ? (
                              <>
                                <IconX size={16} aria-hidden="true" />
                                {ROTULOS_ACAO_PEDIDO[item]}
                              </>
                            ) : (
                              <>
                                <IconCheck size={16} aria-hidden="true" />
                                {ROTULOS_ACAO_PEDIDO[item]}
                              </>
                            )}
                          </button>
                        ))}
                      </>
                    )}
                  </div>
                </td>
                <td>#{pedido.numero_pedido}</td>
                <td>{clienteLabel(pedido, clientes)}</td>
                <td>
                  <span className={badgeStatusPedido(pedido.status)}>
                    {rotuloStatusPedido(pedido.status)}
                  </span>
                </td>
                <td>{formatAmount(pedido.total_amount)}</td>
                <td>{formatDateTime(pedido.created_at)}</td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
