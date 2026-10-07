import type { ReactNode } from 'react'

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

export default function FieldShell({
  id,
  label,
  error,
  hint,
  children,
}: FieldShellProps) {
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
