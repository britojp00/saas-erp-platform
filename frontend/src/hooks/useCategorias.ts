import { useCallback, useEffect, useRef, useState } from 'react'
import { ApiError, api } from '../services/api'
import type {
  CampoOrdenacaoCategoria,
  Categoria,
  ListaCategoriasResposta,
  SortOrder,
} from '../types/categorias'

const INITIAL_PAGE_SIZE = 20
const DEFAULT_SORT: CampoOrdenacaoCategoria = 'created_at'
const DEFAULT_ORDER: SortOrder = 'desc'

export interface FeedbackCategorias {
  tone: 'sucesso' | 'erro'
  text: string
}

function errorMessage(error: unknown): string {
  if (error instanceof ApiError) return error.message
  return 'Não foi possível carregar os dados da API.'
}

function deleteErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return `Não foi possível excluir a categoria: ${error.message}`
  }
  return 'Não foi possível excluir a categoria. Tente novamente.'
}

export function useCategorias() {
  const [page, setPageState] = useState(1)
  const [search, setSearchState] = useState('')
  const [sort, setSortState] = useState<CampoOrdenacaoCategoria>(DEFAULT_SORT)
  const [order, setOrderState] = useState<SortOrder>(DEFAULT_ORDER)

  const [data, setData] = useState<ListaCategoriasResposta | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [deletingId, setDeletingId] = useState<number | null>(null)
  const [feedback, setFeedback] = useState<FeedbackCategorias | null>(null)

  const sequence = useRef(0)
  const deletingRef = useRef(false)

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

    try {
      const response = await api.get<ListaCategoriasResposta>(
        `/api/v1/categorias?${params.toString()}`,
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
  }, [page, search, sort, order])

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

  const toggleSort = useCallback(
    (field: CampoOrdenacaoCategoria) => {
      setFeedback(null)
      setPageState(1)
      if (field === sort) {
        setOrderState((current) => (current === 'asc' ? 'desc' : 'asc'))
      } else {
        setSortState(field)
        setOrderState(field === 'name' ? 'asc' : 'desc')
      }
    },
    [sort],
  )

  const remove = useCallback(
    async (categoria: Categoria) => {
      if (deletingRef.current || data === null) return

      deletingRef.current = true
      setDeletingId(categoria.id)
      setFeedback(null)

      try {
        await api.delete(`/api/v1/categorias/${categoria.id}`)

        setData((current) => {
          if (current === null) return current
          if (!current.items.some((item) => item.id === categoria.id)) {
            return current
          }
          return {
            ...current,
            items: current.items.filter((item) => item.id !== categoria.id),
            total: Math.max(0, current.total - 1),
          }
        })

        const eraUnicoDaPagina = data.items.length === 1
        if (eraUnicoDaPagina && page > 1) {
          setPageState(page - 1)
        }

        setFeedback({
          tone: 'sucesso',
          text: `Categoria "${categoria.name}" excluída com sucesso.`,
        })
      } catch (err) {
        setFeedback({ tone: 'erro', text: deleteErrorMessage(err) })
      } finally {
        deletingRef.current = false
        setDeletingId(null)
      }
    },
    [data, page],
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
    deletingId,
    feedback,
    page,
    search,
    sort,
    order,
    setPage,
    setSearch,
    toggleSort,
    retry,
    remove,
    dismissFeedback,
  }
}
