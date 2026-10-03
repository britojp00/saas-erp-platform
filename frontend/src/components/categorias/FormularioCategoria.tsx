import { useEffect, useId, useRef, useState } from 'react'
import type { FormEvent, ReactNode } from 'react'
import { ApiError, api } from '../../services/api'
import type { ApiFieldError } from '../../services/api'
import type {
  CategoriaCriarPayload,
  ListaCategoriasResposta,
  ValoresFormularioCategoria,
} from '../../types/categorias'

type FieldName = keyof ValoresFormularioCategoria

type FieldErrors = Record<FieldName, string | null>

const PARENT_OPTIONS_QUERY = '/api/v1/categorias?page=1&page_size=100&sort=name&order=asc'

const LIMITS = {
  name: 100,
  description: 5000,
} as const

const NO_ERRORS: FieldErrors = {
  name: null,
  description: null,
  parent_id: null,
}

export interface FormularioCategoriaProps {
  initialValues: ValoresFormularioCategoria
  submit: (values: CategoriaCriarPayload) => Promise<unknown>
  submitLabel: string
  onCancel: () => void
  excludeId?: number
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

function validate(values: ValoresFormularioCategoria): FieldErrors {
  const errors: FieldErrors = { ...NO_ERRORS }

  const name = values.name.trim()
  if (name === '') {
    errors.name = 'Informe o nome da categoria.'
  } else if (name.length > LIMITS.name) {
    errors.name = `O nome deve ter no máximo ${LIMITS.name} caracteres.`
  }

  if (values.description.length > LIMITS.description) {
    errors.description = `A descrição deve ter no máximo ${LIMITS.description} caracteres.`
  }

  return errors
}

function toPayload(values: ValoresFormularioCategoria): CategoriaCriarPayload {
  return {
    name: values.name.trim(),
    description: values.description === '' ? null : values.description,
    parent_id: values.parent_id === '' ? null : Number(values.parent_id),
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

export default function FormularioCategoria({
  initialValues,
  submit,
  submitLabel,
  onCancel,
  excludeId,
}: FormularioCategoriaProps) {
  const formId = useId()
  const [values, setValues] = useState<ValoresFormularioCategoria>(
    initialValues,
  )
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>(NO_ERRORS)
  const [formError, setFormError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  const [parentOptions, setParentOptions] = useState<
    ListaCategoriasResposta['items']
  >([])
  const [parentsStatus, setParentsStatus] = useState<
    'carregando' | 'erro' | 'pronto'
  >('carregando')
  const parentsSequence = useRef(0)

  useEffect(() => {
    const current = ++parentsSequence.current
    setParentsStatus('carregando')

    async function loadParents(): Promise<void> {
      try {
        const response = await api.get<ListaCategoriasResposta>(
          PARENT_OPTIONS_QUERY,
        )
        if (current !== parentsSequence.current) return
        setParentOptions(response.items)
        setParentsStatus('pronto')
      } catch {
        if (current !== parentsSequence.current) return
        setParentOptions([])
        setParentsStatus('erro')
      }
    }

    void loadParents()
  }, [])

  const visibleOptions = parentOptions.filter(
    (option) => option.id !== excludeId,
  )

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
        id={idFor('parent_id')}
        label="Categoria pai"
        error={fieldErrors.parent_id}
        hint={
          parentsStatus === 'erro'
            ? 'Não foi possível carregar a lista de categorias pai.'
            : undefined
        }
      >
        {(aria) => (
          <select
            {...aria}
            name="parent_id"
            value={values.parent_id}
            disabled={parentsStatus !== 'pronto'}
            onChange={(event) => setValue('parent_id', event.target.value)}
          >
            {parentsStatus === 'carregando' ? (
              <option value="">Carregando categorias...</option>
            ) : parentsStatus === 'erro' ? (
              <option value="">Categorias indisponíveis</option>
            ) : (
              <option value="">Nenhuma categoria pai</option>
            )}
            {parentsStatus === 'pronto' &&
              visibleOptions.map((option) => (
                <option key={option.id} value={option.id}>
                  {option.name}
                </option>
              ))}
            {parentsStatus === 'pronto' &&
              values.parent_id !== '' &&
              !visibleOptions.some(
                (option) => String(option.id) === values.parent_id,
              ) && (
                <option value={values.parent_id}>Categoria pai atual</option>
              )}
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
