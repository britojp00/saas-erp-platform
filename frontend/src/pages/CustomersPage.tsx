import CustomerList from '../components/customers/CustomerList'
import CustomerSearch from '../components/customers/CustomerSearch'
import Pagination from '../components/customers/Pagination'
import { SectionError, SectionLoading } from '../components/dashboard/SectionState'
import { useCustomers } from '../hooks/useCustomers'

export default function CustomersPage() {
  const {
    data,
    loading,
    error,
    search,
    sort,
    order,
    setPage,
    setSearch,
    toggleSort,
    retry,
  } = useCustomers()

  return (
    <section className="customers-page">
      <header className="page-header">
        <div>
          <h1>Clientes</h1>
          <p className="muted">Gestão de clientes da empresa autenticada.</p>
        </div>
      </header>

      <div className="customers-toolbar">
        <CustomerSearch value={search} onChange={setSearch} />
        {loading && data !== null && (
          <p className="section-state" role="status">
            Carregando clientes...
          </p>
        )}
      </div>

      {error !== null ? (
        <SectionError message={error} onRetry={retry} />
      ) : data === null ? (
        <SectionLoading label="Carregando clientes..." />
      ) : data.items.length === 0 ? (
        <p className="empty-state">
          {search !== ''
            ? `Nenhum resultado para '${search}'`
            : 'Nenhum cliente cadastrado'}
        </p>
      ) : (
        <>
          <CustomerList
            items={data.items}
            sort={sort}
            order={order}
            onSort={toggleSort}
          />
          <Pagination
            page={data.page}
            pageSize={data.page_size}
            total={data.total}
            onPageChange={setPage}
          />
        </>
      )}
    </section>
  )
}
