import { useEffect, useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import BuscaPedido from '../components/pedidos/BuscaPedido'
import ListaPedidos from '../components/pedidos/ListaPedidos'
import Pagination from '../components/clientes/Pagination'
import {
  SectionError,
  SectionLoading,
} from '../components/dashboard/SectionState'
import { usePedidos } from '../hooks/usePedidos'
import { api } from '../services/api'
import type { Cliente, ListaClientesResposta } from '../types/clientes'
import { ROTULOS_STATUS_PEDIDO, STATUS_PEDIDOS } from '../types/pedidos'

const CLIENTES_OPTIONS_QUERY =
  '/api/v1/clientes?page=1&page_size=100&sort=name&order=asc'

interface FeedbackNavigation {
  feedback?: unknown
}

export default function PaginaPedidos() {
  const location = useLocation()
  const navigate = useNavigate()
  const [flash] = useState<string | null>(() => {
    const state = location.state as FeedbackNavigation | null
    return typeof state?.feedback === 'string' ? state.feedback : null
  })
  const [clientes, setClientes] = useState<Cliente[]>([])

  const {
    data,
    loading,
    error,
    actingId,
    feedback,
    search,
    status,
    sort,
    order,
    setPage,
    setSearch,
    setStatus,
    toggleSort,
    retry,
    executarAcao,
    dismissFeedback,
  } = usePedidos()

  useEffect(() => {
    if (location.state !== null) {
      navigate(location.pathname, { replace: true })
    }
  }, [location.state, location.pathname, navigate])

  useEffect(() => {
    let cancelado = false

    async function loadClientes(): Promise<void> {
      try {
        const response = await api.get<ListaClientesResposta>(
          CLIENTES_OPTIONS_QUERY,
        )
        if (!cancelado) setClientes(response.items)
      } catch {
        if (!cancelado) setClientes([])
      }
    }

    void loadClientes()
    return () => {
      cancelado = true
    }
  }, [])

  function emptyMessage(): string {
    if (search !== '') return `Nenhum resultado para '${search}'`
    if (status !== '') return 'Nenhum pedido com o status selecionado'
    return 'Nenhum pedido cadastrado'
  }

  return (
    <section className="pedidos-page">
      <header className="page-header">
        <div>
          <h1>Pedidos</h1>
          <p className="muted">Pedidos, itens e ciclo de vida do pedido.</p>
        </div>
        <Link className="button-link" to="/pedidos/criar">
          Novo pedido
        </Link>
      </header>

      <div className="pedidos-toolbar">
        <div className="pedidos-filters">
          <BuscaPedido value={search} onChange={setSearch} />
          <div className="field pedidos-filtro">
            <label htmlFor="pedido-status">Filtrar por status</label>
            <select
              id="pedido-status"
              value={status}
              onChange={(event) => setStatus(event.target.value)}
            >
              <option value="">Todos os status</option>
              {STATUS_PEDIDOS.map((item) => (
                <option key={item} value={item}>
                  {ROTULOS_STATUS_PEDIDO[item]}
                </option>
              ))}
            </select>
          </div>
        </div>
        {loading && data !== null && (
          <p className="section-state" role="status">
            Carregando pedidos...
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
        <SectionLoading label="Carregando pedidos..." />
      ) : data.itens.length === 0 ? (
        loading ? null : (
          <p className="empty-state">{emptyMessage()}</p>
        )
      ) : (
        <>
          <ListaPedidos
            items={data.itens}
            clientes={clientes}
            sort={sort}
            order={order}
            onSort={toggleSort}
            actingId={actingId}
            onAcao={executarAcao}
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
