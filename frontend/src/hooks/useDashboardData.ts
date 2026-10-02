import { useCallback, useEffect, useRef, useState } from 'react'
import { ApiError, api } from '../services/api'
import { STATUS_PEDIDOS } from '../types/dashboard'
import type {
  AuditLogItem,
  DashboardSummary,
  ItemEstoque,
  ResumoEstoque,
  ListaPedidosResposta,
  PedidoResumo,
  PaginatedResponse,
} from '../types/dashboard'

const TAMANHO_PAGINA_ESTOQUE = 100
const MAX_PAGINAS_ESTOQUE = 10
const RECENT_LIMIT = 5

export type AsyncState<T> =
  | { status: 'loading' }
  | { status: 'error'; message: string }
  | { status: 'ready'; data: T }

export type DashboardSection = 'summary' | 'pedidos' | 'activity'

function errorMessage(error: unknown): string {
  if (error instanceof ApiError) return error.message
  return 'Não foi possível carregar os dados da API.'
}

async function fetchResumoEstoque(): Promise<ResumoEstoque> {
  const first = await api.get<PaginatedResponse<ItemEstoque>>(
    `/api/v1/estoque?page=1&page_size=${TAMANHO_PAGINA_ESTOQUE}`,
  )

  let items = first.items

  if (items.length < first.total) {
    const remainingPages =
      Math.min(
        Math.ceil(first.total / TAMANHO_PAGINA_ESTOQUE),
        MAX_PAGINAS_ESTOQUE,
      ) - 1

    const pages = await Promise.all(
      Array.from({ length: remainingPages }, (_, index) =>
        api.get<PaginatedResponse<ItemEstoque>>(
          `/api/v1/estoque?page=${index + 2}&page_size=${TAMANHO_PAGINA_ESTOQUE}`,
        ),
      ),
    )

    items = items.concat(...pages.map((page) => page.items))
  }

  const complete = items.length >= first.total

  if (!complete) {
    return {
      total: first.total,
      complete: false,
      quantity: null,
      reserved: null,
      available: null,
    }
  }

  let quantity = 0
  let reserved = 0
  for (const item of items) {
    quantity += Number(item.quantity)
    reserved += Number(item.reserved_quantity)
  }

  return {
    total: first.total,
    complete: true,
    quantity,
    reserved,
    available: quantity - reserved,
  }
}

async function fetchSummary(): Promise<DashboardSummary> {
  const [
    clientesRes,
    produtosRes,
    activeProdutosRes,
    pedidosRes,
    rascunhoRes,
    confirmadoRes,
    concluidoRes,
    canceladoRes,
    estoqueRes,
    movimentosRes,
    reservasRes,
  ] = await Promise.all([
    api.get<PaginatedResponse<unknown>>(
      '/api/v1/clientes?page=1&page_size=1',
    ),
    api.get<PaginatedResponse<unknown>>('/api/v1/produtos?page=1&page_size=1'),
    api.get<PaginatedResponse<unknown>>(
      '/api/v1/produtos?page=1&page_size=1&is_active=true',
    ),
    api.get<PaginatedResponse<unknown>>('/api/v1/pedidos?page=1&page_size=1'),
    api.get<PaginatedResponse<unknown>>(
      '/api/v1/pedidos?page=1&page_size=1&status=RASCUNHO',
    ),
    api.get<PaginatedResponse<unknown>>(
      '/api/v1/pedidos?page=1&page_size=1&status=CONFIRMADO',
    ),
    api.get<PaginatedResponse<unknown>>(
      '/api/v1/pedidos?page=1&page_size=1&status=CONCLUIDO',
    ),
    api.get<PaginatedResponse<unknown>>(
      '/api/v1/pedidos?page=1&page_size=1&status=CANCELADO',
    ),
    fetchResumoEstoque(),
    api.get<PaginatedResponse<unknown>>(
      '/api/v1/estoque/movimentacoes/list?page=1&page_size=1',
    ),
    api.get<PaginatedResponse<unknown>>(
      '/api/v1/estoque/reservas/list?page=1&page_size=1',
    ),
  ])

  const pedidosPorStatus = {
    RASCUNHO: rascunhoRes.total,
    CONFIRMADO: confirmadoRes.total,
    CONCLUIDO: concluidoRes.total,
    CANCELADO: canceladoRes.total,
  }

  const classified = STATUS_PEDIDOS.reduce(
    (sum, status) => sum + pedidosPorStatus[status],
    0,
  )

  return {
    clientesTotal: clientesRes.total,
    produtosTotal: produtosRes.total,
    produtosAtivosTotal: activeProdutosRes.total,
    pedidosTotal: pedidosRes.total,
    pedidosPorStatus,
    pedidosNaoClassificados: Math.max(pedidosRes.total - classified, 0),
    estoque: estoqueRes,
    movimentosTotal: movimentosRes.total,
    reservasTotal: reservasRes.total,
  }
}

async function buscarPedidosRecentes(): Promise<PedidoResumo[]> {
  const response = await api.get<ListaPedidosResposta<PedidoResumo>>(
    `/api/v1/pedidos?page=1&page_size=${RECENT_LIMIT}&sort=created_at&order=desc`,
  )
  return response.itens
}

async function fetchRecentActivity(): Promise<AuditLogItem[]> {
  const response = await api.get<PaginatedResponse<AuditLogItem>>(
    `/api/v1/audit-logs?page=1&page_size=${RECENT_LIMIT}&sort=created_at&order=desc`,
  )
  return response.items
}

export function useDashboardData() {
  const [summary, setSummary] = useState<AsyncState<DashboardSummary>>({
    status: 'loading',
  })
  const [pedidosRecentes, setPedidosRecentes] = useState<
    AsyncState<PedidoResumo[]>
  >({ status: 'loading' })
  const [recentActivity, setRecentActivity] = useState<
    AsyncState<AuditLogItem[]>
  >({ status: 'loading' })

  const sequence = useRef({ summary: 0, pedidos: 0, activity: 0 })

  const loadSummary = useCallback(async () => {
    const current = ++sequence.current.summary
    setSummary({ status: 'loading' })
    try {
      const data = await fetchSummary()
      if (current === sequence.current.summary) setSummary({ status: 'ready', data })
    } catch (error) {
      if (current === sequence.current.summary) {
        setSummary({ status: 'error', message: errorMessage(error) })
      }
    }
  }, [])

  const carregarPedidos = useCallback(async () => {
    const current = ++sequence.current.pedidos
    setPedidosRecentes({ status: 'loading' })
    try {
      const data = await buscarPedidosRecentes()
      if (current === sequence.current.pedidos) {
        setPedidosRecentes({ status: 'ready', data })
      }
    } catch (error) {
      if (current === sequence.current.pedidos) {
        setPedidosRecentes({ status: 'error', message: errorMessage(error) })
      }
    }
  }, [])

  const loadActivity = useCallback(async () => {
    const current = ++sequence.current.activity
    setRecentActivity({ status: 'loading' })
    try {
      const data = await fetchRecentActivity()
      if (current === sequence.current.activity) {
        setRecentActivity({ status: 'ready', data })
      }
    } catch (error) {
      if (current === sequence.current.activity) {
        setRecentActivity({ status: 'error', message: errorMessage(error) })
      }
    }
  }, [])

  useEffect(() => {
    void loadSummary()
    void carregarPedidos()
    void loadActivity()
  }, [loadSummary, carregarPedidos, loadActivity])

  const retry = useCallback(
    (section: DashboardSection) => {
      if (section === 'summary') void loadSummary()
      else if (section === 'pedidos') void carregarPedidos()
      else void loadActivity()
    },
    [loadSummary, carregarPedidos, loadActivity],
  )

  return { summary, pedidosRecentes, recentActivity, retry }
}
