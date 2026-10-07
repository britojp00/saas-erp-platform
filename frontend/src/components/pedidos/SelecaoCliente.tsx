import type { Cliente } from '../../types/clientes'

export type StatusClientes = 'carregando' | 'erro' | 'pronto'

interface SelecaoClienteProps {
  id: string
  label: string
  value: string
  onChange: (value: string) => void
  clientes: Cliente[]
  status: StatusClientes
  emptyLabel?: string
  error?: string | null
  className?: string
  disabled?: boolean
}

export default function SelecaoCliente({
  id,
  label,
  value,
  onChange,
  clientes,
  status,
  emptyLabel,
  error = null,
  className,
  disabled = false,
}: SelecaoClienteProps) {
  const errorId = `${id}-error`
  const hintId = `${id}-hint`
  const hint =
    status === 'erro' ? 'Não foi possível carregar a lista de clientes.' : null
  const describedBy =
    [hint !== null ? hintId : null, error !== null ? errorId : null]
      .filter((item): item is string => item !== null)
      .join(' ') || undefined

  const valorForaDaLista =
    value !== '' && !clientes.some((cliente) => String(cliente.id) === value)

  return (
    <div className={className !== undefined ? `field ${className}` : 'field'}>
      <label htmlFor={id}>{label}</label>
      <select
        id={id}
        name={id}
        value={value}
        disabled={disabled || status !== 'pronto'}
        aria-invalid={error !== null}
        aria-describedby={describedBy}
        onChange={(event) => onChange(event.target.value)}
      >
        {status === 'carregando' ? (
          <option value="">Carregando clientes...</option>
        ) : status === 'erro' ? (
          <option value="">Clientes indisponíveis</option>
        ) : (
          <>
            {emptyLabel !== undefined && <option value="">{emptyLabel}</option>}
            {clientes.map((cliente) => (
              <option key={cliente.id} value={cliente.id}>
                {cliente.name}
              </option>
            ))}
            {valorForaDaLista && (
              <option value={value}>Cliente atual ({value})</option>
            )}
          </>
        )}
      </select>
      {hint !== null && (
        <p className="field-hint" id={hintId}>
          {hint}
        </p>
      )}
      {error !== null && (
        <p className="field-error" id={errorId}>
          {error}
        </p>
      )}
    </div>
  )
}
