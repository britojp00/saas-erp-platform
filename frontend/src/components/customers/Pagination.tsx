import { formatNumber } from '../../utils/format'

interface PaginationProps {
  page: number
  pageSize: number
  total: number
  onPageChange: (page: number) => void
}

export default function Pagination({
  page,
  pageSize,
  total,
  onPageChange,
}: PaginationProps) {
  const totalPages = Math.max(1, Math.ceil(total / pageSize))
  const firstItem = (page - 1) * pageSize + 1
  const lastItem = Math.min(page * pageSize, total)

  return (
    <nav className="pagination" aria-label="Paginação de clientes">
      <p className="pagination__info">
        {formatNumber(firstItem)}–{formatNumber(lastItem)} de{' '}
        {formatNumber(total)} · Página {page} de {totalPages}
      </p>
      <div className="pagination__actions">
        <button
          type="button"
          onClick={() => onPageChange(page - 1)}
          disabled={page <= 1}
        >
          Anterior
        </button>
        <button
          type="button"
          onClick={() => onPageChange(page + 1)}
          disabled={page >= totalPages}
        >
          Próxima
        </button>
      </div>
    </nav>
  )
}
