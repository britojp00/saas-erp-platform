import { useCallback, useEffect, useRef, useState } from 'react'
import { ApiError, api } from '../services/api'
import type { Categoria } from '../types/categorias'

function errorMessage(error: unknown): string {
  if (error instanceof ApiError) return error.message
  return 'Não foi possível carregar os dados da API.'
}

export function useCategoria(id: string) {
  const [categoria, setCategoria] = useState<Categoria | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [notFound, setNotFound] = useState(false)

  const sequence = useRef(0)

  const load = useCallback(async () => {
    const current = ++sequence.current

    if (!/^\d+$/.test(id)) {
      setNotFound(true)
      setError(null)
      setCategoria(null)
      setLoading(false)
      return
    }

    setLoading(true)
    setError(null)
    setNotFound(false)

    try {
      const response = await api.get<Categoria>(`/api/v1/categorias/${id}`)
      if (current === sequence.current) {
        setCategoria(response)
        setLoading(false)
      }
    } catch (err) {
      if (current === sequence.current) {
        if (err instanceof ApiError && err.status === 404) {
          setNotFound(true)
          setCategoria(null)
          setError(null)
        } else {
          setError(errorMessage(err))
        }
        setLoading(false)
      }
    }
  }, [id])

  useEffect(() => {
    setCategoria(null)
  }, [id])

  useEffect(() => {
    void load()
  }, [load])

  const retry = useCallback(() => {
    void load()
  }, [load])

  return { categoria, loading, error, notFound, retry }
}
