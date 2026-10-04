import { useEffect, useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import BuscaProduto from '../components/produtos/BuscaProduto'
import ListaProdutos from '../components/produtos/ListaProdutos'
import Pagination from '../components/clientes/Pagination'
import {
  SectionError,
  SectionLoading,
} from '../components/dashboard/SectionState'
import { useProdutos } from '../hooks/useProdutos'
import { api } from '../services/api'
import type { Categoria, ListaCategoriasResposta } from '../types/categorias'

const CATEGORIAS_OPTIONS_QUERY =
  '/api/v1/categorias?page=1&page_size=100&sort=name&order=asc'

interface FeedbackNavigation {
  feedback?: unknown
}

export default function PaginaListaProdutos() {
  const location = useLocation()
  const navigate = useNavigate()
  const [flash] = useState<string | null>(() => {
    const state = location.state as FeedbackNavigation | null
    return typeof state?.feedback === 'string' ? state.feedback : null
  })
  const [categorias, setCategorias] = useState<Categoria[]>([])

  const {
    data,
    loading,
    error,
    deletingId,
    feedback,
    search,
    sort,
    order,
    setPage,
    setSearch,
    toggleSort,
    retry,
    remove,
    dismissFeedback,
  } = useProdutos()

  useEffect(() => {
    if (location.state !== null) {
      navigate(location.pathname, { replace: true })
    }
  }, [location.state, location.pathname, navigate])

  useEffect(() => {
    let cancelado = false

    async function loadCategorias(): Promise<void> {
      try {
        const response = await api.get<ListaCategoriasResposta>(
          CATEGORIAS_OPTIONS_QUERY,
        )
        if (!cancelado) setCategorias(response.items)
      } catch {
        if (!cancelado) setCategorias([])
      }
    }

    void loadCategorias()
    return () => {
      cancelado = true
    }
  }, [])

  return (
    <section className="produtos-page">
      <header className="page-header">
        <div>
          <h1>Produtos</h1>
          <p className="muted">Gestão de produtos da empresa autenticada.</p>
        </div>
        <Link className="button-link" to="/produtos/criar">
          Novo produto
        </Link>
      </header>

      <div className="produtos-toolbar">
        <BuscaProduto value={search} onChange={setSearch} />
        {loading && data !== null && (
          <p className="section-state" role="status">
            Carregando produtos...
          </p>
        )}
      </div>

      {flash !== null && (
        <p className="section-state" role="status">
          {flash}
        </p>
      )}

      {feedback !== null &&
        (feedback.tone === 'sucesso' ? (
          <p className="section-state" role="status">
            {feedback.text}
          </p>
        ) : (
          <div className="section-error" role="alert">
            <p>{feedback.text}</p>
            <button type="button" onClick={dismissFeedback}>
              Fechar
            </button>
          </div>
        ))}

      {error !== null ? (
        <SectionError message={error} onRetry={retry} />
      ) : data === null ? (
        <SectionLoading label="Carregando produtos..." />
      ) : data.items.length === 0 ? (
        loading ? null : (
          <p className="empty-state">
            {search !== ''
              ? `Nenhum resultado para '${search}'`
              : 'Nenhum produto cadastrado'}
          </p>
        )
      ) : (
        <>
          <ListaProdutos
            items={data.items}
            categorias={categorias}
            sort={sort}
            order={order}
            onSort={toggleSort}
            deletingId={deletingId}
            onRemove={remove}
          />
          <Pagination
            page={data.page}
            pageSize={data.page_size}
            total={data.total}
            onPageChange={setPage}
          />
        </>
      )}
    </section>
  )
}
