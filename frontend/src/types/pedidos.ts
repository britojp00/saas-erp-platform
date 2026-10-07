export interface ListaPedidosResposta<T> {
  itens: T[]
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

export function ehStatusPedido(value: string): value is StatusPedido {
  return (STATUS_PEDIDOS as readonly string[]).includes(value)
}

export function rotuloStatusPedido(status: string): string {
  return ehStatusPedido(status) ? ROTULOS_STATUS_PEDIDO[status] : status
}

export function badgeStatusPedido(status: string): string {
  return `badge badge--${status.toLowerCase()}`
}

export interface PedidoItem {
  id: number
  empresa_id: number
  pedido_id: number
  produto_id: number
  quantity: number
  unit_price: number
  total_price: number
  created_at: string
  updated_at: string
}

export interface Pedido {
  id: number
  empresa_id: number
  numero_pedido: number
  cliente_id: number
  status: string
  total_amount: number
  notes: string | null
  created_at: string
  updated_at: string
  deleted_at: string | null
  itens: PedidoItem[]
}

export interface PedidoResumo {
  id: number
  empresa_id: number
  numero_pedido: number
  cliente_id: number
  status: string
  total_amount: number
  created_at: string
  updated_at: string
}

export type CampoOrdenacaoPedido =
  | 'numero_pedido'
  | 'status'
  | 'total_amount'
  | 'cliente_id'
  | 'created_at'
  | 'updated_at'

export type SortOrder = 'asc' | 'desc'

export type AcaoPedido = 'confirmar' | 'cancelar' | 'concluir'

export const ROTULOS_ACAO_PEDIDO: Record<AcaoPedido, string> = {
  confirmar: 'Confirmar',
  cancelar: 'Cancelar',
  concluir: 'Concluir',
}

export const SUBSTANTIVOS_ACAO_PEDIDO: Record<AcaoPedido, string> = {
  confirmar: 'confirmação',
  cancelar: 'cancelamento',
  concluir: 'conclusão',
}

export const ROTULOS_ACAO_PASSADO_PEDIDO: Record<AcaoPedido, string> = {
  confirmar: 'confirmado',
  cancelar: 'cancelado',
  concluir: 'concluído',
}

export function acoesDoPedido(status: string): AcaoPedido[] {
  if (status === 'RASCUNHO') return ['confirmar', 'cancelar']
  if (status === 'CONFIRMADO') return ['concluir', 'cancelar']
  return []
}

export interface PedidoCriarPayload {
  cliente_id: number
  notes: string | null
  itens: PedidoItemCriarPayload[]
}

export interface PedidoAtualizarPayload {
  cliente_id?: number
  notes?: string | null
}

export interface PedidoItemCriarPayload {
  produto_id: number
  quantity: number
  unit_price?: number
}

export interface PedidoItemAtualizarPayload {
  quantity?: number
  unit_price?: number
}

export interface ValoresFormularioPedido {
  cliente_id: string
  notes: string
  itens: ValoresFormItemPedido[]
}

export interface ValoresFormItemPedido {
  produto_id: string
  quantity: string
  unit_price: string
}
