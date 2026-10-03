import { Link } from 'react-router-dom'
import ListaCategorias from '../components/categorias/ListaCategorias'
import BuscaCategoria from '../components/categorias/BuscaCategoria'
import Pagination from '../components/clientes/Pagination'
import { SectionError, SectionLoading } from '../components/dashboard/SectionState'
import { useCategorias } from '../hooks/useCategorias'

export default function PaginaListaCategorias() {
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
  } = useCategorias()

  return (
    <section className="categorias-page">
      <header className="page-header">
        <div>
          <h1>Categorias</h1>
          <p className="muted">Gestão de categorias da empresa autenticada.</p>
        </div>
        <Link className="button-link" to="/categorias/criar">
          Nova categoria
        </Link>
      </header>

      <div className="categorias-toolbar">
        <BuscaCategoria value={search} onChange={setSearch} />
        {loading && data !== null && (
          <p className="section-state" role="status">
            Carregando categorias...
          </p>
        )}
      </div>

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
        <SectionLoading label="Carregando categorias..." />
      ) : data.items.length === 0 ? (
        loading ? null : (
          <p className="empty-state">
            {search !== ''
              ? `Nenhum resultado para '${search}'`
              : 'Nenhuma categoria cadastrada'}
          </p>
        )
      ) : (
        <>
          <ListaCategorias
            items={data.items}
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
