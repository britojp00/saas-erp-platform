import type { PaginatedResponse } from './dashboard'

export interface EstoqueSaldo {
  id: number
  empresa_id: number
  produto_id: number
  quantity: string
  reserved_quantity: string
  created_at: string
  updated_at: string
}

export type ListaSaldosEstoqueResposta = PaginatedResponse<EstoqueSaldo>

export type TipoMovimentacao = 'ENTRADA' | 'SAIDA' | 'AJUSTE'

export const TIPOS_MOVIMENTACAO: readonly TipoMovimentacao[] = [
  'ENTRADA',
  'SAIDA',
  'AJUSTE',
]

export const ROTULOS_TIPO_MOVIMENTACAO: Record<TipoMovimentacao, string> = {
  ENTRADA: 'Entrada',
  SAIDA: 'Saída',
  AJUSTE: 'Ajuste',
}

export interface MovimentacaoEstoque {
  id: number
  empresa_id: number
  produto_id: number
  tipo_movimentacao: TipoMovimentacao
  quantity: string
  reference: string | null
  notes: string | null
  idempotency_key: string
  performed_at: string
  created_at: string
  updated_at: string
}

export type ListaMovimentacoesEstoqueResposta =
  PaginatedResponse<MovimentacaoEstoque>

export type StatusReserva = 'ATIVA' | 'CONFIRMADA' | 'LIBERADA' | 'CANCELADA'

export interface ReservaEstoque {
  id: number
  empresa_id: number
  produto_id: number
  quantity: string
  status: StatusReserva
  reference: string | null
  notes: string | null
  idempotency_key: string
  pedido_item_id: number | null
  reserved_at: string
  confirmed_at: string | null
  released_at: string | null
  created_at: string
  updated_at: string
}

export type ListaReservasEstoqueResposta = PaginatedResponse<ReservaEstoque>

export type AcaoReserva = 'confirmar' | 'liberar' | 'cancelar'

export interface MovimentacaoCriarPayload {
  produto_id: number
  tipo_movimentacao: TipoMovimentacao
  quantity: string
  reference: string | null
  notes: string | null
  idempotency_key: string
}

export interface ValoresFormularioMovimentacao {
  produto_id: string
  tipo_movimentacao: string
  quantity: string
  reference: string
  notes: string
}
