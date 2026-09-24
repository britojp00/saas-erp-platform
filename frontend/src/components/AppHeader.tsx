import { useAuth } from '../contexts/AuthContext'

interface AppHeaderProps {
  onToggleSidebar: () => void
}

export default function AppHeader({ onToggleSidebar }: AppHeaderProps) {
  const { user, logout } = useAuth()

  return (
    <header className="topbar">
      <button
        type="button"
        className="topbar__menu"
        aria-label="Abrir menu de navegação"
        aria-controls="app-sidebar"
        onClick={onToggleSidebar}
      >
        Menu
      </button>

      <div className="topbar__identity">
        {user !== null && (
          <>
            <span className="topbar__name">{user.full_name}</span>
            <span className="topbar__email">{user.email}</span>
          </>
        )}
      </div>

      <button type="button" className="topbar__logout" onClick={logout}>
        Sair
      </button>
    </header>
  )
}
