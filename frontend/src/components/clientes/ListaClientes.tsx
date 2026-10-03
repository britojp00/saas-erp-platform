import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { IconCheck, IconEdit, IconTrash, IconX } from '@tabler/icons-react'
import type {
  Cliente,
  CampoOrdenacaoCliente,
  SortOrder,
} from '../../types/clientes'
import { formatDateTime } from '../../utils/format'

interface ListaClientesProps {
  items: Cliente[]
  sort: CampoOrdenacaoCliente
  order: SortOrder
  onSort: (field: CampoOrdenacaoCliente) => void
  deletingId: number | null
  onRemove: (cliente: Cliente) => void
}

interface SortableHeaderProps {
  field: CampoOrdenacaoCliente
  label: string
  sort: CampoOrdenacaoCliente
  order: SortOrder
  onSort: (field: CampoOrdenacaoCliente) => void
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
        className="clientes-table__sort"
        aria-label={`Ordenar por ${label}`}
        onClick={() => onSort(field)}
      >
        {label}
        {active && (
          <span className="clientes-table__sort-mark" aria-hidden="true">
            {order === 'asc' ? '↑' : '↓'}
          </span>
        )}
      </button>
    </th>
  )
}

function OptionalValue({ value }: { value: string | null }) {
  if (value === null || value === '') {
    return <span className="muted">—</span>
  }
  return <>{value}</>
}

export default function ListaClientes({
  items,
  sort,
  order,
  onSort,
  deletingId,
  onRemove,
}: ListaClientesProps) {
  const [confirmingId, setConfirmingId] = useState<number | null>(null)
  const confirmButtonRef = useRef<HTMLButtonElement | null>(null)

  useEffect(() => {
    setConfirmingId(null)
  }, [items])

  useEffect(() => {
    if (confirmingId !== null) {
      confirmButtonRef.current?.focus()
    }
  }, [confirmingId])

  function restoreFocusToExcluir(container: HTMLElement | null) {
    requestAnimationFrame(() => {
      container
        ?.querySelector<HTMLButtonElement>('button:last-of-type')
        ?.focus()
    })
  }

  return (
    <div className="table-wrap">
      <table className="clientes-table">
        <thead>
          <tr>
            <th scope="col">Ações</th>
            <SortableHeader
              field="id"
              label="ID"
              sort={sort}
              order={order}
              onSort={onSort}
            />
            <SortableHeader
              field="name"
              label="Nome"
              sort={sort}
              order={order}
              onSort={onSort}
            />
            <th scope="col">Documento</th>
            <th scope="col">E-mail</th>
            <th scope="col">Telefone</th>
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
          {items.map((cliente) => {
            const confirmando = confirmingId === cliente.id
            const excluindo = deletingId === cliente.id

            return (
              <tr key={cliente.id}>
                <td>
                  <div
                    className="clientes-table__actions"
                    role="group"
                    aria-label={`Ações do cliente ${cliente.name}`}
                  >
                    {confirmando ? (
                      <>
                        <span
                          className="clientes-table__confirm-text"
                          role="status"
                        >
                          Excluir {cliente.name}?
                        </span>
                        <button
                          ref={confirmButtonRef}
                          type="button"
                          className="clientes-table__action clientes-table__action--danger"
                          aria-label={`Confirmar exclusão de ${cliente.name}`}
                          onClick={(event) => {
                            const container =
                              event.currentTarget.closest<HTMLElement>(
                                '.clientes-table__actions',
                              )
                            setConfirmingId(null)
                            onRemove(cliente)
                            restoreFocusToExcluir(container)
                          }}
                        >
                          <IconCheck size={16} aria-hidden="true" />
                          Confirmar
                        </button>
                        <button
                          type="button"
                          className="clientes-table__action"
                          onClick={(event) => {
                            const container =
                              event.currentTarget.closest<HTMLElement>(
                                '.clientes-table__actions',
                              )
                            setConfirmingId(null)
                            restoreFocusToExcluir(container)
                          }}
                        >
                          <IconX size={16} aria-hidden="true" />
                          Cancelar
                        </button>
                      </>
                    ) : (
                      <>
                        <Link
                          className="clientes-table__action"
                          to={`/clientes/${cliente.id}/editar`}
                        >
                          <IconEdit size={16} aria-hidden="true" />
                          Editar
                        </Link>
                        <button
                          type="button"
                          className="clientes-table__action clientes-table__action--danger"
                          disabled={excluindo}
                          aria-busy={excluindo}
                          aria-label={`Excluir cliente ${cliente.name}`}
                          onClick={() => setConfirmingId(cliente.id)}
                        >
                          {excluindo ? (
                            <>
                              <span
                                className="clientes-table__spinner"
                                aria-hidden="true"
                              />
                              Excluindo...
                            </>
                          ) : (
                            <>
                              <IconTrash size={16} aria-hidden="true" />
                              Excluir
                            </>
                          )}
                        </button>
                      </>
                    )}
                  </div>
                </td>
                <td>{cliente.id}</td>
                <td>{cliente.name}</td>
                <td>
                  <OptionalValue value={cliente.document} />
                </td>
                <td>
                  <OptionalValue value={cliente.email} />
                </td>
                <td>
                  <OptionalValue value={cliente.phone} />
                </td>
                <td>{formatDateTime(cliente.created_at)}</td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
