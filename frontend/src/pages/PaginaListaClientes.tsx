import { Link } from 'react-router-dom'
import ListaClientes from '../components/clientes/ListaClientes'
import BuscaCliente from '../components/clientes/BuscaCliente'
import Pagination from '../components/clientes/Pagination'
import { SectionError, SectionLoading } from '../components/dashboard/SectionState'
import { useClientes } from '../hooks/useClientes'

export default function PaginaListaClientes() {
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
  } = useClientes()

  return (
    <section className="clientes-page">
      <header className="page-header">
        <div>
          <h1>Clientes</h1>
          <p className="muted">Gestão de clientes da empresa autenticada.</p>
        </div>
        <Link className="button-link" to="/clientes/criar">
          Novo cliente
        </Link>
      </header>

      <div className="clientes-toolbar">
        <BuscaCliente value={search} onChange={setSearch} />
        {loading && data !== null && (
          <p className="section-state" role="status">
            Carregando clientes...
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
        <SectionLoading label="Carregando clientes..." />
      ) : data.items.length === 0 ? (
        loading ? null : (
          <p className="empty-state">
            {search !== ''
              ? `Nenhum resultado para '${search}'`
              : 'Nenhum cliente cadastrado'}
          </p>
        )
      ) : (
        <>
          <ListaClientes
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
