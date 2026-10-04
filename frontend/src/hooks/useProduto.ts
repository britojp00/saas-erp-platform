import { useCallback, useEffect, useRef, useState } from 'react'
import { ApiError, api } from '../services/api'
import type { Produto } from '../types/produtos'

function errorMessage(error: unknown): string {
  if (error instanceof ApiError) return error.message
  return 'Não foi possível carregar os dados da API.'
}

export function useProduto(id: string) {
  const [produto, setProduto] = useState<Produto | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [notFound, setNotFound] = useState(false)

  const sequence = useRef(0)

  const load = useCallback(async () => {
    const current = ++sequence.current

    if (!/^\d+$/.test(id)) {
      setNotFound(true)
      setError(null)
      setProduto(null)
      setLoading(false)
      return
    }

    setLoading(true)
    setError(null)
    setNotFound(false)

    try {
      const response = await api.get<Produto>(`/api/v1/produtos/${id}`)
      if (current === sequence.current) {
        setProduto(response)
        setLoading(false)
      }
    } catch (err) {
      if (current === sequence.current) {
        if (err instanceof ApiError && err.status === 404) {
          setNotFound(true)
          setProduto(null)
          setError(null)
        } else {
          setError(errorMessage(err))
        }
        setLoading(false)
      }
    }
  }, [id])

  useEffect(() => {
    setProduto(null)
  }, [id])

  useEffect(() => {
    void load()
  }, [load])

  const retry = useCallback(() => {
    void load()
  }, [load])

  return { produto, loading, error, notFound, retry }
}
