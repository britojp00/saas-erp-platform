import type { Produto } from '../../types/produtos'

export type StatusProdutos = 'carregando' | 'erro' | 'pronto'

interface SelecaoProdutoProps {
  id: string
  label: string
  value: string
  onChange: (value: string) => void
  produtos: Produto[]
  status: StatusProdutos
  emptyLabel: string
  error?: string | null
  className?: string
  disabled?: boolean
}

export default function SelecaoProduto({
  id,
  label,
  value,
  onChange,
  produtos,
  status,
  emptyLabel,
  error = null,
  className,
  disabled = false,
}: SelecaoProdutoProps) {
  const errorId = `${id}-error`
  const hintId = `${id}-hint`
  const hint =
    status === 'erro' ? 'Não foi possível carregar a lista de produtos.' : null
  const describedBy =
    [hint !== null ? hintId : null, error !== null ? errorId : null]
      .filter((item): item is string => item !== null)
      .join(' ') || undefined

  const valorForaDaLista =
    value !== '' && !produtos.some((produto) => String(produto.id) === value)

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
          <option value="">Carregando produtos...</option>
        ) : status === 'erro' ? (
          <option value="">Produtos indisponíveis</option>
        ) : (
          <>
            <option value="">{emptyLabel}</option>
            {produtos.map((produto) => (
              <option key={produto.id} value={produto.id}>
                {produto.name} ({produto.sku})
              </option>
            ))}
            {valorForaDaLista && (
              <option value={value}>Produto atual ({value})</option>
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
