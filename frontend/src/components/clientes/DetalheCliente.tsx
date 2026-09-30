import type { Cliente } from '../../types/clientes'
import { formatDateTime } from '../../utils/format'

interface DetalheClienteProps {
  cliente: Cliente
}

function OptionalValue({ value }: { value: string | null }) {
  if (value === null || value === '') {
    return <span className="muted">—</span>
  }
  return <>{value}</>
}

export default function DetalheCliente({ cliente }: DetalheClienteProps) {
  return (
    <div className="panel">
      <dl className="detail-list">
        <dt>ID</dt>
        <dd>{cliente.id}</dd>
        <dt>Nome</dt>
        <dd>{cliente.name}</dd>
        <dt>Documento</dt>
        <dd>
          <OptionalValue value={cliente.document} />
        </dd>
        <dt>E-mail</dt>
        <dd>
          <OptionalValue value={cliente.email} />
        </dd>
        <dt>Telefone</dt>
        <dd>
          <OptionalValue value={cliente.phone} />
        </dd>
        <dt>Observações</dt>
        <dd className="detail-list__notes">
          <OptionalValue value={cliente.notes} />
        </dd>
        <dt>Criado em</dt>
        <dd>{formatDateTime(cliente.created_at)}</dd>
        <dt>Atualizado em</dt>
        <dd>{formatDateTime(cliente.updated_at)}</dd>
      </dl>
    </div>
  )
}
