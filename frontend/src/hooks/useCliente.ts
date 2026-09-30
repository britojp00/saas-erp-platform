import { useCallback, useEffect, useRef, useState } from 'react'
import { ApiError, api } from '../services/api'
import type { Cliente } from '../types/clientes'

function errorMessage(error: unknown): string {
  if (error instanceof ApiError) return error.message
  return 'Não foi possível carregar os dados da API.'
}

export function useCliente(id: string) {
  const [cliente, setCliente] = useState<Cliente | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [notFound, setNotFound] = useState(false)

  const sequence = useRef(0)

  const load = useCallback(async () => {
    const current = ++sequence.current

    if (!/^\d+$/.test(id)) {
      setNotFound(true)
      setError(null)
      setCliente(null)
      setLoading(false)
      return
    }

    setLoading(true)
    setError(null)
    setNotFound(false)

    try {
      const response = await api.get<Cliente>(`/api/v1/clientes/${id}`)
      if (current === sequence.current) {
        setCliente(response)
        setLoading(false)
      }
    } catch (err) {
      if (current === sequence.current) {
        if (err instanceof ApiError && err.status === 404) {
          setNotFound(true)
          setCliente(null)
          setError(null)
        } else {
          setError(errorMessage(err))
        }
        setLoading(false)
      }
    }
  }, [id])

  useEffect(() => {
    setCliente(null)
  }, [id])

  useEffect(() => {
    void load()
  }, [load])

  const retry = useCallback(() => {
    void load()
  }, [load])

  return { cliente, loading, error, notFound, retry }
}
