import type { StatusPedido } from './pedidos'

export type { ListaPedidosResposta, PedidoResumo } from './pedidos'
export type { StatusPedido }
export { ROTULOS_STATUS_PEDIDO, STATUS_PEDIDOS } from './pedidos'

export interface PaginatedResponse<T> {
  items: T[]
  page: number
  page_size: number
  total: number
}

export interface ItemEstoque {
  id: number
  empresa_id: number
  produto_id: number
  quantity: number | string
  reserved_quantity: number | string
  created_at: string
  updated_at: string
}

export interface AuditLogItem {
  id: number
  empresa_id: number
  user_id: number | null
  action: string
  entity_type: string
  entity_id: number | null
  description: string | null
  created_at: string
}

export interface ResumoEstoque {
  total: number
  complete: boolean
  quantity: number | null
  reserved: number | null
  available: number | null
}

export interface DashboardSummary {
  clientesTotal: number
  produtosTotal: number
  produtosAtivosTotal: number
  pedidosTotal: number
  pedidosPorStatus: Record<StatusPedido, number>
  pedidosNaoClassificados: number
  estoque: ResumoEstoque
  movimentosTotal: number
  reservasTotal: number
}
