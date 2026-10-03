import { Link, useParams } from 'react-router-dom'
import DetalheCliente from '../components/clientes/DetalheCliente'
import {
  SectionError,
  SectionLoading,
} from '../components/dashboard/SectionState'
import { useCliente } from '../hooks/useCliente'

export default function PaginaDetalheCliente() {
  const { id = '' } = useParams()
  const { cliente, loading, error, notFound, retry } = useCliente(id)

  return (
    <section className="cliente-detail-page">
      <header className="page-header">
        <div>
          <h1>{cliente !== null ? cliente.name : 'Cliente'}</h1>
          <p className="muted">Cliente #{id}</p>
        </div>
        <div className="page-header__actions">
          {cliente !== null && (
            <Link
              className="button-link"
              to={`/clientes/${cliente.id}/editar`}
            >
              Editar
            </Link>
          )}
          <Link to="/clientes">← Voltar</Link>
        </div>
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
        <>
          {loading && (
            <p className="section-state" role="status">
              Carregando cliente...
            </p>
          )}
          <DetalheCliente cliente={cliente} />
        </>
      ) : null}
    </section>
  )
}
