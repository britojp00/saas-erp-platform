import { useEffect, useId, useRef, useState } from 'react'
import type { FormEvent, ReactNode } from 'react'
import { ApiError, api } from '../../services/api'
import type { ApiFieldError } from '../../services/api'
import type { ListaCategoriasResposta } from '../../types/categorias'
import type {
  ProdutoCriarPayload,
  ValoresFormularioProduto,
} from '../../types/produtos'

type FieldName = keyof ValoresFormularioProduto

type FieldErrors = Record<FieldName, string | null>

const CATEGORIAS_OPTIONS_QUERY =
  '/api/v1/categorias?page=1&page_size=100&sort=name&order=asc'

const LIMITS = {
  sku: 50,
  name: 150,
  description: 5000,
} as const

const NO_ERRORS: FieldErrors = {
  sku: null,
  name: null,
  description: null,
  categoria_id: null,
  price: null,
  cost_price: null,
  is_active: null,
}

const MONEY_PATTERN = /^\d{1,13}(\.\d{1,2})?$/
const MONEY_DECIMALS_PATTERN = /^\d+(\.\d{3,})$/
const MONEY_DIGITS_PATTERN = /^\d{14,}(\.\d+)?$/

function normalizeMoney(value: string): string {
  return value.trim().replace(',', '.')
}

function validateMoney(
  raw: string,
  label: string,
  required: boolean,
  negativeMessage: string,
): string | null {
  const value = raw.trim()
  if (value === '') {
    return required ? `Informe o ${label}.` : null
  }
  if (value.startsWith('-')) {
    return negativeMessage
  }

  const normalized = normalizeMoney(value)
  if (MONEY_PATTERN.test(normalized)) return null
  if (MONEY_DECIMALS_PATTERN.test(normalized)) {
    return `O ${label} deve ter no máximo 2 casas decimais.`
  }
  if (MONEY_DIGITS_PATTERN.test(normalized)) {
    return `O ${label} deve ter no máximo 15 dígitos.`
  }
  return `Informe um valor decimal válido para o ${label} (ex.: 99,90).`
}

export interface FormularioProdutoProps {
  initialValues: ValoresFormularioProduto
  submit: (values: ProdutoCriarPayload) => Promise<unknown>
  submitLabel: string
  onCancel: () => void
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

function validate(values: ValoresFormularioProduto): FieldErrors {
  const errors: FieldErrors = { ...NO_ERRORS }

  const sku = values.sku.trim()
  if (sku === '') {
    errors.sku = 'Informe o SKU.'
  } else if (sku.length > LIMITS.sku) {
    errors.sku = `O SKU deve ter no máximo ${LIMITS.sku} caracteres.`
  }

  const name = values.name.trim()
  if (name === '') {
    errors.name = 'Informe o nome do produto.'
  } else if (name.length > LIMITS.name) {
    errors.name = `O nome deve ter no máximo ${LIMITS.name} caracteres.`
  }

  if (values.description.length > LIMITS.description) {
    errors.description = `A descrição deve ter no máximo ${LIMITS.description} caracteres.`
  }

  errors.price = validateMoney(
    values.price,
    'preço',
    true,
    'O preço não pode ser negativo.',
  )
  errors.cost_price = validateMoney(
    values.cost_price,
    'preço de custo',
    false,
    'O preço de custo não pode ser negativo.',
  )

  return errors
}

function toPayload(values: ValoresFormularioProduto): ProdutoCriarPayload {
  return {
    sku: values.sku.trim(),
    name: values.name.trim(),
    description: values.description === '' ? null : values.description,
    categoria_id:
      values.categoria_id === '' ? null : Number(values.categoria_id),
    price: normalizeMoney(values.price),
    cost_price:
      values.cost_price.trim() === '' ? null : normalizeMoney(values.cost_price),
    is_active: values.is_active === 'true',
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

export default function FormularioProduto({
  initialValues,
  submit,
  submitLabel,
  onCancel,
}: FormularioProdutoProps) {
  const formId = useId()
  const [values, setValues] = useState<ValoresFormularioProduto>(initialValues)
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>(NO_ERRORS)
  const [formError, setFormError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  const [categoriaOptions, setCategoriaOptions] = useState<
    ListaCategoriasResposta['items']
  >([])
  const [categoriasStatus, setCategoriasStatus] = useState<
    'carregando' | 'erro' | 'pronto'
  >('carregando')
  const categoriasSequence = useRef(0)

  useEffect(() => {
    const current = ++categoriasSequence.current
    setCategoriasStatus('carregando')

    async function loadCategorias(): Promise<void> {
      try {
        const response = await api.get<ListaCategoriasResposta>(
          CATEGORIAS_OPTIONS_QUERY,
        )
        if (current !== categoriasSequence.current) return
        setCategoriaOptions(response.items)
        setCategoriasStatus('pronto')
      } catch {
        if (current !== categoriasSequence.current) return
        setCategoriaOptions([])
        setCategoriasStatus('erro')
      }
    }

    void loadCategorias()
  }, [])

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
      if (error.message.includes('SKU')) {
        setFieldErrors({ ...NO_ERRORS, sku: error.message })
      } else if (error.message.includes('categoria')) {
        setFieldErrors({ ...NO_ERRORS, categoria_id: error.message })
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
      await submit(toPayload(values))
    } catch (error) {
      applySubmitError(error)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <form className="entity-form" onSubmit={handleSubmit} noValidate>
      {formError !== null && (
        <p className="form-error" role="alert">
          {formError}
        </p>
      )}

      <FieldShell id={idFor('sku')} label="SKU" error={fieldErrors.sku}>
        {(aria) => (
          <input
            {...aria}
            name="sku"
            type="text"
            value={values.sku}
            maxLength={LIMITS.sku}
            onChange={(event) => setValue('sku', event.target.value)}
          />
        )}
      </FieldShell>

      <FieldShell id={idFor('name')} label="Nome" error={fieldErrors.name}>
        {(aria) => (
          <input
            {...aria}
            name="name"
            type="text"
            value={values.name}
            maxLength={LIMITS.name}
            onChange={(event) => setValue('name', event.target.value)}
          />
        )}
      </FieldShell>

      <FieldShell
        id={idFor('description')}
        label="Descrição"
        error={fieldErrors.description}
        hint={`${values.description.length} / ${LIMITS.description}`}
      >
        {(aria) => (
          <textarea
            {...aria}
            name="description"
            rows={5}
            value={values.description}
            maxLength={LIMITS.description}
            onChange={(event) => setValue('description', event.target.value)}
          />
        )}
      </FieldShell>

      <FieldShell
        id={idFor('categoria_id')}
        label="Categoria"
        error={fieldErrors.categoria_id}
        hint={
          categoriasStatus === 'erro'
            ? 'Não foi possível carregar a lista de categorias.'
            : undefined
        }
      >
        {(aria) => (
          <select
            {...aria}
            name="categoria_id"
            value={values.categoria_id}
            disabled={categoriasStatus !== 'pronto'}
            onChange={(event) => setValue('categoria_id', event.target.value)}
          >
            {categoriasStatus === 'carregando' ? (
              <option value="">Carregando categorias...</option>
            ) : categoriasStatus === 'erro' ? (
              <option value="">Categorias indisponíveis</option>
            ) : (
              <option value="">Sem categoria</option>
            )}
            {categoriasStatus === 'pronto' &&
              categoriaOptions.map((option) => (
                <option key={option.id} value={option.id}>
                  {option.name}
                </option>
              ))}
            {categoriasStatus === 'pronto' &&
              values.categoria_id !== '' &&
              !categoriaOptions.some(
                (option) => String(option.id) === values.categoria_id,
              ) && (
                <option value={values.categoria_id}>Categoria atual</option>
              )}
          </select>
        )}
      </FieldShell>

      <FieldShell id={idFor('price')} label="Preço" error={fieldErrors.price}>
        {(aria) => (
          <input
            {...aria}
            name="price"
            type="text"
            inputMode="decimal"
            value={values.price}
            onChange={(event) => setValue('price', event.target.value)}
          />
        )}
      </FieldShell>

      <FieldShell
        id={idFor('cost_price')}
        label="Preço de custo"
        error={fieldErrors.cost_price}
      >
        {(aria) => (
          <input
            {...aria}
            name="cost_price"
            type="text"
            inputMode="decimal"
            value={values.cost_price}
            onChange={(event) => setValue('cost_price', event.target.value)}
          />
        )}
      </FieldShell>

      <FieldShell
        id={idFor('is_active')}
        label="Situação"
        error={fieldErrors.is_active}
      >
        {(aria) => (
          <select
            {...aria}
            name="is_active"
            value={values.is_active}
            onChange={(event) => setValue('is_active', event.target.value)}
          >
            <option value="true">Ativo</option>
            <option value="false">Inativo</option>
          </select>
        )}
      </FieldShell>

      <div className="entity-form__actions">
        <button type="submit" disabled={submitting}>
          {submitting ? 'Salvando...' : submitLabel}
        </button>
        <button
          type="button"
          className="button--secondary"
          onClick={onCancel}
          disabled={submitting}
        >
          Cancelar
        </button>
      </div>
    </form>
  )
}
