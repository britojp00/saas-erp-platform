import { Navigate, Route, Routes } from 'react-router-dom'
import AppLayout from './layouts/AppLayout'
import PaginaCriarCliente from './pages/PaginaCriarCliente'
import PaginaDetalheCliente from './pages/PaginaDetalheCliente'
import PaginaEditarCliente from './pages/PaginaEditarCliente'
import PaginaListaClientes from './pages/PaginaListaClientes'
import PaginaCriarCategoria from './pages/PaginaCriarCategoria'
import PaginaEditarCategoria from './pages/PaginaEditarCategoria'
import PaginaListaCategorias from './pages/PaginaListaCategorias'
import DashboardPage from './pages/DashboardPage'
import PaginaEstoque from './pages/PaginaEstoque'
import LoginPage from './pages/LoginPage'
import PaginaPedidos from './pages/PaginaPedidos'
import PaginaCriarPedido from './pages/PaginaCriarPedido'
import PaginaDetalhePedido from './pages/PaginaDetalhePedido'
import PaginaCriarProduto from './pages/PaginaCriarProduto'
import PaginaEditarProduto from './pages/PaginaEditarProduto'
import PaginaListaProdutos from './pages/PaginaListaProdutos'
import ProtectedRoute from './routes/ProtectedRoute'

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route element={<ProtectedRoute />}>
        <Route element={<AppLayout />}>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/clientes" element={<PaginaListaClientes />} />
          <Route path="/clientes/criar" element={<PaginaCriarCliente />} />
          <Route path="/clientes/:id" element={<PaginaDetalheCliente />} />
          <Route path="/clientes/:id/editar" element={<PaginaEditarCliente />} />
          <Route path="/categorias" element={<PaginaListaCategorias />} />
          <Route
            path="/categorias/criar"
            element={<PaginaCriarCategoria />}
          />
          <Route
            path="/categorias/:id/editar"
            element={<PaginaEditarCategoria />}
          />
          <Route path="/produtos" element={<PaginaListaProdutos />} />
          <Route path="/produtos/criar" element={<PaginaCriarProduto />} />
          <Route
            path="/produtos/:id/editar"
            element={<PaginaEditarProduto />}
          />
          <Route path="/estoque" element={<PaginaEstoque />} />
          <Route path="/pedidos" element={<PaginaPedidos />} />
          <Route path="/pedidos/criar" element={<PaginaCriarPedido />} />
          <Route path="/pedidos/:id" element={<PaginaDetalhePedido />} />
        </Route>
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
