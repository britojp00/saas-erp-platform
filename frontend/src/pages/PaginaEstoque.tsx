import { useEffect, useState } from 'react'
import FormularioMovimentacao from '../components/estoque/FormularioMovimentacao'
import ListaMovimentacoes from '../components/estoque/ListaMovimentacoes'
import ListaReservas from '../components/estoque/ListaReservas'
import ListaSaldos from '../components/estoque/ListaSaldos'
import SelecaoProduto from '../components/estoque/SelecaoProduto'
import type { StatusProdutos } from '../components/estoque/SelecaoProduto'
import Pagination from '../components/clientes/Pagination'
import {
  SectionError,
  SectionLoading,
} from '../components/dashboard/SectionState'
import {
  useMovimentacoesEstoque,
  useReservasEstoque,
  useSaldosEstoque,
} from '../hooks/useEstoque'
import type { FeedbackEstoque } from '../hooks/useEstoque'
import { api } from '../services/api'
import type {
  AcaoReserva,
  MovimentacaoCriarPayload,
  MovimentacaoEstoque,
  ReservaEstoque,
} from '../types/estoque'
import type { ListaProdutosResposta, Produto } from '../types/produtos'

const PRODUTOS_OPTIONS_QUERY =
  '/api/v1/produtos?page=1&page_size=100&sort=name&order=asc'

type AbaEstoque = 'saldos' | 'movimentacoes' | 'reservas'

const ABAS: { id: AbaEstoque; rotulo: string }[] = [
  { id: 'saldos', rotulo: 'Saldos' },
  { id: 'movimentacoes', rotulo: 'Movimentações' },
  { id: 'reservas', rotulo: 'Reservas' },
]

function Feedback({
  feedback,
  onDismiss,
}: {
  feedback: FeedbackEstoque
  onDismiss: () => void
}) {
  if (feedback.tone === 'sucesso') {
    return (
      <p className="section-state" role="status">
        {feedback.text}
      </p>
    )
  }
  return (
    <div className="section-error" role="alert">
      <p>{feedback.text}</p>
      <button type="button" onClick={onDismiss}>
        Fechar
      </button>
    </div>
  )
}

export default function PaginaEstoque() {
  const [aba, setAba] = useState<AbaEstoque>('saldos')
  const [produtos, setProdutos] = useState<Produto[]>([])
  const [produtosStatus, setProdutosStatus] =
    useState<StatusProdutos>('carregando')
  const [movimentacaoFeedback, setMovimentacaoFeedback] =
    useState<FeedbackEstoque | null>(null)

  const saldos = useSaldosEstoque()
  const movimentacoes = useMovimentacoesEstoque()
  const reservas = useReservasEstoque()

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

  async function submitMovimentacao(
    payload: MovimentacaoCriarPayload,
  ): Promise<void> {
    setMovimentacaoFeedback(null)
    await api.post<MovimentacaoEstoque>(
      '/api/v1/estoque/movimentacoes',
      payload,
    )
    setMovimentacaoFeedback({
      tone: 'sucesso',
      text: 'Movimentação registrada com sucesso.',
    })
    movimentacoes.refresh()
    saldos.refresh()
  }

  function handleAcaoReserva(
    reserva: ReservaEstoque,
    acao: AcaoReserva,
  ): void {
    void reservas.executarAcao(reserva, acao).then((sucesso) => {
      if (sucesso) saldos.refresh()
    })
  }

  function selectAba(next: AbaEstoque): void {
    if (next === aba) return
    setMovimentacaoFeedback(null)
    reservas.dismissFeedback()
    setAba(next)
  }

  function emptyMessage(base: string, produtoId: string): string {
    if (produtoId !== '') return `${base} para o produto selecionado.`
    return base
  }

  return (
    <section className="estoque-page">
      <header className="page-header">
        <div>
          <h1>Estoque</h1>
          <p className="muted">
            Saldos, movimentações e reservas da empresa autenticada.
          </p>
        </div>
      </header>

      <div className="estoque-tabs" role="tablist" aria-label="Seções de estoque">
        {ABAS.map((item) => (
          <button
            key={item.id}
            type="button"
            role="tab"
            id={`estoque-tab-${item.id}`}
            className="estoque-tab"
            aria-selected={aba === item.id}
            aria-controls={`estoque-painel-${item.id}`}
            onClick={() => selectAba(item.id)}
          >
            {item.rotulo}
          </button>
        ))}
      </div>

      {aba === 'saldos' && (
        <div
          role="tabpanel"
          id="estoque-painel-saldos"
          aria-labelledby="estoque-tab-saldos"
          className="estoque-panel"
        >
          <div className="estoque-toolbar">
            <SelecaoProduto
              id="estoque-filtro-saldos"
              className="estoque-filtro"
              label="Filtrar por produto"
              value={saldos.produtoId}
              onChange={saldos.setProdutoId}
              produtos={produtos}
              status={produtosStatus}
              emptyLabel="Todos os produtos"
            />
            {saldos.loading && saldos.data !== null && (
              <p className="section-state" role="status">
                Carregando saldos...
              </p>
            )}
          </div>

          {saldos.error !== null ? (
            <SectionError message={saldos.error} onRetry={saldos.refresh} />
          ) : saldos.data === null ? (
            <SectionLoading label="Carregando saldos..." />
          ) : saldos.data.items.length === 0 ? (
            saldos.loading ? null : (
              <p className="empty-state">
                {emptyMessage(
                  'Nenhum registro de estoque',
                  saldos.produtoId,
                )}
              </p>
            )
          ) : (
            <>
              <ListaSaldos items={saldos.data.items} produtos={produtos} />
              <Pagination
                page={saldos.data.page}
                pageSize={saldos.data.page_size}
                total={saldos.data.total}
                onPageChange={saldos.setPage}
              />
            </>
          )}
        </div>
      )}

      {aba === 'movimentacoes' && (
        <div
          role="tabpanel"
          id="estoque-painel-movimentacoes"
          aria-labelledby="estoque-tab-movimentacoes"
          className="estoque-panel"
        >
          {movimentacaoFeedback !== null && (
            <Feedback
              feedback={movimentacaoFeedback}
              onDismiss={() => setMovimentacaoFeedback(null)}
            />
          )}

          <section className="panel" aria-labelledby="estoque-movimentacao-title">
            <h2 id="estoque-movimentacao-title">Nova movimentação</h2>
            <FormularioMovimentacao
              produtos={produtos}
              produtosStatus={produtosStatus}
              submit={submitMovimentacao}
            />
          </section>

          <div className="estoque-toolbar">
            <SelecaoProduto
              id="estoque-filtro-movimentacoes"
              className="estoque-filtro"
              label="Filtrar por produto"
              value={movimentacoes.produtoId}
              onChange={movimentacoes.setProdutoId}
              produtos={produtos}
              status={produtosStatus}
              emptyLabel="Todos os produtos"
            />
            {movimentacoes.loading && movimentacoes.data !== null && (
              <p className="section-state" role="status">
                Carregando movimentações...
              </p>
            )}
          </div>

          {movimentacoes.error !== null ? (
            <SectionError
              message={movimentacoes.error}
              onRetry={movimentacoes.refresh}
            />
          ) : movimentacoes.data === null ? (
            <SectionLoading label="Carregando movimentações..." />
          ) : movimentacoes.data.items.length === 0 ? (
            movimentacoes.loading ? null : (
              <p className="empty-state">
                {emptyMessage(
                  'Nenhuma movimentação registrada',
                  movimentacoes.produtoId,
                )}
              </p>
            )
          ) : (
            <>
              <ListaMovimentacoes
                items={movimentacoes.data.items}
                produtos={produtos}
              />
              <Pagination
                page={movimentacoes.data.page}
                pageSize={movimentacoes.data.page_size}
                total={movimentacoes.data.total}
                onPageChange={movimentacoes.setPage}
              />
            </>
          )}
        </div>
      )}

      {aba === 'reservas' && (
        <div
          role="tabpanel"
          id="estoque-painel-reservas"
          aria-labelledby="estoque-tab-reservas"
          className="estoque-panel"
        >
          {reservas.feedback !== null && (
            <Feedback
              feedback={reservas.feedback}
              onDismiss={reservas.dismissFeedback}
            />
          )}

          <div className="estoque-toolbar">
            <SelecaoProduto
              id="estoque-filtro-reservas"
              className="estoque-filtro"
              label="Filtrar por produto"
              value={reservas.produtoId}
              onChange={reservas.setProdutoId}
              produtos={produtos}
              status={produtosStatus}
              emptyLabel="Todos os produtos"
            />
            {reservas.loading && reservas.data !== null && (
              <p className="section-state" role="status">
                Carregando reservas...
              </p>
            )}
          </div>

          {reservas.error !== null ? (
            <SectionError
              message={reservas.error}
              onRetry={reservas.refresh}
            />
          ) : reservas.data === null ? (
            <SectionLoading label="Carregando reservas..." />
          ) : reservas.data.items.length === 0 ? (
            reservas.loading ? null : (
              <p className="empty-state">
                {emptyMessage(
                  'Nenhuma reserva de estoque',
                  reservas.produtoId,
                )}
              </p>
            )
          ) : (
            <>
              <ListaReservas
                items={reservas.data.items}
                produtos={produtos}
                actingId={reservas.actingId}
                onAction={handleAcaoReserva}
              />
              <Pagination
                page={reservas.data.page}
                pageSize={reservas.data.page_size}
                total={reservas.data.total}
                onPageChange={reservas.setPage}
              />
            </>
          )}
        </div>
      )}
    </section>
  )
}
