import { Link, useNavigate, useParams } from 'react-router-dom'
import FormularioCliente from '../components/clientes/FormularioCliente'
import {
  SectionError,
  SectionLoading,
} from '../components/dashboard/SectionState'
import { useCliente } from '../hooks/useCliente'
import { api } from '../services/api'
import type {
  Cliente,
  ValoresFormularioCliente,
  ClienteAtualizarPayload,
} from '../types/clientes'

function toFormValues(cliente: Cliente): ValoresFormularioCliente {
  return {
    name: cliente.name,
    document: cliente.document ?? '',
    email: cliente.email ?? '',
    phone: cliente.phone ?? '',
    notes: cliente.notes ?? '',
  }
}

export default function PaginaEditarCliente() {
  const { id = '' } = useParams()
  const navigate = useNavigate()
  const { cliente, loading, error, notFound, retry } = useCliente(id)

  async function submit(values: ClienteAtualizarPayload): Promise<void> {
    await api.patch<Cliente>(`/api/v1/clientes/${id}`, values)
    navigate('/clientes', { replace: true })
  }

  function cancel(): void {
    navigate('/clientes', { replace: true })
  }

  return (
    <section className="cliente-edit-page">
      <header className="page-header">
        <div>
          <h1>Editar cliente</h1>
          <p className="muted">Cliente #{id}</p>
        </div>
        <Link to="/clientes" replace>← Voltar</Link>
      </header>

      {notFound ? (
        <div className="cliente-missing" role="alert">
          <p>Cliente não encontrado</p>
          <Link to="/clientes">Voltar para clientes</Link>
        </div>
      ) : error !== null ? (
        <SectionError message={error} onRetry={retry} />
      ) : loading && cliente === null ? (
        <SectionLoading label="Carregando cliente..." />
      ) : cliente !== null ? (
        <FormularioCliente
          key={cliente.id}
          initialValues={toFormValues(cliente)}
          submit={submit}
          submitLabel="Salvar"
          onCancel={cancel}
        />
      ) : null}
    </section>
  )
}
