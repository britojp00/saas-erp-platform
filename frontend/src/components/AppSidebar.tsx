import type { ReactNode } from 'react'
import { NavLink } from 'react-router-dom'
import { IconFolder, IconPackage } from '@tabler/icons-react'
import { useAuth } from '../contexts/AuthContext'

interface NavItem {
  to: string
  label: string
  icon?: ReactNode
}

const NAV_ITEMS: NavItem[] = [
  { to: '/dashboard', label: 'Dashboard' },
  { to: '/clientes', label: 'Clientes' },
  {
    to: '/categorias',
    label: 'Categorias',
    icon: <IconFolder size={16} aria-hidden="true" />,
  },
  {
    to: '/produtos',
    label: 'Produtos',
    icon: <IconPackage size={16} aria-hidden="true" />,
  },
  { to: '/estoque', label: 'Estoque' },
  { to: '/pedidos', label: 'Pedidos' },
]

interface AppSidebarProps {
  open: boolean
  onClose: () => void
}

export default function AppSidebar({ open, onClose }: AppSidebarProps) {
  const { user } = useAuth()

  return (
    <>
      {open && (
        <button
          type="button"
          className="sidebar-overlay"
          aria-label="Fechar menu de navegação"
          onClick={onClose}
        />
      )}
      <aside
        className={open ? 'sidebar sidebar--open' : 'sidebar'}
        id="app-sidebar"
      >
        <div className="sidebar__brand">SaaS ERP Platform</div>

        <nav className="sidebar__nav" aria-label="Módulos do ERP">
          <ul>
            {NAV_ITEMS.map((item) => (
              <li key={item.to}>
                <NavLink
                  to={item.to}
                  onClick={onClose}
                  className={({ isActive }) =>
                    isActive
                      ? 'sidebar__link sidebar__link--active'
                      : 'sidebar__link'
                  }
                >
                  {item.icon !== undefined && (
                    <span className="sidebar__icon" aria-hidden="true">
                      {item.icon}
                    </span>
                  )}
                  {item.label}
                </NavLink>
              </li>
            ))}
          </ul>
        </nav>

        {user !== null && (
          <div className="sidebar__user">
            <span className="sidebar__user-name">{user.full_name}</span>
            <span className="sidebar__user-meta">Empresa {user.empresa_id}</span>
          </div>
        )}
      </aside>
    </>
  )
}
