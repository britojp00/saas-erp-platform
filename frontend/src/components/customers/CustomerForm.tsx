import { useId, useState } from 'react'
import type { FormEvent, ReactNode } from 'react'
import { ApiError } from '../../services/api'
import type { ApiFieldError } from '../../services/api'
import type { CustomerCreatePayload, CustomerFormValues } from '../../types/customers'

type FieldName = keyof CustomerFormValues

type FieldErrors = Record<FieldName, string | null>

const LIMITS = {
  name: 150,
  document: 30,
  email: 255,
  phone: 30,
  notes: 5000,
} as const

const NO_ERRORS: FieldErrors = {
  name: null,
  document: null,
  email: null,
  phone: null,
  notes: null,
}

export interface CustomerFormProps {
  initialValues: CustomerFormValues
  submit: (values: CustomerCreatePayload) => Promise<unknown>
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

function validate(values: CustomerFormValues): FieldErrors {
  const errors: FieldErrors = { ...NO_ERRORS }

  const name = values.name.trim()
  if (name === '') {
    errors.name = 'Informe o nome do cliente.'
  } else if (name.length > LIMITS.name) {
    errors.name = `O nome deve ter no máximo ${LIMITS.name} caracteres.`
  }

  if (values.document.trim().length > LIMITS.document) {
    errors.document = `O documento deve ter no máximo ${LIMITS.document} caracteres.`
  }
  if (values.email.trim().length > LIMITS.email) {
    errors.email = `O e-mail deve ter no máximo ${LIMITS.email} caracteres.`
  }
  if (values.phone.trim().length > LIMITS.phone) {
    errors.phone = `O telefone deve ter no máximo ${LIMITS.phone} caracteres.`
  }
  if (values.notes.length > LIMITS.notes) {
    errors.notes = `As observações devem ter no máximo ${LIMITS.notes} caracteres.`
  }

  return errors
}

function toPayload(values: CustomerFormValues): CustomerCreatePayload {
  const optional = (value: string): string | null =>
    value.trim() === '' ? null : value.trim()

  return {
    name: values.name.trim(),
    document: optional(values.document),
    email: optional(values.email),
    phone: optional(values.phone),
    notes: values.notes === '' ? null : values.notes,
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

export default function CustomerForm({
  initialValues,
  submit,
  submitLabel,
  onCancel,
}: CustomerFormProps) {
  const formId = useId()
  const [values, setValues] = useState<CustomerFormValues>(initialValues)
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
      setFieldErrors({ ...NO_ERRORS, document: error.message })
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
        id={idFor('document')}
        label="Documento"
        error={fieldErrors.document}
      >
        {(aria) => (
          <input
            {...aria}
            name="document"
            type="text"
            value={values.document}
            maxLength={LIMITS.document}
            onChange={(event) => setValue('document', event.target.value)}
          />
        )}
      </FieldShell>

      <FieldShell
        id={idFor('email')}
        label="E-mail"
        error={fieldErrors.email}
      >
        {(aria) => (
          <input
            {...aria}
            name="email"
            type="text"
            value={values.email}
            maxLength={LIMITS.email}
            onChange={(event) => setValue('email', event.target.value)}
          />
        )}
      </FieldShell>

      <FieldShell
        id={idFor('phone')}
        label="Telefone"
        error={fieldErrors.phone}
      >
        {(aria) => (
          <input
            {...aria}
            name="phone"
            type="text"
            value={values.phone}
            maxLength={LIMITS.phone}
            onChange={(event) => setValue('phone', event.target.value)}
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
            rows={5}
            value={values.notes}
            maxLength={LIMITS.notes}
            onChange={(event) => setValue('notes', event.target.value)}
          />
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
