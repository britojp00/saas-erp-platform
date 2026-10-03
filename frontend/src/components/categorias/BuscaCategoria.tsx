import { useEffect, useState } from 'react'

const DEBOUNCE_MS = 350

interface BuscaCategoriaProps {
  value: string
  onChange: (term: string) => void
}

export default function BuscaCategoria({ value, onChange }: BuscaCategoriaProps) {
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
    <div className="categorias-search">
      <div className="field">
        <label htmlFor="categoria-search">Buscar por nome</label>
        <input
          id="categoria-search"
          type="search"
          placeholder="Nome da categoria"
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
