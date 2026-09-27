import { Link, useNavigate } from 'react-router-dom'
import CustomerForm from '../components/customers/CustomerForm'
import { api } from '../services/api'
import type {
  Customer,
  CustomerCreatePayload,
  CustomerFormValues,
} from '../types/customers'

const INITIAL_VALUES: CustomerFormValues = {
  name: '',
  document: '',
  email: '',
  phone: '',
  notes: '',
}

export default function CustomerCreatePage() {
  const navigate = useNavigate()

  async function submit(values: CustomerCreatePayload): Promise<void> {
    const created = await api.post<Customer>('/api/v1/customers', values)
    navigate(`/customers/${created.id}`, { replace: true })
  }

  function cancel(): void {
    navigate('/customers')
  }

  return (
    <section className="customer-create-page">
      <header className="page-header">
        <div>
          <h1>Novo cliente</h1>
          <p className="muted">Cadastre um novo cliente da empresa.</p>
        </div>
        <Link to="/customers">← Voltar</Link>
      </header>

      <CustomerForm
        initialValues={INITIAL_VALUES}
        submit={submit}
        submitLabel="Salvar"
        onCancel={cancel}
      />
    </section>
  )
}
