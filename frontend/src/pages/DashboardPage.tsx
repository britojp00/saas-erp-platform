import { useAuth } from '../contexts/AuthContext'

export default function DashboardPage() {
  const { user } = useAuth()

  if (user === null) {
    return null
  }

  return (
    <section className="dashboard">
      <header className="page-header">
        <div>
          <h1>Dashboard</h1>
          <p className="muted">Visão geral — Fase 2.4.</p>
        </div>
      </header>

      <section>
        <h2>Usuário</h2>
        <dl className="detail-list">
          <dt>Nome</dt>
          <dd>{user.full_name}</dd>
          <dt>E-mail</dt>
          <dd>{user.email}</dd>
          <dt>Tenant</dt>
          <dd>{user.tenant_id}</dd>
        </dl>
      </section>

      <section>
        <h2>Roles</h2>
        <ul className="tag-list">
          {user.roles.map((role) => (
            <li key={role}>{role}</li>
          ))}
        </ul>
      </section>

      <section>
        <h2>Permissions</h2>
        <ul className="tag-list">
          {user.permissions.map((permission) => (
            <li key={permission}>{permission}</li>
          ))}
        </ul>
      </section>
    </section>
  )
}
