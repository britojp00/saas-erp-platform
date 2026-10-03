import { Link, useNavigate } from 'react-router-dom'
import FormularioCategoria from '../components/categorias/FormularioCategoria'
import { api } from '../services/api'
import type {
  Categoria,
  CategoriaCriarPayload,
  ValoresFormularioCategoria,
} from '../types/categorias'

const INITIAL_VALUES: ValoresFormularioCategoria = {
  name: '',
  description: '',
  parent_id: '',
}

export default function PaginaCriarCategoria() {
  const navigate = useNavigate()

  async function submit(values: CategoriaCriarPayload): Promise<void> {
    await api.post<Categoria>('/api/v1/categorias', values)
    navigate('/categorias', { replace: true })
  }

  function cancel(): void {
    navigate('/categorias', { replace: true })
  }

  return (
    <section className="categoria-create-page">
      <header className="page-header">
        <div>
          <h1>Nova categoria</h1>
          <p className="muted">Cadastre uma nova categoria da empresa.</p>
        </div>
        <Link to="/categorias" replace>
          ← Voltar
        </Link>
      </header>

      <FormularioCategoria
        initialValues={INITIAL_VALUES}
        submit={submit}
        submitLabel="Salvar"
        onCancel={cancel}
      />
    </section>
  )
}
