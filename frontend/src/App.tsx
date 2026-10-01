import { Navigate, Route, Routes } from 'react-router-dom'
import AppLayout from './layouts/AppLayout'
import PaginaCriarCliente from './pages/PaginaCriarCliente'
import PaginaDetalheCliente from './pages/PaginaDetalheCliente'
import PaginaEditarCliente from './pages/PaginaEditarCliente'
import PaginaListaClientes from './pages/PaginaListaClientes'
import DashboardPage from './pages/DashboardPage'
import InventoryPage from './pages/InventoryPage'
import LoginPage from './pages/LoginPage'
import OrdersPage from './pages/OrdersPage'
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
          <Route path="/clientes/new" element={<PaginaCriarCliente />} />
          <Route path="/clientes/:id" element={<PaginaDetalheCliente />} />
          <Route path="/clientes/:id/edit" element={<PaginaEditarCliente />} />
          <Route path="/produtos" element={<PaginaListaProdutos />} />
          <Route path="/inventory" element={<InventoryPage />} />
          <Route path="/orders" element={<OrdersPage />} />
        </Route>
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
