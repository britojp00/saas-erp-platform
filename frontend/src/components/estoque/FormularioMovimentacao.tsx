import { useId, useState } from 'react'
import type { FormEvent, ReactNode } from 'react'
import { ApiError } from '../../services/api'
import type { ApiFieldError } from '../../services/api'
import type {
  MovimentacaoCriarPayload,
  TipoMovimentacao,
  ValoresFormularioMovimentacao,
} from '../../types/estoque'
import {
  ROTULOS_TIPO_MOVIMENTACAO,
  TIPOS_MOVIMENTACAO,
} from '../../types/estoque'
import type { Produto } from '../../types/produtos'
import SelecaoProduto from './SelecaoProduto'
import type { StatusProdutos } from './SelecaoProduto'

type FieldName = keyof ValoresFormularioMovimentacao

type FieldErrors = Record<FieldName, string | null>

const LIMITS = {
  reference: 255,
  notes: 500,
} as const

const NO_ERRORS: FieldErrors = {
  produto_id: null,
  tipo_movimentacao: null,
  quantity: null,
  reference: null,
  notes: null,
}

const INITIAL_VALUES: ValoresFormularioMovimentacao = {
  produto_id: '',
  tipo_movimentacao: '',
  quantity: '',
  reference: '',
  notes: '',
}

const QUANTITY_PATTERN = /^\d{1,12}(\.\d{1,3})?$/
const QUANTITY_DECIMALS_PATTERN = /^\d{1,12}\.\d{4,}$/
const QUANTITY_DIGITS_PATTERN = /^\d{13,}(\.\d+)?$/

function normalizeQuantity(value: string): string {
  return value.trim().replace(',', '.')
}

function validateQuantity(raw: string): string | null {
  const value = raw.trim()
  if (value === '') return 'Informe a quantidade.'

  const normalized = normalizeQuantity(value)
  if (normalized.startsWith('-')) {
    return 'A quantidade deve ser maior que zero.'
  }
  if (QUANTITY_DECIMALS_PATTERN.test(normalized)) {
    return 'A quantidade deve ter no máximo 3 casas decimais.'
  }
  if (QUANTITY_DIGITS_PATTERN.test(normalized)) {
    return 'A quantidade deve ter no máximo 12 dígitos inteiros.'
  }
  if (!QUANTITY_PATTERN.test(normalized)) {
    return 'Informe uma quantidade decimal válida (ex.: 10 ou 2,5).'
  }
  if (Number(normalized) <= 0) {
    return 'A quantidade deve ser maior que zero.'
  }
  return null
}

function validate(values: ValoresFormularioMovimentacao): FieldErrors {
  const errors: FieldErrors = { ...NO_ERRORS }

  if (values.produto_id.trim() === '') {
    errors.produto_id = 'Informe o produto.'
  }

  const tipo = values.tipo_movimentacao
  if (!(TIPOS_MOVIMENTACAO as readonly string[]).includes(tipo)) {
    errors.tipo_movimentacao = 'Selecione o tipo de movimentação.'
  }

  errors.quantity = validateQuantity(values.quantity)

  if (values.reference.length > LIMITS.reference) {
    errors.reference = `A referência deve ter no máximo ${LIMITS.reference} caracteres.`
  }

  if (values.notes.length > LIMITS.notes) {
    errors.notes = `As observações devem ter no máximo ${LIMITS.notes} caracteres.`
  }

  return errors
}

function toPayload(
  values: ValoresFormularioMovimentacao,
  idempotencyKey: string,
): MovimentacaoCriarPayload {
  const reference = values.reference.trim()
  const notes = values.notes.trim()
  return {
    produto_id: Number(values.produto_id),
    tipo_movimentacao: values.tipo_movimentacao as TipoMovimentacao,
    quantity: normalizeQuantity(values.quantity),
    reference: reference === '' ? null : reference,
    notes: notes === '' ? null : notes,
    idempotency_key: idempotencyKey,
  }
}

function toFieldErrors(errors: ApiFieldError[]): FieldErrors | null {
  if (errors.length === 0) return null
  const next: FieldErrors = { ...NO_ERRORS }
  let mapped = false
  for (const { field, message } of errors) {
    if (field in next) {
      next[field as FieldName] = message
      mapped = true
    }
  }
  return mapped ? next : null
}

export interface FormularioMovimentacaoProps {
  produtos: Produto[]
  produtosStatus: StatusProdutos
  submit: (values: MovimentacaoCriarPayload) => Promise<unknown>
}

interface FieldShellProps {
  id: string
  label: string
  error: string | null
  hint?: string
  children: (aria: {
    id: string
    'aria-invalid': boolean
    'aria-describedby': string | undefined
  }) => ReactNode
}

function FieldShell({ id, label, error, hint, children }: FieldShellProps) {
  const errorId = `${id}-error`
  const hintId = `${id}-hint`
  const describedBy =
    [hint !== undefined ? hintId : null, error !== null ? errorId : null]
      .filter((value): value is string => value !== null)
      .join(' ') || undefined

  return (
    <div className="field">
      <label htmlFor={id}>{label}</label>
      {children({
        id,
        'aria-invalid': error !== null,
        'aria-describedby': describedBy,
      })}
      {hint !== undefined && (
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

export default function FormularioMovimentacao({
  produtos,
  produtosStatus,
  submit,
}: FormularioMovimentacaoProps) {
  const formId = useId()
  const [values, setValues] = useState<ValoresFormularioMovimentacao>(
    INITIAL_VALUES,
  )
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>(NO_ERRORS)
  const [formError, setFormError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  const idFor = (field: FieldName): string => `${formId}-${field}`

  function setValue(field: FieldName, value: string): void {
    setValues((previous) => ({ ...previous, [field]: value }))
    setFieldErrors((previous) =>
      previous[field] === null
        ? previous
        : { ...previous, [field]: null },
    )
  }

  function applySubmitError(error: unknown): void {
    if (!(error instanceof ApiError)) {
      setFormError('Não foi possível conectar à API.')
      return
    }

    if (error.status === 409) {
      setFormError(error.message)
      if (error.message.includes('Estoque insuficiente')) {
        setFieldErrors({ ...NO_ERRORS, quantity: error.message })
      }
      return
    }

    const serverFieldErrors = toFieldErrors(error.errors)
    if (serverFieldErrors !== null) {
      setFieldErrors(serverFieldErrors)
      setFormError(null)
      return
    }

    setFormError(error.message)
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault()
    if (submitting) return

    setFormError(null)
    const validation = validate(values)
    setFieldErrors(validation)
    const hasErrors = Object.values(validation).some(
      (message) => message !== null,
    )
    if (hasErrors) return

    setSubmitting(true)
    try {
      await submit(toPayload(values, crypto.randomUUID()))
      setValues(INITIAL_VALUES)
      setFieldErrors(NO_ERRORS)
    } catch (error) {
      applySubmitError(error)
    } finally {
      setSubmitting(false)
    }
  }

  function handleReset(): void {
    setFormError(null)
    setFieldErrors(NO_ERRORS)
    setValues(INITIAL_VALUES)
  }

  return (
    <form className="entity-form" onSubmit={handleSubmit} noValidate>
      {formError !== null && (
        <p className="form-error" role="alert">
          {formError}
        </p>
      )}

      <SelecaoProduto
        id={idFor('produto_id')}
        label="Produto"
        value={values.produto_id}
        onChange={(value) => setValue('produto_id', value)}
        produtos={produtos}
        status={produtosStatus}
        emptyLabel="Selecione um produto"
        error={fieldErrors.produto_id}
        disabled={submitting}
      />

      <FieldShell
        id={idFor('tipo_movimentacao')}
        label="Tipo"
        error={fieldErrors.tipo_movimentacao}
      >
        {(aria) => (
          <select
            {...aria}
            name="tipo_movimentacao"
            value={values.tipo_movimentacao}
            onChange={(event) =>
              setValue('tipo_movimentacao', event.target.value)
            }
          >
            <option value="">Selecione o tipo</option>
            {TIPOS_MOVIMENTACAO.map((tipo) => (
              <option key={tipo} value={tipo}>
                {ROTULOS_TIPO_MOVIMENTACAO[tipo]}
              </option>
            ))}
          </select>
        )}
      </FieldShell>

      <FieldShell
        id={idFor('quantity')}
        label="Quantidade"
        error={fieldErrors.quantity}
      >
        {(aria) => (
          <input
            {...aria}
            name="quantity"
            type="text"
            inputMode="decimal"
            value={values.quantity}
            onChange={(event) => setValue('quantity', event.target.value)}
          />
        )}
      </FieldShell>

      <FieldShell
        id={idFor('reference')}
        label="Referência"
        error={fieldErrors.reference}
      >
        {(aria) => (
          <input
            {...aria}
            name="reference"
            type="text"
            value={values.reference}
            maxLength={LIMITS.reference}
            onChange={(event) => setValue('reference', event.target.value)}
          />
        )}
      </FieldShell>

      <FieldShell
        id={idFor('notes')}
        label="Observações"
        error={fieldErrors.notes}
        hint={`${values.notes.length} / ${LIMITS.notes}`}
      >
        {(aria) => (
          <textarea
            {...aria}
            name="notes"
            rows={3}
            value={values.notes}
            maxLength={LIMITS.notes}
            onChange={(event) => setValue('notes', event.target.value)}
          />
        )}
      </FieldShell>

      <div className="entity-form__actions">
        <button type="submit" disabled={submitting}>
          {submitting ? 'Registrando...' : 'Registrar movimentação'}
        </button>
        <button
          type="button"
          className="button--secondary"
          onClick={handleReset}
          disabled={submitting}
        >
          Limpar
        </button>
      </div>
    </form>
  )
}
