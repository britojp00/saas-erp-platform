import type { EstoqueSaldo } from '../../types/estoque'
import type { Produto } from '../../types/produtos'
import { formatDateTime, formatQuantity } from '../../utils/format'

interface ListaSaldosProps {
  items: EstoqueSaldo[]
  produtos: Produto[]
}

function produtoLabel(
  saldo: EstoqueSaldo,
  produtos: Produto[],
): string {
  const produto = produtos.find((item) => item.id === saldo.produto_id)
  if (produto !== undefined) return produto.name
  return `Produto #${saldo.produto_id}`
}

export default function ListaSaldos({ items, produtos }: ListaSaldosProps) {
  return (
    <div className="table-wrap">
      <table className="estoque-table">
        <thead>
          <tr>
            <th scope="col">ID</th>
            <th scope="col">Produto</th>
            <th scope="col">Quantidade</th>
            <th scope="col">Reservado</th>
            <th scope="col">Disponível</th>
            <th scope="col">Criado em</th>
          </tr>
        </thead>
        <tbody>
          {items.map((saldo) => (
            <tr key={saldo.id}>
              <td>{saldo.id}</td>
              <td>{produtoLabel(saldo, produtos)}</td>
              <td>{formatQuantity(saldo.quantity)}</td>
              <td>{formatQuantity(saldo.reserved_quantity)}</td>
              <td>
                {formatQuantity(
                  Number(saldo.quantity) - Number(saldo.reserved_quantity),
                )}
              </td>
              <td>{formatDateTime(saldo.created_at)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
