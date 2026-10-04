import type { PaginatedResponse } from './dashboard'

export interface Produto {
  id: number
  empresa_id: number
  sku: string
  name: string
  description: string | null
  categoria_id: number | null
  price: string
  cost_price: string | null
  is_active: boolean
  created_at: string
  updated_at: string
  deleted_at: string | null
}

export type ListaProdutosResposta = PaginatedResponse<Produto>

export type CampoOrdenacaoProduto =
  | 'sku'
  | 'name'
  | 'price'
  | 'is_active'
  | 'created_at'

export type SortOrder = 'asc' | 'desc'

export interface ProdutoCriarPayload {
  sku: string
  name: string
  description: string | null
  categoria_id: number | null
  price: string
  cost_price: string | null
  is_active: boolean
}

export interface ProdutoAtualizarPayload {
  sku: string
  name: string
  description: string | null
  categoria_id: number | null
  price: string
  cost_price: string | null
  is_active: boolean
}

export interface ValoresFormularioProduto {
  sku: string
  name: string
  description: string
  categoria_id: string
  price: string
  cost_price: string
  is_active: string
}
