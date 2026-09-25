interface SectionLoadingProps {
  label: string
}

export function SectionLoading({ label }: SectionLoadingProps) {
  return (
    <p className="section-state" role="status">
      {label}
    </p>
  )
}

interface SectionErrorProps {
  message: string
  onRetry: () => void
}

export function SectionError({ message, onRetry }: SectionErrorProps) {
  return (
    <div className="section-error" role="alert">
      <p>{message}</p>
      <button type="button" onClick={onRetry}>
        Tentar novamente
      </button>
    </div>
  )
}
