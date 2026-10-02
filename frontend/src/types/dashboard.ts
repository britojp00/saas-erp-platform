export interface PaginatedResponse<T> {
  items: T[]
  page: number
  page_size: number
  total: number
}

export type StatusPedido = 'RASCUNHO' | 'CONFIRMADO' | 'CONCLUIDO' | 'CANCELADO'

export const STATUS_PEDIDOS: readonly StatusPedido[] = [
  'RASCUNHO',
  'CONFIRMADO',
  'CONCLUIDO',
  'CANCELADO',
]

export const ROTULOS_STATUS_PEDIDO: Record<StatusPedido, string> = {
  RASCUNHO: 'Rascunho',
  CONFIRMADO: 'Confirmado',
  CONCLUIDO: 'Concluído',
  CANCELADO: 'Cancelado',
}

export interface ListaPedidosResposta<T> {
  itens: T[]
  page: number
  page_size: number
  total: number
}

export interface PedidoResumo {
  id: number
  tenant_id: number
  numero_pedido: number
  cliente_id: number
  status: string
  total_amount: number
  created_at: string
  updated_at: string
}

export interface ItemEstoque {
  id: number
  tenant_id: number
  produto_id: number
  quantity: number | string
  reserved_quantity: number | string
  created_at: string
  updated_at: string
}

export interface AuditLogItem {
  id: number
  tenant_id: number
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
