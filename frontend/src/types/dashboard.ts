export interface PaginatedResponse<T> {
  items: T[]
  page: number
  page_size: number
  total: number
}

export type OrderStatus = 'DRAFT' | 'CONFIRMED' | 'COMPLETED' | 'CANCELLED'

export const ORDER_STATUSES: readonly OrderStatus[] = [
  'DRAFT',
  'CONFIRMED',
  'COMPLETED',
  'CANCELLED',
]

export const ORDER_STATUS_LABELS: Record<OrderStatus, string> = {
  DRAFT: 'Rascunho',
  CONFIRMED: 'Confirmado',
  COMPLETED: 'Concluído',
  CANCELLED: 'Cancelado',
}

export interface OrderListItem {
  id: number
  tenant_id: number
  order_number: number
  customer_id: number
  status: string
  total_amount: number
  created_at: string
  updated_at: string
}

export interface InventoryItem {
  id: number
  tenant_id: number
  product_id: number
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

export interface InventorySummary {
  total: number
  complete: boolean
  quantity: number | null
  reserved: number | null
  available: number | null
}

export interface DashboardSummary {
  customersTotal: number
  productsTotal: number
  activeProductsTotal: number
  ordersTotal: number
  ordersByStatus: Record<OrderStatus, number>
  ordersUnclassified: number
  inventory: InventorySummary
  movementsTotal: number
  reservationsTotal: number
}
