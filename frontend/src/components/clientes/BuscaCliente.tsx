import { useEffect, useState } from 'react'

const DEBOUNCE_MS = 350

interface BuscaClienteProps {
  value: string
  onChange: (term: string) => void
}

export default function BuscaCliente({ value, onChange }: BuscaClienteProps) {
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
    <div className="clientes-search">
      <div className="field">
        <label htmlFor="cliente-search">Buscar por nome</label>
        <input
          id="cliente-search"
          type="search"
          placeholder="Nome do cliente"
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
