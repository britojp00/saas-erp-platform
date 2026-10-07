import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import type { StatusProdutos } from '../components/estoque/SelecaoProduto'
import FormularioPedido, {
  INITIAL_VALUES_PEDIDO,
} from '../components/pedidos/FormularioPedido'
import type { StatusClientes } from '../components/pedidos/SelecaoCliente'
import { api } from '../services/api'
import type { Cliente, ListaClientesResposta } from '../types/clientes'
import type { Pedido, PedidoCriarPayload } from '../types/pedidos'
import type { ListaProdutosResposta, Produto } from '../types/produtos'

const CLIENTES_OPTIONS_QUERY =
  '/api/v1/clientes?page=1&page_size=100&sort=name&order=asc'
const PRODUTOS_OPTIONS_QUERY =
  '/api/v1/produtos?page=1&page_size=100&sort=name&order=asc'

export default function PaginaCriarPedido() {
  const navigate = useNavigate()
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

  async function submit(values: PedidoCriarPayload): Promise<void> {
    const created = await api.post<Pedido>('/api/v1/pedidos', values)
    navigate('/pedidos', {
      replace: true,
      state: { feedback: `Pedido #${created.numero_pedido} criado com sucesso.` },
    })
  }

  function cancel(): void {
    navigate('/pedidos', { replace: true })
  }

  return (
    <section className="pedido-create-page">
      <header className="page-header">
        <div>
          <h1>Novo pedido</h1>
          <p className="muted">Registre um pedido em rascunho.</p>
        </div>
        <Link to="/pedidos" replace>
          ← Voltar
        </Link>
      </header>

      <FormularioPedido
        initialValues={INITIAL_VALUES_PEDIDO}
        submit={submit}
        submitLabel="Salvar"
        onCancel={cancel}
        clientes={clientes}
        clientesStatus={clientesStatus}
        produtos={produtos}
        produtosStatus={produtosStatus}
      />
    </section>
  )
}
