import type { MovimentacaoEstoque } from '../../types/estoque'
import { ROTULOS_TIPO_MOVIMENTACAO } from '../../types/estoque'
import type { Produto } from '../../types/produtos'
import { formatDateTime, formatQuantity } from '../../utils/format'

interface ListaMovimentacoesProps {
  items: MovimentacaoEstoque[]
  produtos: Produto[]
}

function produtoLabel(
  movimentacao: MovimentacaoEstoque,
  produtos: Produto[],
): string {
  const produto = produtos.find((item) => item.id === movimentacao.produto_id)
  if (produto !== undefined) return produto.name
  return `Produto #${movimentacao.produto_id}`
}

export default function ListaMovimentacoes({
  items,
  produtos,
}: ListaMovimentacoesProps) {
  return (
    <div className="table-wrap">
      <table className="estoque-table">
        <thead>
          <tr>
            <th scope="col">ID</th>
            <th scope="col">Produto</th>
            <th scope="col">Tipo</th>
            <th scope="col">Quantidade</th>
            <th scope="col">Referência</th>
            <th scope="col">Observações</th>
            <th scope="col">Movimentado em</th>
          </tr>
        </thead>
        <tbody>
          {items.map((movimentacao) => (
            <tr key={movimentacao.id}>
              <td>{movimentacao.id}</td>
              <td>{produtoLabel(movimentacao, produtos)}</td>
              <td>
                {ROTULOS_TIPO_MOVIMENTACAO[movimentacao.tipo_movimentacao] ??
                  movimentacao.tipo_movimentacao}
              </td>
              <td>{formatQuantity(movimentacao.quantity)}</td>
              <td>
                {movimentacao.reference !== null ? (
                  <>{movimentacao.reference}</>
                ) : (
                  <span className="muted">—</span>
                )}
              </td>
              <td>
                {movimentacao.notes !== null ? (
                  <>{movimentacao.notes}</>
                ) : (
                  <span className="muted">—</span>
                )}
              </td>
              <td>{formatDateTime(movimentacao.performed_at)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
