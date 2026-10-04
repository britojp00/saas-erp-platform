import { useEffect, useState } from 'react'

const DEBOUNCE_MS = 350

interface BuscaProdutoProps {
  value: string
  onChange: (term: string) => void
}

export default function BuscaProduto({ value, onChange }: BuscaProdutoProps) {
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
    <div className="produtos-search">
      <div className="field">
        <label htmlFor="produto-search">Buscar por nome ou SKU</label>
        <input
          id="produto-search"
          type="search"
          placeholder="Nome ou SKU do produto"
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
