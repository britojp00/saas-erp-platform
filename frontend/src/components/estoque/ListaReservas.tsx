import { useEffect, useRef, useState } from 'react'
import { IconArrowBackUp, IconCheck, IconX } from '@tabler/icons-react'
import type {
  AcaoReserva,
  ReservaEstoque,
} from '../../types/estoque'
import type { Produto } from '../../types/produtos'
import { formatDateTime, formatQuantity } from '../../utils/format'

interface ListaReservasProps {
  items: ReservaEstoque[]
  produtos: Produto[]
  actingId: number | null
  onAction: (reserva: ReservaEstoque, acao: AcaoReserva) => void
}

const ROTULOS_ACAO: Record<AcaoReserva, string> = {
  confirmar: 'Confirmar',
  liberar: 'Liberar',
  cancelar: 'Cancelar',
}

const ROTULOS_ANDAMENTO: Record<AcaoReserva, string> = {
  confirmar: 'Confirmando...',
  liberar: 'Liberando...',
  cancelar: 'Cancelando...',
}

function produtoLabel(
  reserva: ReservaEstoque,
  produtos: Produto[],
): string {
  const produto = produtos.find((item) => item.id === reserva.produto_id)
  if (produto !== undefined) return produto.name
  return `Produto #${reserva.produto_id}`
}

interface ConfirmacaoState {
  id: number
  acao: AcaoReserva
}

export default function ListaReservas({
  items,
  produtos,
  actingId,
  onAction,
}: ListaReservasProps) {
  const [confirming, setConfirming] = useState<ConfirmacaoState | null>(null)
  const confirmButtonRef = useRef<HTMLButtonElement | null>(null)
  const triggerRef = useRef<HTMLElement | null>(null)

  useEffect(() => {
    setConfirming(null)
  }, [items])

  useEffect(() => {
    if (confirming !== null) {
      confirmButtonRef.current?.focus()
    }
  }, [confirming])

  function restoreFocus(): void {
    const trigger = triggerRef.current
    triggerRef.current = null
    requestAnimationFrame(() => {
      if (trigger !== null && trigger.isConnected) trigger.focus()
    })
  }

  function closeConfirm(): void {
    setConfirming(null)
    restoreFocus()
  }

  return (
    <div className="table-wrap">
      <table className="estoque-table">
        <thead>
          <tr>
            <th scope="col">Ações</th>
            <th scope="col">ID</th>
            <th scope="col">Produto</th>
            <th scope="col">Quantidade</th>
            <th scope="col">Status</th>
            <th scope="col">Referência</th>
            <th scope="col">Pedido item</th>
            <th scope="col">Reservado em</th>
            <th scope="col">Confirmado em</th>
            <th scope="col">Liberado em</th>
          </tr>
        </thead>
        <tbody>
          {items.map((reserva) => {
            const confirmando =
              confirming !== null && confirming.id === reserva.id
            const aplicando = actingId === reserva.id

            return (
              <tr key={reserva.id}>
                <td>
                  <div
                    className="estoque-table__actions"
                    role="group"
                    aria-label={`Ações da reserva ${reserva.id}`}
                  >
                    {confirmando && confirming !== null ? (
                      <>
                        <span
                          className="estoque-table__confirm-text"
                          role="status"
                        >
                          {ROTULOS_ACAO[confirming.acao]} reserva #{reserva.id}?
                        </span>
                        <button
                          ref={confirmButtonRef}
                          type="button"
                          className="estoque-table__action"
                          disabled={aplicando}
                          aria-busy={aplicando}
                          aria-label={`${ROTULOS_ACAO[confirming.acao]} reserva ${reserva.id}`}
                          onClick={() => onAction(reserva, confirming.acao)}
                        >
                          {aplicando ? (
                            <>
                              <span
                                className="estoque-table__spinner"
                                aria-hidden="true"
                              />
                              {ROTULOS_ANDAMENTO[confirming.acao]}
                            </>
                          ) : (
                            <>
                              <IconCheck size={16} aria-hidden="true" />
                              {ROTULOS_ACAO[confirming.acao]}
                            </>
                          )}
                        </button>
                        <button
                          type="button"
                          className="estoque-table__action"
                          disabled={aplicando}
                          onClick={closeConfirm}
                        >
                          <IconX size={16} aria-hidden="true" />
                          Cancelar
                        </button>
                      </>
                    ) : reserva.status === 'ATIVA' ? (
                      <>
                        <button
                          type="button"
                          className="estoque-table__action"
                          disabled={actingId !== null}
                          aria-label={`Confirmar reserva ${reserva.id}`}
                          onClick={(event) => {
                            triggerRef.current = event.currentTarget
                            setConfirming({ id: reserva.id, acao: 'confirmar' })
                          }}
                        >
                          <IconCheck size={16} aria-hidden="true" />
                          Confirmar
                        </button>
                        <button
                          type="button"
                          className="estoque-table__action"
                          disabled={actingId !== null}
                          aria-label={`Liberar reserva ${reserva.id}`}
                          onClick={(event) => {
                            triggerRef.current = event.currentTarget
                            setConfirming({ id: reserva.id, acao: 'liberar' })
                          }}
                        >
                          <IconArrowBackUp size={16} aria-hidden="true" />
                          Liberar
                        </button>
                        <button
                          type="button"
                          className="estoque-table__action"
                          disabled={actingId !== null}
                          aria-label={`Cancelar reserva ${reserva.id}`}
                          onClick={(event) => {
                            triggerRef.current = event.currentTarget
                            setConfirming({ id: reserva.id, acao: 'cancelar' })
                          }}
                        >
                          <IconX size={16} aria-hidden="true" />
                          Cancelar
                        </button>
                      </>
                    ) : (
                      <span className="muted">—</span>
                    )}
                  </div>
                </td>
                <td>{reserva.id}</td>
                <td>{produtoLabel(reserva, produtos)}</td>
                <td>{formatQuantity(reserva.quantity)}</td>
                <td>
                  <span className={`badge badge--${reserva.status.toLowerCase()}`}>
                    {reserva.status.charAt(0) + reserva.status.slice(1).toLowerCase()}
                  </span>
                </td>
                <td>
                  {reserva.reference !== null ? (
                    <>{reserva.reference}</>
                  ) : (
                    <span className="muted">—</span>
                  )}
                </td>
                <td>
                  {reserva.pedido_item_id !== null ? (
                    <>{reserva.pedido_item_id}</>
                  ) : (
                    <span className="muted">—</span>
                  )}
                </td>
                <td>{formatDateTime(reserva.reserved_at)}</td>
                <td>
                  {reserva.confirmed_at !== null ? (
                    <>{formatDateTime(reserva.confirmed_at)}</>
                  ) : (
                    <span className="muted">—</span>
                  )}
                </td>
                <td>
                  {reserva.released_at !== null ? (
                    <>{formatDateTime(reserva.released_at)}</>
                  ) : (
                    <span className="muted">—</span>
                  )}
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
