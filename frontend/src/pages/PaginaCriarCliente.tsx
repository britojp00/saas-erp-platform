import { Link, useNavigate } from 'react-router-dom'
import FormularioCliente from '../components/clientes/FormularioCliente'
import { api } from '../services/api'
import type {
  Cliente,
  ClienteCriarPayload,
  ValoresFormularioCliente,
} from '../types/clientes'

const INITIAL_VALUES: ValoresFormularioCliente = {
  name: '',
  document: '',
  email: '',
  phone: '',
  notes: '',
}

export default function PaginaCriarCliente() {
  const navigate = useNavigate()

  async function submit(values: ClienteCriarPayload): Promise<void> {
    const created = await api.post<Cliente>('/api/v1/clientes', values)
    navigate(`/clientes/${created.id}`, { replace: true })
  }

  function cancel(): void {
    navigate('/clientes')
  }

  return (
    <section className="cliente-create-page">
      <header className="page-header">
        <div>
          <h1>Novo cliente</h1>
          <p className="muted">Cadastre um novo cliente da empresa.</p>
        </div>
        <Link to="/clientes">← Voltar</Link>
      </header>

      <FormularioCliente
        initialValues={INITIAL_VALUES}
        submit={submit}
        submitLabel="Salvar"
        onCancel={cancel}
      />
    </section>
  )
}
