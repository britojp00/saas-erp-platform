import { Link, useNavigate, useParams } from 'react-router-dom'
import FormularioProduto from '../components/produtos/FormularioProduto'
import {
  SectionError,
  SectionLoading,
} from '../components/dashboard/SectionState'
import { useProduto } from '../hooks/useProduto'
import { api } from '../services/api'
import type {
  Produto,
  ProdutoAtualizarPayload,
  ValoresFormularioProduto,
} from '../types/produtos'

function toFormValues(produto: Produto): ValoresFormularioProduto {
  return {
    sku: produto.sku,
    name: produto.name,
    description: produto.description ?? '',
    categoria_id:
      produto.categoria_id === null ? '' : String(produto.categoria_id),
    price: produto.price.replace('.', ','),
    cost_price: produto.cost_price?.replace('.', ',') ?? '',
    is_active: produto.is_active ? 'true' : 'false',
  }
}

export default function PaginaEditarProduto() {
  const { id = '' } = useParams()
  const navigate = useNavigate()
  const { produto, loading, error, notFound, retry } = useProduto(id)

  async function submit(values: ProdutoAtualizarPayload): Promise<void> {
    const updated = await api.patch<Produto>(`/api/v1/produtos/${id}`, values)
    navigate('/produtos', {
      replace: true,
      state: { feedback: `Produto "${updated.name}" atualizado com sucesso.` },
    })
  }

  function cancel(): void {
    navigate('/produtos', { replace: true })
  }

  return (
    <section className="produto-edit-page">
      <header className="page-header">
        <div>
          <h1>Editar produto</h1>
          <p className="muted">Produto #{id}</p>
        </div>
        <Link to="/produtos" replace>
          ← Voltar
        </Link>
      </header>

      {notFound ? (
        <div className="produto-missing" role="alert">
          <p>Produto não encontrado</p>
          <Link to="/produtos">Voltar para produtos</Link>
        </div>
      ) : error !== null ? (
        <SectionError message={error} onRetry={retry} />
      ) : loading && produto === null ? (
        <SectionLoading label="Carregando produto..." />
      ) : produto !== null ? (
        <FormularioProduto
          key={produto.id}
          initialValues={toFormValues(produto)}
          submit={submit}
          submitLabel="Salvar"
          onCancel={cancel}
        />
      ) : null}
    </section>
  )
}
