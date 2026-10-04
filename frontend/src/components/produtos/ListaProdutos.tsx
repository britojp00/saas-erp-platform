import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { IconCheck, IconEdit, IconTrash, IconX } from '@tabler/icons-react'
import type { Categoria } from '../../types/categorias'
import type {
  CampoOrdenacaoProduto,
  Produto,
  SortOrder,
} from '../../types/produtos'
import { formatAmount, formatDateTime } from '../../utils/format'

interface ListaProdutosProps {
  items: Produto[]
  categorias: Categoria[]
  sort: CampoOrdenacaoProduto
  order: SortOrder
  onSort: (field: CampoOrdenacaoProduto) => void
  deletingId: number | null
  onRemove: (produto: Produto) => void
}

interface SortableHeaderProps {
  field: CampoOrdenacaoProduto
  label: string
  sort: CampoOrdenacaoProduto
  order: SortOrder
  onSort: (field: CampoOrdenacaoProduto) => void
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
        className="produtos-table__sort"
        aria-label={`Ordenar por ${label}`}
        onClick={() => onSort(field)}
      >
        {label}
        {active && (
          <span className="produtos-table__sort-mark" aria-hidden="true">
            {order === 'asc' ? '↑' : '↓'}
          </span>
        )}
      </button>
    </th>
  )
}

function categoriaLabel(
  produto: Produto,
  categorias: Categoria[],
): string | null {
  if (produto.categoria_id === null) return null
  const categoria = categorias.find(
    (item) => item.id === produto.categoria_id,
  )
  return categoria?.name ?? null
}

export default function ListaProdutos({
  items,
  categorias,
  sort,
  order,
  onSort,
  deletingId,
  onRemove,
}: ListaProdutosProps) {
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
      <table className="produtos-table">
        <thead>
          <tr>
            <th scope="col">Ações</th>
            <th scope="col">ID</th>
            <SortableHeader
              field="sku"
              label="SKU"
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
            <th scope="col">Categoria</th>
            <SortableHeader
              field="price"
              label="Preço"
              sort={sort}
              order={order}
              onSort={onSort}
            />
            <SortableHeader
              field="is_active"
              label="Situação"
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
          {items.map((produto) => {
            const confirmando = confirmingId === produto.id
            const excluindo = deletingId === produto.id
            const categoria = categoriaLabel(produto, categorias)

            return (
              <tr key={produto.id}>
                <td>
                  <div
                    className="produtos-table__actions"
                    role="group"
                    aria-label={`Ações do produto ${produto.name}`}
                  >
                    {confirmando ? (
                      <>
                        <span
                          className="produtos-table__confirm-text"
                          role="status"
                        >
                          Excluir {produto.name}?
                        </span>
                        <button
                          ref={confirmButtonRef}
                          type="button"
                          className="produtos-table__action produtos-table__action--danger"
                          aria-label={`Confirmar exclusão de ${produto.name}`}
                          onClick={(event) => {
                            const container =
                              event.currentTarget.closest<HTMLElement>(
                                '.produtos-table__actions',
                              )
                            setConfirmingId(null)
                            onRemove(produto)
                            restoreFocusToExcluir(container)
                          }}
                        >
                          <IconCheck size={16} aria-hidden="true" />
                          Confirmar
                        </button>
                        <button
                          type="button"
                          className="produtos-table__action"
                          onClick={(event) => {
                            const container =
                              event.currentTarget.closest<HTMLElement>(
                                '.produtos-table__actions',
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
                          className="produtos-table__action"
                          to={`/produtos/${produto.id}/editar`}
                        >
                          <IconEdit size={16} aria-hidden="true" />
                          Editar
                        </Link>
                        <button
                          type="button"
                          className="produtos-table__action produtos-table__action--danger"
                          disabled={excluindo}
                          aria-busy={excluindo}
                          aria-label={`Excluir produto ${produto.name}`}
                          onClick={() => setConfirmingId(produto.id)}
                        >
                          {excluindo ? (
                            <>
                              <span
                                className="produtos-table__spinner"
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
                <td>{produto.id}</td>
                <td>{produto.sku}</td>
                <td>{produto.name}</td>
                <td>
                  {categoria !== null ? (
                    <>{categoria}</>
                  ) : (
                    <span className="muted">—</span>
                  )}
                </td>
                <td>{formatAmount(Number(produto.price))}</td>
                <td>
                  {produto.is_active ? (
                    'Ativo'
                  ) : (
                    <span className="muted">Inativo</span>
                  )}
                </td>
                <td>{formatDateTime(produto.created_at)}</td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
