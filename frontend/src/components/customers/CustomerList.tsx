import { Link } from 'react-router-dom'
import type {
  Customer,
  CustomerSortField,
  SortOrder,
} from '../../types/customers'
import { formatDateTime } from '../../utils/format'

interface CustomerListProps {
  items: Customer[]
  sort: CustomerSortField
  order: SortOrder
  onSort: (field: CustomerSortField) => void
}

interface SortableHeaderProps {
  field: CustomerSortField
  label: string
  sort: CustomerSortField
  order: SortOrder
  onSort: (field: CustomerSortField) => void
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
        className="customers-table__sort"
        aria-label={`Ordenar por ${label}`}
        onClick={() => onSort(field)}
      >
        {label}
        {active && (
          <span className="customers-table__sort-mark" aria-hidden="true">
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

export default function CustomerList({
  items,
  sort,
  order,
  onSort,
}: CustomerListProps) {
  return (
    <div className="table-wrap">
      <table className="customers-table">
        <thead>
          <tr>
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
          {items.map((customer) => (
            <tr key={customer.id}>
              <td>{customer.id}</td>
              <td>
                <Link to={`/customers/${customer.id}`}>{customer.name}</Link>
              </td>
              <td>
                <OptionalValue value={customer.document} />
              </td>
              <td>
                <OptionalValue value={customer.email} />
              </td>
              <td>
                <OptionalValue value={customer.phone} />
              </td>
              <td>{formatDateTime(customer.created_at)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
