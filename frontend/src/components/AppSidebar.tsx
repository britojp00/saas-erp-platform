import { NavLink } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

interface NavItem {
  to: string
  label: string
}

const NAV_ITEMS: NavItem[] = [
  { to: '/dashboard', label: 'Dashboard' },
  { to: '/customers', label: 'Customers' },
  { to: '/products', label: 'Products' },
  { to: '/inventory', label: 'Inventory' },
  { to: '/orders', label: 'Orders' },
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
                  {item.label}
                </NavLink>
              </li>
            ))}
          </ul>
        </nav>

        {user !== null && (
          <div className="sidebar__user">
            <span className="sidebar__user-name">{user.full_name}</span>
            <span className="sidebar__user-meta">Tenant {user.tenant_id}</span>
          </div>
        )}
      </aside>
    </>
  )
}
