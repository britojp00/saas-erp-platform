import { useCallback, useEffect, useRef, useState } from 'react'
import { ApiError, api } from '../services/api'
import type { Pedido } from '../types/pedidos'

function errorMessage(error: unknown): string {
  if (error instanceof ApiError) return error.message
  return 'Não foi possível carregar os dados da API.'
}

export function usePedido(id: string) {
  const [pedido, setPedido] = useState<Pedido | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [notFound, setNotFound] = useState(false)

  const sequence = useRef(0)

  const load = useCallback(async () => {
    const current = ++sequence.current

    if (!/^\d+$/.test(id)) {
      setNotFound(true)
      setError(null)
      setPedido(null)
      setLoading(false)
      return
    }

    setLoading(true)
    setError(null)
    setNotFound(false)

    try {
      const response = await api.get<Pedido>(`/api/v1/pedidos/${id}`)
      if (current === sequence.current) {
        setPedido(response)
        setLoading(false)
      }
    } catch (err) {
      if (current === sequence.current) {
        if (err instanceof ApiError && err.status === 404) {
          setNotFound(true)
          setPedido(null)
          setError(null)
        } else {
          setError(errorMessage(err))
        }
        setLoading(false)
      }
    }
  }, [id])

  useEffect(() => {
    setPedido(null)
  }, [id])

  useEffect(() => {
    void load()
  }, [load])

  const retry = useCallback(() => {
    void load()
  }, [load])

  const substituir = useCallback((proximo: Pedido) => {
    setPedido(proximo)
  }, [])

  return { pedido, loading, error, notFound, retry, substituir }
}
