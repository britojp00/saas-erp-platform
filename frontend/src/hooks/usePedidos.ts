import { useCallback, useEffect, useRef, useState } from 'react'
import { ApiError, api } from '../services/api'
import { ROTULOS_ACAO_PASSADO_PEDIDO } from '../types/pedidos'
import type {
  AcaoPedido,
  CampoOrdenacaoPedido,
  ListaPedidosResposta,
  Pedido,
  PedidoResumo,
  SortOrder,
} from '../types/pedidos'

const INITIAL_PAGE_SIZE = 20
const DEFAULT_SORT: CampoOrdenacaoPedido = 'created_at'
const DEFAULT_ORDER: SortOrder = 'desc'

export interface FeedbackPedidos {
  tone: 'sucesso' | 'erro'
  text: string
}

function errorMessage(error: unknown): string {
  if (error instanceof ApiError) return error.message
  return 'Não foi possível carregar os dados da API.'
}

function acaoErrorMessage(error: unknown): string {
  if (error instanceof ApiError) return error.message
  return 'Não foi possível atualizar o pedido. Tente novamente.'
}

export function usePedidos() {
  const [page, setPageState] = useState(1)
  const [search, setSearchState] = useState('')
  const [status, setStatusState] = useState('')
  const [sort, setSortState] = useState<CampoOrdenacaoPedido>(DEFAULT_SORT)
  const [order, setOrderState] = useState<SortOrder>(DEFAULT_ORDER)

  const [data, setData] = useState<ListaPedidosResposta<PedidoResumo> | null>(
    null,
  )
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [actingId, setActingId] = useState<number | null>(null)
  const [feedback, setFeedback] = useState<FeedbackPedidos | null>(null)

  const sequence = useRef(0)
  const actingRef = useRef(false)

  const load = useCallback(async () => {
    const current = ++sequence.current
    setLoading(true)
    setError(null)

    const params = new URLSearchParams({
      page: String(page),
      page_size: String(INITIAL_PAGE_SIZE),
      sort,
      order,
    })
    if (search !== '') params.set('search', search)
    if (status !== '') params.set('status', status)

    try {
      const response = await api.get<ListaPedidosResposta<PedidoResumo>>(
        `/api/v1/pedidos?${params.toString()}`,
      )
      if (current === sequence.current) {
        setData(response)
        setLoading(false)
      }
    } catch (err) {
      if (current === sequence.current) {
        setError(errorMessage(err))
        setLoading(false)
      }
    }
  }, [page, search, status, sort, order])

  useEffect(() => {
    void load()
  }, [load])

  const setPage = useCallback((next: number) => {
    setFeedback(null)
    setPageState(next)
  }, [])

  const setSearch = useCallback((term: string) => {
    setFeedback(null)
    setSearchState(term)
    setPageState(1)
  }, [])

  const setStatus = useCallback((next: string) => {
    setFeedback(null)
    setStatusState(next)
    setPageState(1)
  }, [])

  const toggleSort = useCallback(
    (field: CampoOrdenacaoPedido) => {
      setFeedback(null)
      setPageState(1)
      if (field === sort) {
        setOrderState((current) => (current === 'asc' ? 'desc' : 'asc'))
      } else {
        setSortState(field)
        setOrderState(field === 'numero_pedido' || field === 'status' ? 'asc' : 'desc')
      }
    },
    [sort],
  )

  const executarAcao = useCallback(
    async (pedido: PedidoResumo, acao: AcaoPedido) => {
      if (actingRef.current) return

      actingRef.current = true
      setActingId(pedido.id)
      setFeedback(null)

      try {
        await api.post<Pedido>(`/api/v1/pedidos/${pedido.id}/${acao}`)
        setFeedback({
          tone: 'sucesso',
          text: `Pedido #${pedido.numero_pedido} ${ROTULOS_ACAO_PASSADO_PEDIDO[acao]} com sucesso.`,
        })
        await load()
      } catch (err) {
        setFeedback({ tone: 'erro', text: acaoErrorMessage(err) })
      } finally {
        actingRef.current = false
        setActingId(null)
      }
    },
    [load],
  )

  const dismissFeedback = useCallback(() => {
    setFeedback(null)
  }, [])

  const retry = useCallback(() => {
    void load()
  }, [load])

  return {
    data,
    loading,
    error,
    actingId,
    feedback,
    page,
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
  }
}
