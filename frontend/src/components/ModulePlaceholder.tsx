interface ModulePlaceholderProps {
  title: string
  description: string
}

export default function ModulePlaceholder({
  title,
  description,
}: ModulePlaceholderProps) {
  return (
    <section className="module-placeholder">
      <h1>{title}</h1>
      <p className="muted">{description}</p>
      <div className="module-placeholder__card">
        <p>
          Módulo em construção. A navegação e a estrutura do aplicativo já
          estão disponíveis para esta área.
        </p>
      </div>
    </section>
  )
}
