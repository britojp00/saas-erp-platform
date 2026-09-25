import { Link, useParams } from 'react-router-dom'
import CustomerDetail from '../components/customers/CustomerDetail'
import {
  SectionError,
  SectionLoading,
} from '../components/dashboard/SectionState'
import { useCustomer } from '../hooks/useCustomer'

export default function CustomerDetailPage() {
  const { id = '' } = useParams()
  const { customer, loading, error, notFound, retry } = useCustomer(id)

  return (
    <section className="customer-detail-page">
      <header className="page-header">
        <div>
          <h1>{customer !== null ? customer.name : 'Cliente'}</h1>
          <p className="muted">Cliente #{id}</p>
        </div>
        <Link to="/customers">← Voltar</Link>
      </header>

      {notFound ? (
        <div className="customer-missing" role="alert">
          <p>Cliente não encontrado</p>
          <Link to="/customers">Voltar para clientes</Link>
        </div>
      ) : error !== null ? (
        <SectionError message={error} onRetry={retry} />
      ) : loading && customer === null ? (
        <SectionLoading label="Carregando cliente..." />
      ) : customer !== null ? (
        <>
          {loading && (
            <p className="section-state" role="status">
              Carregando cliente...
            </p>
          )}
          <CustomerDetail customer={customer} />
        </>
      ) : null}
    </section>
  )
}
