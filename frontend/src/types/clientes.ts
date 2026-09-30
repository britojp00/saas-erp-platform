import type { PaginatedResponse } from './dashboard'

export interface Cliente {
  id: number
  name: string
  document: string | null
  email: string | null
  phone: string | null
  notes: string | null
  created_at: string
  updated_at: string
}

export type ListaClientesResposta = PaginatedResponse<Cliente>

export type CampoOrdenacaoCliente = 'id' | 'name' | 'created_at'

export type SortOrder = 'asc' | 'desc'

export interface ClienteCriarPayload {
  name: string
  document: string | null
  email: string | null
  phone: string | null
  notes: string | null
}

export interface ClienteAtualizarPayload {
  name: string
  document: string | null
  email: string | null
  phone: string | null
  notes: string | null
}

export interface ValoresFormularioCliente {
  name: string
  document: string
  email: string
  phone: string
  notes: string
}
