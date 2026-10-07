import { useCallback, useEffect, useRef, useState } from 'react'
import { ApiError, api } from '../services/api'
import type {
  AcaoReserva,
  ListaMovimentacoesEstoqueResposta,
  ListaReservasEstoqueResposta,
  ListaSaldosEstoqueResposta,
  ReservaEstoque,
} from '../types/estoque'

const PAGE_SIZE = 20

export interface FeedbackEstoque {
  tone: 'sucesso' | 'erro'
  text: string
}

function errorMessage(error: unknown): string {
  if (error instanceof ApiError) return error.message
  return 'Não foi possível carregar os dados da API.'
}

function buildQuery(page: number, produtoId: string): string {
  const params = new URLSearchParams({
    page: String(page),
    page_size: String(PAGE_SIZE),
  })
  if (produtoId !== '') params.set('produto_id', produtoId)
  return params.toString()
}

function acaoErrorMessage(error: unknown, acao: AcaoReserva): string {
  if (error instanceof ApiError) {
    return `Não foi possível ${acao} a reserva: ${error.message}`
  }
  return `Não foi possível ${acao} a reserva. Tente novamente.`
}

const MENSAGENS_SUCESSO_RESERVA: Record<AcaoReserva, string> = {
  confirmar: 'Reserva confirmada com sucesso.',
  liberar: 'Reserva liberada com sucesso.',
  cancelar: 'Reserva cancelada com sucesso.',
}

export function useSaldosEstoque() {
  const [page, setPageState] = useState(1)
  const [produtoId, setProdutoIdState] = useState('')
  const [data, setData] = useState<ListaSaldosEstoqueResposta | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const sequence = useRef(0)

  const load = useCallback(async () => {
    const current = ++sequence.current
    setLoading(true)
    setError(null)

    try {
      const response = await api.get<ListaSaldosEstoqueResposta>(
        `/api/v1/estoque?${buildQuery(page, produtoId)}`,
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
  }, [page, produtoId])

  useEffect(() => {
    void load()
  }, [load])

  const setPage = useCallback((next: number) => {
    setPageState(next)
  }, [])

  const setProdutoId = useCallback((next: string) => {
    setPageState(1)
    setProdutoIdState(next)
  }, [])

  const refresh = useCallback(() => {
    void load()
  }, [load])

  return {
    data,
    loading,
    error,
    page,
    produtoId,
    setPage,
    setProdutoId,
    refresh,
  }
}

export function useMovimentacoesEstoque() {
  const [page, setPageState] = useState(1)
  const [produtoId, setProdutoIdState] = useState('')
  const [data, setData] = useState<ListaMovimentacoesEstoqueResposta | null>(
    null,
  )
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const sequence = useRef(0)

  const load = useCallback(async () => {
    const current = ++sequence.current
    setLoading(true)
    setError(null)

    try {
      const response = await api.get<ListaMovimentacoesEstoqueResposta>(
        `/api/v1/estoque/movimentacoes/list?${buildQuery(page, produtoId)}`,
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
  }, [page, produtoId])

  useEffect(() => {
    void load()
  }, [load])

  const setPage = useCallback((next: number) => {
    setPageState(next)
  }, [])

  const setProdutoId = useCallback((next: string) => {
    setPageState(1)
    setProdutoIdState(next)
  }, [])

  const refresh = useCallback(() => {
    void load()
  }, [load])

  return {
    data,
    loading,
    error,
    page,
    produtoId,
    setPage,
    setProdutoId,
    refresh,
  }
}

export function useReservasEstoque() {
  const [page, setPageState] = useState(1)
  const [produtoId, setProdutoIdState] = useState('')
  const [data, setData] = useState<ListaReservasEstoqueResposta | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [actingId, setActingId] = useState<number | null>(null)
  const [feedback, setFeedback] = useState<FeedbackEstoque | null>(null)

  const sequence = useRef(0)
  const actingRef = useRef(false)

  const load = useCallback(async () => {
    const current = ++sequence.current
    setLoading(true)
    setError(null)

    try {
      const response = await api.get<ListaReservasEstoqueResposta>(
        `/api/v1/estoque/reservas/list?${buildQuery(page, produtoId)}`,
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
  }, [page, produtoId])

  useEffect(() => {
    void load()
  }, [load])

  const setPage = useCallback((next: number) => {
    setPageState(next)
  }, [])

  const setProdutoId = useCallback((next: string) => {
    setPageState(1)
    setProdutoIdState(next)
  }, [])

  const refresh = useCallback(() => {
    void load()
  }, [load])

  const executarAcao = useCallback(
    async (reserva: ReservaEstoque, acao: AcaoReserva): Promise<boolean> => {
      if (actingRef.current) return false

      actingRef.current = true
      setActingId(reserva.id)
      setFeedback(null)

      try {
        await api.post<ReservaEstoque>(
          `/api/v1/estoque/reservas/${reserva.id}/${acao}`,
        )
        setFeedback({ tone: 'sucesso', text: MENSAGENS_SUCESSO_RESERVA[acao] })
        refresh()
        return true
      } catch (err) {
        setFeedback({ tone: 'erro', text: acaoErrorMessage(err, acao) })
        return false
      } finally {
        actingRef.current = false
        setActingId(null)
      }
    },
    [refresh],
  )

  const dismissFeedback = useCallback(() => {
    setFeedback(null)
  }, [])

  return {
    data,
    loading,
    error,
    actingId,
    feedback,
    page,
    produtoId,
    setPage,
    setProdutoId,
    refresh,
    executarAcao,
    dismissFeedback,
  }
}
