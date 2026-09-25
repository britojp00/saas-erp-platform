import { useCallback, useEffect, useRef, useState } from 'react'
import { ApiError, api } from '../services/api'
import type { Customer } from '../types/customers'

function errorMessage(error: unknown): string {
  if (error instanceof ApiError) return error.message
  return 'Não foi possível carregar os dados da API.'
}

export function useCustomer(id: string) {
  const [customer, setCustomer] = useState<Customer | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [notFound, setNotFound] = useState(false)

  const sequence = useRef(0)

  const load = useCallback(async () => {
    const current = ++sequence.current

    if (!/^\d+$/.test(id)) {
      setNotFound(true)
      setError(null)
      setCustomer(null)
      setLoading(false)
      return
    }

    setLoading(true)
    setError(null)
    setNotFound(false)

    try {
      const response = await api.get<Customer>(`/api/v1/customers/${id}`)
      if (current === sequence.current) {
        setCustomer(response)
        setLoading(false)
      }
    } catch (err) {
      if (current === sequence.current) {
        if (err instanceof ApiError && err.status === 404) {
          setNotFound(true)
          setCustomer(null)
          setError(null)
        } else {
          setError(errorMessage(err))
        }
        setLoading(false)
      }
    }
  }, [id])

  useEffect(() => {
    setCustomer(null)
  }, [id])

  useEffect(() => {
    void load()
  }, [load])

  const retry = useCallback(() => {
    void load()
  }, [load])

  return { customer, loading, error, notFound, retry }
}
