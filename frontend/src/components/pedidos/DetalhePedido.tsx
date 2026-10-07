import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { ApiError } from '../../services/api'
import type { ApiFieldError } from '../../services/api'
import type { Cliente } from '../../types/clientes'
import type { Pedido, ValoresFormularioPedido } from '../../types/pedidos'
import { badgeStatusPedido, rotuloStatusPedido } from '../../types/pedidos'
import { formatAmount, formatDateTime } from '../../utils/format'
import FieldShell from './FieldShell'
import SelecaoCliente, { type StatusClientes } from './SelecaoCliente'

type FieldErrors = Record<'cliente_id' | 'notes', string | null>

const NOTES_LIMIT = 1000

const NO_ERRORS: FieldErrors = {
  cliente_id: null,
  notes: null,
}

function toFieldErrors(errors: ApiFieldError[]): FieldErrors | null {
  if (errors.length === 0) return null
  const next: FieldErrors = { ...NO_ERRORS }
  let mapped = false
  for (const { field, message } of errors) {
    if (field === 'cliente_id' || field === 'notes') {
      next[field] = message
      mapped = true
    }
  }
  return mapped ? next : null
}

interface DetalhePedidoProps {
  pedido: Pedido
  clientes: Cliente[]
  clientesStatus: StatusClientes
  onSalvar: (values: Pick<ValoresFormularioPedido, 'cliente_id' | 'notes'>) => Promise<void>
}

function clienteLabel(pedido: Pedido, clientes: Cliente[]): string {
  const cliente = clientes.find((item) => item.id === pedido.cliente_id)
  return cliente?.name ?? `Cliente #${pedido.cliente_id}`
}

export default function DetalhePedido({
  pedido,
  clientes,
  clientesStatus,
  onSalvar,
}: DetalhePedidoProps) {
  const editando = pedido.status === 'RASCUNHO'
  const [draft, setDraft] = useState({
    cliente_id: String(pedido.cliente_id),
    notes: pedido.notes ?? '',
  })
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>(NO_ERRORS)
  const [formError, setFormError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    setDraft({ cliente_id: String(pedido.cliente_id), notes: pedido.notes ?? '' })
    setFieldErrors(NO_ERRORS)
    setFormError(null)
  }, [pedido.id, pedido.cliente_id, pedido.notes, pedido.updated_at])

  function setValue(field: keyof FieldErrors, value: string): void {
    setDraft((previous) => ({ ...previous, [field]: value }))
    setFieldErrors((previous) =>
      previous[field] === null ? previous : { ...previous, [field]: null },
    )
  }

  function reset(): void {
    setDraft({ cliente_id: String(pedido.cliente_id), notes: pedido.notes ?? '' })
    setFieldErrors(NO_ERRORS)
    setFormError(null)
  }

  function applySubmitError(error: unknown): void {
    if (!(error instanceof ApiError)) {
      setFormError('Não foi possível conectar à API.')
      return
    }

    if (error.status === 409) {
      setFormError(error.message)
      if (error.message.toLowerCase().includes('cliente')) {
        setFieldErrors({ ...NO_ERRORS, cliente_id: error.message })
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
    if (saving) return

    const validation: FieldErrors = { ...NO_ERRORS }
    if (draft.cliente_id.trim() === '') {
      validation.cliente_id = 'Informe o cliente.'
    }
    if (draft.notes.length > NOTES_LIMIT) {
      validation.notes = `As observações devem ter no máximo ${NOTES_LIMIT} caracteres.`
    }
    setFieldErrors(validation)
    setFormError(null)
    if (validation.cliente_id !== null || validation.notes !== null) return

    setSaving(true)
    try {
      await onSalvar(draft)
    } catch (error) {
      applySubmitError(error)
    } finally {
      setSaving(false)
    }
  }

  return (
    <>
      <div className="panel">
        <h2>Pedido</h2>
        <dl className="detail-list">
          <dt>Número</dt>
          <dd>#{pedido.numero_pedido}</dd>
          <dt>Status</dt>
          <dd>
            <span className={badgeStatusPedido(pedido.status)}>
              {rotuloStatusPedido(pedido.status)}
            </span>
          </dd>
          {!editando && (
            <>
              <dt>Cliente</dt>
              <dd>{clienteLabel(pedido, clientes)}</dd>
            </>
          )}
          <dt>Total</dt>
          <dd>{formatAmount(pedido.total_amount)}</dd>
          {!editando && (
            <>
              <dt>Observações</dt>
              <dd>
                {pedido.notes !== null && pedido.notes !== '' ? (
                  pedido.notes
                ) : (
                  <span className="muted">—</span>
                )}
              </dd>
            </>
          )}
          <dt>Criado em</dt>
          <dd>{formatDateTime(pedido.created_at)}</dd>
          <dt>Atualizado em</dt>
          <dd>{formatDateTime(pedido.updated_at)}</dd>
        </dl>
      </div>

      {editando && (
        <div className="panel">
          <h2>Editar pedido</h2>
          <form className="entity-form" onSubmit={handleSubmit} noValidate>
            {formError !== null && (
              <p className="form-error" role="alert">
                {formError}
              </p>
            )}

            <SelecaoCliente
              id="pedido-detalhe-cliente"
              label="Cliente"
              value={draft.cliente_id}
              onChange={(value) => setValue('cliente_id', value)}
              clientes={clientes}
              status={clientesStatus}
              emptyLabel="Selecione um cliente"
              error={fieldErrors.cliente_id}
              disabled={saving}
            />

            <FieldShell
              id="pedido-detalhe-notes"
              label="Observações"
              error={fieldErrors.notes}
              hint={`${draft.notes.length} / ${NOTES_LIMIT}`}
            >
              {(aria) => (
                <textarea
                  {...aria}
                  name="notes"
                  rows={4}
                  value={draft.notes}
                  maxLength={NOTES_LIMIT}
                  onChange={(event) => setValue('notes', event.target.value)}
                />
              )}
            </FieldShell>

            <div className="entity-form__actions">
              <button type="submit" disabled={saving}>
                {saving ? 'Salvando...' : 'Salvar'}
              </button>
              <button
                type="button"
                className="button--secondary"
                onClick={reset}
                disabled={saving}
              >
                Descartar
              </button>
            </div>
          </form>
        </div>
      )}
    </>
  )
}
