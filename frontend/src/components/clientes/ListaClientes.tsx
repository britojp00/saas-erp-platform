import { Link } from 'react-router-dom'
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
}: ListaClientesProps) {
  return (
    <div className="table-wrap">
      <table className="clientes-table">
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
          {items.map((cliente) => (
            <tr key={cliente.id}>
              <td>{cliente.id}</td>
              <td>
                <Link to={`/clientes/${cliente.id}`}>{cliente.name}</Link>
              </td>
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
          ))}
        </tbody>
      </table>
    </div>
  )
}
