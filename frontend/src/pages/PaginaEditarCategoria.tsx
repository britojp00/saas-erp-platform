import { Link, useNavigate, useParams } from 'react-router-dom'
import FormularioCategoria from '../components/categorias/FormularioCategoria'
import {
  SectionError,
  SectionLoading,
} from '../components/dashboard/SectionState'
import { useCategoria } from '../hooks/useCategoria'
import { api } from '../services/api'
import type {
  Categoria,
  CategoriaAtualizarPayload,
  ValoresFormularioCategoria,
} from '../types/categorias'

function toFormValues(categoria: Categoria): ValoresFormularioCategoria {
  return {
    name: categoria.name,
    description: categoria.description ?? '',
    parent_id: categoria.parent_id === null ? '' : String(categoria.parent_id),
  }
}

export default function PaginaEditarCategoria() {
  const { id = '' } = useParams()
  const navigate = useNavigate()
  const { categoria, loading, error, notFound, retry } = useCategoria(id)

  async function submit(values: CategoriaAtualizarPayload): Promise<void> {
    await api.patch<Categoria>(`/api/v1/categorias/${id}`, values)
    navigate('/categorias', { replace: true })
  }

  function cancel(): void {
    navigate('/categorias', { replace: true })
  }

  return (
    <section className="categoria-edit-page">
      <header className="page-header">
        <div>
          <h1>Editar categoria</h1>
          <p className="muted">Categoria #{id}</p>
        </div>
        <Link to="/categorias" replace>
          ← Voltar
        </Link>
      </header>

      {notFound ? (
        <div className="categoria-missing" role="alert">
          <p>Categoria não encontrada</p>
          <Link to="/categorias">Voltar para categorias</Link>
        </div>
      ) : error !== null ? (
        <SectionError message={error} onRetry={retry} />
      ) : loading && categoria === null ? (
        <SectionLoading label="Carregando categoria..." />
      ) : categoria !== null ? (
        <FormularioCategoria
          key={categoria.id}
          initialValues={toFormValues(categoria)}
          submit={submit}
          submitLabel="Salvar"
          onCancel={cancel}
          excludeId={categoria.id}
        />
      ) : null}
    </section>
  )
}
