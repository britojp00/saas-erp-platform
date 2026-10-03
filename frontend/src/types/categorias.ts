import type { PaginatedResponse } from './dashboard'

export interface Categoria {
  id: number
  empresa_id: number
  name: string
  description: string | null
  parent_id: number | null
  created_at: string
  updated_at: string
  deleted_at: string | null
}

export type ListaCategoriasResposta = PaginatedResponse<Categoria>

export type CampoOrdenacaoCategoria = 'name' | 'created_at'

export type SortOrder = 'asc' | 'desc'

export interface CategoriaCriarPayload {
  name: string
  description: string | null
  parent_id: number | null
}

export interface CategoriaAtualizarPayload {
  name?: string
  description?: string | null
  parent_id?: number | null
}

export interface ValoresFormularioCategoria {
  name: string
  description: string
  parent_id: string
}
