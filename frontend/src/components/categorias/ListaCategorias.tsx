import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { IconCheck, IconEdit, IconTrash, IconX } from '@tabler/icons-react'
import type {
  CampoOrdenacaoCategoria,
  Categoria,
  SortOrder,
} from '../../types/categorias'
import { formatDateTime } from '../../utils/format'

interface ListaCategoriasProps {
  items: Categoria[]
  sort: CampoOrdenacaoCategoria
  order: SortOrder
  onSort: (field: CampoOrdenacaoCategoria) => void
  deletingId: number | null
  onRemove: (categoria: Categoria) => void
}

interface SortableHeaderProps {
  field: CampoOrdenacaoCategoria
  label: string
  sort: CampoOrdenacaoCategoria
  order: SortOrder
  onSort: (field: CampoOrdenacaoCategoria) => void
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
        className="categorias-table__sort"
        aria-label={`Ordenar por ${label}`}
        onClick={() => onSort(field)}
      >
        {label}
        {active && (
          <span className="categorias-table__sort-mark" aria-hidden="true">
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

export default function ListaCategorias({
  items,
  sort,
  order,
  onSort,
  deletingId,
  onRemove,
}: ListaCategoriasProps) {
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
      <table className="categorias-table">
        <thead>
          <tr>
            <th scope="col">Ações</th>
            <th scope="col">ID</th>
            <SortableHeader
              field="name"
              label="Nome"
              sort={sort}
              order={order}
              onSort={onSort}
            />
            <th scope="col">Descrição</th>
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
          {items.map((categoria) => {
            const confirmando = confirmingId === categoria.id
            const excluindo = deletingId === categoria.id

            return (
              <tr key={categoria.id}>
                <td>
                  <div
                    className="categorias-table__actions"
                    role="group"
                    aria-label={`Ações da categoria ${categoria.name}`}
                  >
                    {confirmando ? (
                      <>
                        <span
                          className="categorias-table__confirm-text"
                          role="status"
                        >
                          Excluir {categoria.name}?
                        </span>
                        <button
                          ref={confirmButtonRef}
                          type="button"
                          className="categorias-table__action categorias-table__action--danger"
                          aria-label={`Confirmar exclusão de ${categoria.name}`}
                          onClick={(event) => {
                            const container =
                              event.currentTarget.closest<HTMLElement>(
                                '.categorias-table__actions',
                              )
                            setConfirmingId(null)
                            onRemove(categoria)
                            restoreFocusToExcluir(container)
                          }}
                        >
                          <IconCheck size={16} aria-hidden="true" />
                          Confirmar
                        </button>
                        <button
                          type="button"
                          className="categorias-table__action"
                          onClick={(event) => {
                            const container =
                              event.currentTarget.closest<HTMLElement>(
                                '.categorias-table__actions',
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
                          className="categorias-table__action"
                          to={`/categorias/${categoria.id}/editar`}
                        >
                          <IconEdit size={16} aria-hidden="true" />
                          Editar
                        </Link>
                        <button
                          type="button"
                          className="categorias-table__action categorias-table__action--danger"
                          disabled={excluindo}
                          aria-busy={excluindo}
                          aria-label={`Excluir categoria ${categoria.name}`}
                          onClick={() => setConfirmingId(categoria.id)}
                        >
                          {excluindo ? (
                            <>
                              <span
                                className="categorias-table__spinner"
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
                <td>{categoria.id}</td>
                <td>{categoria.name}</td>
                <td>
                  <OptionalValue value={categoria.description} />
                </td>
                <td>{formatDateTime(categoria.created_at)}</td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
