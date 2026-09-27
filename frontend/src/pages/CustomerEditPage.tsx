import { Link, useNavigate, useParams } from 'react-router-dom'
import CustomerForm from '../components/customers/CustomerForm'
import {
  SectionError,
  SectionLoading,
} from '../components/dashboard/SectionState'
import { useCustomer } from '../hooks/useCustomer'
import { api } from '../services/api'
import type {
  Customer,
  CustomerFormValues,
  CustomerUpdatePayload,
} from '../types/customers'

function toFormValues(customer: Customer): CustomerFormValues {
  return {
    name: customer.name,
    document: customer.document ?? '',
    email: customer.email ?? '',
    phone: customer.phone ?? '',
    notes: customer.notes ?? '',
  }
}

export default function CustomerEditPage() {
  const { id = '' } = useParams()
  const navigate = useNavigate()
  const { customer, loading, error, notFound, retry } = useCustomer(id)

  async function submit(values: CustomerUpdatePayload): Promise<void> {
    await api.patch<Customer>(`/api/v1/customers/${id}`, values)
    navigate(`/customers/${id}`, { replace: true })
  }

  function cancel(): void {
    navigate(`/customers/${id}`)
  }

  return (
    <section className="customer-edit-page">
      <header className="page-header">
        <div>
          <h1>Editar cliente</h1>
          <p className="muted">Cliente #{id}</p>
        </div>
        <Link to={`/customers/${id}`}>← Voltar</Link>
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
        <CustomerForm
          key={customer.id}
          initialValues={toFormValues(customer)}
          submit={submit}
          submitLabel="Salvar"
          onCancel={cancel}
        />
      ) : null}
    </section>
  )
}
