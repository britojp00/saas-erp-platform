import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import {
  SectionError,
  SectionLoading,
} from '../components/dashboard/SectionState'
import type { StatusProdutos } from '../components/estoque/SelecaoProduto'
import DetalhePedido from '../components/pedidos/DetalhePedido'
import ItensPedido from '../components/pedidos/ItensPedido'
import type { StatusClientes } from '../components/pedidos/SelecaoCliente'
import { usePedido } from '../hooks/usePedido'
import type { FeedbackPedidos } from '../hooks/usePedidos'
import { ApiError, api } from '../services/api'
import type { Cliente, ListaClientesResposta } from '../types/clientes'
import type {
  AcaoPedido,
  Pedido,
  PedidoAtualizarPayload,
  PedidoItem,
  PedidoItemAtualizarPayload,
  PedidoItemCriarPayload,
  ValoresFormItemPedido,
  ValoresFormularioPedido,
} from '../types/pedidos'
import {
  ROTULOS_ACAO_PASSADO_PEDIDO,
  ROTULOS_ACAO_PEDIDO,
  SUBSTANTIVOS_ACAO_PEDIDO,
  acoesDoPedido,
  rotuloStatusPedido,
} from '../types/pedidos'
import type { ListaProdutosResposta, Produto } from '../types/produtos'
import { normalizeDecimal } from '../utils/pedido'

const CLIENTES_OPTIONS_QUERY =
  '/api/v1/clientes?page=1&page_size=100&sort=name&order=asc'
const PRODUTOS_OPTIONS_QUERY =
  '/api/v1/produtos?page=1&page_size=100&sort=name&order=asc'

function acaoErrorMessage(error: unknown): string {
  if (error instanceof ApiError) return error.message
  return 'Não foi possível atualizar o pedido. Tente novamente.'
}

export default function PaginaDetalhePedido() {
  const { id = '' } = useParams()
  const {
    pedido,
    loading,
    error,
    notFound,
    retry,
    substituir,
  } = usePedido(id)

  const [feedback, setFeedback] = useState<FeedbackPedidos | null>(null)
  const [confirming, setConfirming] = useState<AcaoPedido | null>(null)
  const [actionLoading, setActionLoading] = useState(false)

  const [clientes, setClientes] = useState<Cliente[]>([])
  const [clientesStatus, setClientesStatus] = useState<StatusClientes>(
    'carregando',
  )
  const [produtos, setProdutos] = useState<Produto[]>([])
  const [produtosStatus, setProdutosStatus] = useState<StatusProdutos>(
    'carregando',
  )

  useEffect(() => {
    let cancelado = false

    async function loadClientes(): Promise<void> {
      try {
        const response = await api.get<ListaClientesResposta>(
          CLIENTES_OPTIONS_QUERY,
        )
        if (cancelado) return
        setClientes(response.items)
        setClientesStatus('pronto')
      } catch {
        if (cancelado) return
        setClientes([])
        setClientesStatus('erro')
      }
    }

    void loadClientes()
    return () => {
      cancelado = true
    }
  }, [])

  useEffect(() => {
    let cancelado = false

    async function loadProdutos(): Promise<void> {
      try {
        const response = await api.get<ListaProdutosResposta>(
          PRODUTOS_OPTIONS_QUERY,
        )
        if (cancelado) return
        setProdutos(response.items)
        setProdutosStatus('pronto')
      } catch {
        if (cancelado) return
        setProdutos([])
        setProdutosStatus('erro')
      }
    }

    void loadProdutos()
    return () => {
      cancelado = true
    }
  }, [])

  async function executar(acao: AcaoPedido): Promise<void> {
    if (pedido === null || actionLoading) return

    setActionLoading(true)
    setFeedback(null)

    try {
      const atualizado = await api.post<Pedido>(
        `/api/v1/pedidos/${pedido.id}/${acao}`,
      )
      substituir(atualizado)
      setFeedback({
        tone: 'sucesso',
        text: `Pedido #${atualizado.numero_pedido} ${ROTULOS_ACAO_PASSADO_PEDIDO[acao]} com sucesso.`,
      })
    } catch (err) {
      setFeedback({ tone: 'erro', text: acaoErrorMessage(err) })
    } finally {
      setActionLoading(false)
      setConfirming(null)
    }
  }

  async function salvarPedido(
    values: Pick<ValoresFormularioPedido, 'cliente_id' | 'notes'>,
  ): Promise<void> {
    if (pedido === null) return

    const payload: PedidoAtualizarPayload = {
      cliente_id: Number(values.cliente_id),
      notes: values.notes.trim() === '' ? null : values.notes.trim(),
    }
    const atualizado = await api.patch<Pedido>(
      `/api/v1/pedidos/${pedido.id}`,
      payload,
    )
    substituir(atualizado)
    setFeedback({ tone: 'sucesso', text: 'Pedido atualizado com sucesso.' })
  }

  async function salvarItem(
    item: PedidoItem,
    values: { quantity: string; unit_price: string },
  ): Promise<void> {
    if (pedido === null) return

    const payload: PedidoItemAtualizarPayload = {
      quantity: Number(normalizeDecimal(values.quantity)),
      ...(values.unit_price === ''
        ? {}
        : { unit_price: Number(normalizeDecimal(values.unit_price)) }),
    }
    await api.patch<PedidoItem>(
      `/api/v1/pedidos/${pedido.id}/itens/${item.id}`,
      payload,
    )
    setFeedback({
      tone: 'sucesso',
      text: `Item do pedido #${pedido.numero_pedido} atualizado com sucesso.`,
    })
    retry()
  }

  async function removerItem(item: PedidoItem): Promise<void> {
    if (pedido === null) return

    await api.delete(`/api/v1/pedidos/${pedido.id}/itens/${item.id}`)
    setFeedback({
      tone: 'sucesso',
      text: `Item do pedido #${pedido.numero_pedido} removido com sucesso.`,
    })
    retry()
  }

  async function adicionarItem(values: ValoresFormItemPedido): Promise<void> {
    if (pedido === null) return

    const payload: PedidoItemCriarPayload = {
      produto_id: Number(values.produto_id),
      quantity: Number(normalizeDecimal(values.quantity)),
      ...(values.unit_price.trim() === ''
        ? {}
        : { unit_price: Number(normalizeDecimal(values.unit_price)) }),
    }
    await api.post<PedidoItem>(`/api/v1/pedidos/${pedido.id}/itens`, payload)
    setFeedback({
      tone: 'sucesso',
      text: `Item adicionado ao pedido #${pedido.numero_pedido}.`,
    })
    retry()
  }

  const acoes = pedido !== null ? acoesDoPedido(pedido.status) : []

  return (
    <section className="pedido-detail-page">
      <header className="page-header">
        <div>
          <h1>
            {pedido !== null ? `Pedido #${pedido.numero_pedido}` : 'Pedido'}
          </h1>
          <p className="muted">
            {pedido !== null
              ? rotuloStatusPedido(pedido.status)
              : `Pedido #${id}`}
          </p>
        </div>

        <div className="page-header__actions">
          {pedido !== null && acoes.length > 0 && (
            <>
              {confirming !== null ? (
                <>
                  <span className="section-state" role="status">
                    {ROTULOS_ACAO_PEDIDO[confirming]} pedido #
                    {pedido.numero_pedido}?
                  </span>
                  <button
                    type="button"
                    className={
                      confirming === 'cancelar'
                        ? 'button--danger'
                        : 'button--primary'
                    }
                    disabled={actionLoading}
                    aria-busy={actionLoading}
                    aria-label={`Confirmar a ${SUBSTANTIVOS_ACAO_PEDIDO[confirming]} do pedido ${pedido.numero_pedido}`}
                    onClick={() => {
                      void executar(confirming)
                    }}
                  >
                    {actionLoading ? 'Processando...' : 'Confirmar'}
                  </button>
                  <button
                    type="button"
                    className="button--secondary"
                    disabled={actionLoading}
                    aria-label={`Descartar a ${SUBSTANTIVOS_ACAO_PEDIDO[confirming]} do pedido ${pedido.numero_pedido}`}
                    onClick={() => setConfirming(null)}
                  >
                    Cancelar
                  </button>
                </>
              ) : (
                acoes.map((acao) => (
                  <button
                    key={acao}
                    type="button"
                    className={
                      acao === 'cancelar' ? 'button--danger' : 'button--primary'
                    }
                    aria-label={`${ROTULOS_ACAO_PEDIDO[acao]} pedido ${pedido.numero_pedido}`}
                    onClick={() => setConfirming(acao)}
                  >
                    {ROTULOS_ACAO_PEDIDO[acao]}
                  </button>
                ))
              )}
            </>
          )}
          <Link to="/pedidos">← Voltar</Link>
        </div>
      </header>

      {feedback !== null &&
        (feedback.tone === 'sucesso' ? (
          <p className="section-state" role="status">
            {feedback.text}
          </p>
        ) : (
          <div className="section-error" role="alert">
            <p>{feedback.text}</p>
            <button type="button" onClick={() => setFeedback(null)}>
              Fechar
            </button>
          </div>
        ))}

      {notFound ? (
        <div className="pedido-missing" role="alert">
          <p>Pedido não encontrado</p>
          <Link to="/pedidos">Voltar para pedidos</Link>
        </div>
      ) : error !== null ? (
        <SectionError message={error} onRetry={retry} />
      ) : loading && pedido === null ? (
        <SectionLoading label="Carregando pedido..." />
      ) : pedido !== null ? (
        <>
          {loading && (
            <p className="section-state" role="status">
              Carregando pedido...
            </p>
          )}
          <DetalhePedido
            pedido={pedido}
            clientes={clientes}
            clientesStatus={clientesStatus}
            onSalvar={salvarPedido}
          />
          <ItensPedido
            pedido={pedido}
            produtos={produtos}
            produtosStatus={produtosStatus}
            onSalvarItem={salvarItem}
            onRemoverItem={removerItem}
            onAdicionarItem={adicionarItem}
          />
        </>
      ) : null}
    </section>
  )
}
