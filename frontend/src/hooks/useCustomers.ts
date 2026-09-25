import { useCallback, useEffect, useRef, useState } from 'react'
import { ApiError, api } from '../services/api'
import type {
  CustomerListResponse,
  CustomerSortField,
  SortOrder,
} from '../types/customers'

const INITIAL_PAGE_SIZE = 20
const DEFAULT_SORT: CustomerSortField = 'id'
const DEFAULT_ORDER: SortOrder = 'desc'

function errorMessage(error: unknown): string {
  if (error instanceof ApiError) return error.message
  return 'Não foi possível carregar os dados da API.'
}

export function useCustomers() {
  const [page, setPageState] = useState(1)
  const [search, setSearchState] = useState('')
  const [sort, setSortState] = useState<CustomerSortField>(DEFAULT_SORT)
  const [order, setOrderState] = useState<SortOrder>(DEFAULT_ORDER)

  const [data, setData] = useState<CustomerListResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const sequence = useRef(0)

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
      const response = await api.get<CustomerListResponse>(
        `/api/v1/customers?${params.toString()}`,
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
    setPageState(next)
  }, [])

  const setSearch = useCallback((term: string) => {
    setSearchState(term)
    setPageState(1)
  }, [])

  const toggleSort = useCallback(
    (field: CustomerSortField) => {
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

  const retry = useCallback(() => {
    void load()
  }, [load])

  return {
    data,
    loading,
    error,
    page,
    search,
    sort,
    order,
    setPage,
    setSearch,
    toggleSort,
    retry,
  }
}
