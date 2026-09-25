import type { Customer } from '../../types/customers'
import { formatDateTime } from '../../utils/format'

interface CustomerDetailProps {
  customer: Customer
}

function OptionalValue({ value }: { value: string | null }) {
  if (value === null || value === '') {
    return <span className="muted">—</span>
  }
  return <>{value}</>
}

export default function CustomerDetail({ customer }: CustomerDetailProps) {
  return (
    <div className="panel">
      <dl className="detail-list">
        <dt>ID</dt>
        <dd>{customer.id}</dd>
        <dt>Nome</dt>
        <dd>{customer.name}</dd>
        <dt>Documento</dt>
        <dd>
          <OptionalValue value={customer.document} />
        </dd>
        <dt>E-mail</dt>
        <dd>
          <OptionalValue value={customer.email} />
        </dd>
        <dt>Telefone</dt>
        <dd>
          <OptionalValue value={customer.phone} />
        </dd>
        <dt>Observações</dt>
        <dd className="detail-list__notes">
          <OptionalValue value={customer.notes} />
        </dd>
        <dt>Criado em</dt>
        <dd>{formatDateTime(customer.created_at)}</dd>
        <dt>Atualizado em</dt>
        <dd>{formatDateTime(customer.updated_at)}</dd>
      </dl>
    </div>
  )
}
