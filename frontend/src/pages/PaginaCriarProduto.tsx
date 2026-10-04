import { Link, useNavigate } from 'react-router-dom'
import FormularioProduto from '../components/produtos/FormularioProduto'
import { api } from '../services/api'
import type {
  Produto,
  ProdutoCriarPayload,
  ValoresFormularioProduto,
} from '../types/produtos'

const INITIAL_VALUES: ValoresFormularioProduto = {
  sku: '',
  name: '',
  description: '',
  categoria_id: '',
  price: '',
  cost_price: '',
  is_active: 'true',
}

export default function PaginaCriarProduto() {
  const navigate = useNavigate()

  async function submit(values: ProdutoCriarPayload): Promise<void> {
    const created = await api.post<Produto>('/api/v1/produtos', values)
    navigate('/produtos', {
      replace: true,
      state: { feedback: `Produto "${created.name}" criado com sucesso.` },
    })
  }

  function cancel(): void {
    navigate('/produtos', { replace: true })
  }

  return (
    <section className="produto-create-page">
      <header className="page-header">
        <div>
          <h1>Novo produto</h1>
          <p className="muted">Cadastre um novo produto da empresa.</p>
        </div>
        <Link to="/produtos" replace>
          ← Voltar
        </Link>
      </header>

      <FormularioProduto
        initialValues={INITIAL_VALUES}
        submit={submit}
        submitLabel="Salvar"
        onCancel={cancel}
      />
    </section>
  )
}
