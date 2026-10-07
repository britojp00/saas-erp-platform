const QUANTITY_PATTERN = /^\d{1,15}(\.\d{1,3})?$/
const QUANTITY_DECIMALS_PATTERN = /^\d+(\.\d{4,})$/
const MONEY_PATTERN = /^\d{1,15}(\.\d{1,2})?$/
const MONEY_DECIMALS_PATTERN = /^\d+(\.\d{3,})$/

export function normalizeDecimal(value: string): string {
  return value.trim().replace(',', '.')
}

export function validateQuantidade(raw: string): string | null {
  const value = raw.trim()
  if (value === '') return 'Informe a quantidade.'
  if (value.startsWith('-')) return 'A quantidade deve ser maior que zero.'

  const normalized = normalizeDecimal(value)
  if (QUANTITY_DECIMALS_PATTERN.test(normalized)) {
    return 'A quantidade deve ter no máximo 3 casas decimais.'
  }
  if (!QUANTITY_PATTERN.test(normalized)) {
    return 'Informe uma quantidade decimal válida (ex.: 2).'
  }
  if (Number(normalized) <= 0) return 'A quantidade deve ser maior que zero.'
  return null
}

export function validatePrecoUnitario(raw: string): string | null {
  const value = raw.trim()
  if (value === '') return null
  if (value.startsWith('-')) return 'O preço unitário não pode ser negativo.'

  const normalized = normalizeDecimal(value)
  if (MONEY_DECIMALS_PATTERN.test(normalized)) {
    return 'O preço unitário deve ter no máximo 2 casas decimais.'
  }
  if (!MONEY_PATTERN.test(normalized)) {
    return 'Informe um preço unitário decimal válido (ex.: 99,90).'
  }
  return null
}
