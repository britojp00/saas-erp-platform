import { useEffect, useState } from 'react'

const DEBOUNCE_MS = 350

interface BuscaPedidoProps {
  value: string
  onChange: (term: string) => void
}

export default function BuscaPedido({ value, onChange }: BuscaPedidoProps) {
  const [draft, setDraft] = useState(value)

  useEffect(() => {
    if (draft === value) return
    const timer = window.setTimeout(() => onChange(draft), DEBOUNCE_MS)
    return () => window.clearTimeout(timer)
  }, [draft, value, onChange])

  function handleClear() {
    setDraft('')
    onChange('')
  }

  return (
    <div className="pedidos-search">
      <div className="field">
        <label htmlFor="pedido-search">Buscar por número ou observações</label>
        <input
          id="pedido-search"
          type="search"
          placeholder="Número ou observações do pedido"
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
        />
      </div>
      {draft !== '' && (
        <button type="button" onClick={handleClear}>
          Limpar busca
        </button>
      )}
    </div>
  )
}
