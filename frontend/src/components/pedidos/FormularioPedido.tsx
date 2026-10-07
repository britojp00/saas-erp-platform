import { useId, useState } from 'react'
import type { FormEvent } from 'react'
import { IconPlus, IconTrash } from '@tabler/icons-react'
import SelecaoProduto, {
  type StatusProdutos,
} from '../estoque/SelecaoProduto'
import { ApiError } from '../../services/api'
import type { ApiFieldError } from '../../services/api'
import type { Cliente } from '../../types/clientes'
import type { Produto } from '../../types/produtos'
import type {
  PedidoCriarPayload,
  ValoresFormItemPedido,
  ValoresFormularioPedido,
} from '../../types/pedidos'
import {
  normalizeDecimal,
  validatePrecoUnitario,
  validateQuantidade,
} from '../../utils/pedido'
import SelecaoCliente, { type StatusClientes } from './SelecaoCliente'
import FieldShell from './FieldShell'

type FieldErrors = Record<'cliente_id' | 'notes', string | null>

interface ItemFieldErrors {
  produto_id: string | null
  quantity: string | null
  unit_price: string | null
}

interface ValidationErrors {
  values: FieldErrors
  itens: ItemFieldErrors[]
}

const NOTES_LIMIT = 1000

const NO_ERRORS: FieldErrors = {
  cliente_id: null,
  notes: null,
}

const NO_ITEM_ERRORS: ItemFieldErrors = {
  produto_id: null,
  quantity: null,
  unit_price: null,
}

const BLANK_ITEM: ValoresFormItemPedido = {
  produto_id: '',
  quantity: '',
  unit_price: '',
}

export const INITIAL_VALUES_PEDIDO: ValoresFormularioPedido = {
  cliente_id: '',
  notes: '',
  itens: [{ ...BLANK_ITEM }],
}

function validateItem(item: ValoresFormItemPedido): ItemFieldErrors {
  const errors: ItemFieldErrors = { ...NO_ITEM_ERRORS }

  if (item.produto_id.trim() === '') {
    errors.produto_id = 'Informe o produto.'
  }
  errors.quantity = validateQuantidade(item.quantity)
  errors.unit_price = validatePrecoUnitario(item.unit_price)

  return errors
}

function validate(
  values: ValoresFormularioPedido,
): ValidationErrors {
  const errors: ValidationErrors = {
    values: { ...NO_ERRORS },
    itens: values.itens.map(() => ({ ...NO_ITEM_ERRORS })),
  }

  if (values.cliente_id.trim() === '') {
    errors.values.cliente_id = 'Informe o cliente.'
  }
  if (values.notes.length > NOTES_LIMIT) {
    errors.values.notes = `As observações devem ter no máximo ${NOTES_LIMIT} caracteres.`
  }

  values.itens.forEach((item, index) => {
    errors.itens[index] = validateItem(item)
  })

  const produtoIds = new Set<string>()
  values.itens.forEach((item, index) => {
    const produtoId = item.produto_id.trim()
    if (produtoId === '') return
    if (produtoIds.has(produtoId)) {
      errors.itens[index].produto_id = 'Este produto já foi adicionado.'
      return
    }
    produtoIds.add(produtoId)
  })

  return errors
}

function hasErrors(errors: ValidationErrors): boolean {
  if (errors.values.cliente_id !== null || errors.values.notes !== null) {
    return true
  }
  return errors.itens.some(
    (item) =>
      item.produto_id !== null ||
      item.quantity !== null ||
      item.unit_price !== null,
  )
}

function toPayload(values: ValoresFormularioPedido): PedidoCriarPayload {
  return {
    cliente_id: Number(values.cliente_id),
    notes: values.notes.trim() === '' ? null : values.notes.trim(),
    itens: values.itens.map((item) => ({
      produto_id: Number(item.produto_id),
      quantity: Number(normalizeDecimal(item.quantity)),
      ...(item.unit_price.trim() === ''
        ? {}
        : { unit_price: Number(normalizeDecimal(item.unit_price)) }),
    })),
  }
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

interface FormularioPedidoProps {
  initialValues: ValoresFormularioPedido
  submit: (values: PedidoCriarPayload) => Promise<unknown>
  submitLabel: string
  onCancel: () => void
  clientes: Cliente[]
  clientesStatus: StatusClientes
  produtos: Produto[]
  produtosStatus: StatusProdutos
}

export default function FormularioPedido({
  initialValues,
  submit,
  submitLabel,
  onCancel,
  clientes,
  clientesStatus,
  produtos,
  produtosStatus,
}: FormularioPedidoProps) {
  const formId = useId()
  const [values, setValues] = useState<ValoresFormularioPedido>(initialValues)
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>(NO_ERRORS)
  const [itensErrors, setItensErrors] = useState<ItemFieldErrors[]>(
    initialValues.itens.map(() => ({ ...NO_ITEM_ERRORS })),
  )
  const [formError, setFormError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  function setValue(field: 'cliente_id' | 'notes', value: string): void {
    setValues((previous) => ({ ...previous, [field]: value }))
    setFieldErrors((previous) =>
      previous[field] === null ? previous : { ...previous, [field]: null },
    )
  }

  function setItemValue(
    index: number,
    field: keyof ValoresFormItemPedido,
    value: string,
  ): void {
    setValues((previous) => ({
      ...previous,
      itens: previous.itens.map((item, position) =>
        position === index ? { ...item, [field]: value } : item,
      ),
    }))
    setItensErrors((previous) =>
      previous.map((item, position) => {
        if (position !== index) return item
        const next: ItemFieldErrors = { ...item }
        if (field === 'produto_id') next.produto_id = null
        else if (field === 'quantity') next.quantity = null
        else next.unit_price = null
        return next
      }),
    )
  }

  function addItem(): void {
    setValues((previous) => ({
      ...previous,
      itens: [...previous.itens, { ...BLANK_ITEM }],
    }))
    setItensErrors((previous) => [...previous, { ...NO_ITEM_ERRORS }])
  }

  function removeItem(index: number): void {
    setValues((previous) => {
      if (previous.itens.length <= 1) return previous
      return {
        ...previous,
        itens: previous.itens.filter((_, position) => position !== index),
      }
    })
    setItensErrors((previous) => {
      if (previous.length <= 1) return previous
      return previous.filter((_, position) => position !== index)
    })
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
    if (submitting) return

    setFormError(null)
    const validation = validate(values)
    setFieldErrors(validation.values)
    setItensErrors(validation.itens)
    if (hasErrors(validation)) return

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
    <form className="entity-form pedidos-form" onSubmit={handleSubmit} noValidate>
      {formError !== null && (
        <p className="form-error" role="alert">
          {formError}
        </p>
      )}

      <SelecaoCliente
        id={`${formId}-cliente_id`}
        label="Cliente"
        value={values.cliente_id}
        onChange={(value) => setValue('cliente_id', value)}
        clientes={clientes}
        status={clientesStatus}
        emptyLabel="Selecione um cliente"
        error={fieldErrors.cliente_id}
        disabled={submitting}
      />

      <FieldShell
        id={`${formId}-notes`}
        label="Observações"
        error={fieldErrors.notes}
        hint={`${values.notes.length} / ${NOTES_LIMIT}`}
      >
        {(aria) => (
          <textarea
            {...aria}
            name="notes"
            rows={4}
            value={values.notes}
            maxLength={NOTES_LIMIT}
            onChange={(event) => setValue('notes', event.target.value)}
          />
        )}
      </FieldShell>

      <fieldset className="pedidos-item-list">
        <legend>Itens do pedido</legend>

        {values.itens.map((item, index) => {
          const errors = itensErrors[index] ?? NO_ITEM_ERRORS
          const itemFormId = `${formId}-item-${index}`

          return (
            <div className="pedidos-item-row" key={itemFormId}>
              <div className="pedidos-item-row__header">
                <span className="pedidos-item-row__title">
                  Item {index + 1}
                </span>
                <button
                  type="button"
                  className="pedidos-table__action pedidos-table__action--danger"
                  disabled={submitting || values.itens.length <= 1}
                  aria-label={`Remover item ${index + 1}`}
                  onClick={() => removeItem(index)}
                >
                  <IconTrash size={16} aria-hidden="true" />
                  Remover
                </button>
              </div>

              <div className="pedidos-item-row__fields">
                <SelecaoProduto
                  id={`${itemFormId}-produto_id`}
                  label="Produto"
                  value={item.produto_id}
                  onChange={(value) => setItemValue(index, 'produto_id', value)}
                  produtos={produtos}
                  status={produtosStatus}
                  emptyLabel="Selecione um produto"
                  error={errors.produto_id}
                  disabled={submitting}
                />

                <FieldShell
                  id={`${itemFormId}-quantity`}
                  label="Quantidade"
                  error={errors.quantity}
                >
                  {(aria) => (
                    <input
                      {...aria}
                      name={`${itemFormId}-quantity`}
                      type="text"
                      inputMode="decimal"
                      value={item.quantity}
                      onChange={(event) =>
                        setItemValue(index, 'quantity', event.target.value)
                      }
                    />
                  )}
                </FieldShell>

                <FieldShell
                  id={`${itemFormId}-unit_price`}
                  label="Preço unitário"
                  error={errors.unit_price}
                >
                  {(aria) => (
                    <input
                      {...aria}
                      name={`${itemFormId}-unit_price`}
                      type="text"
                      inputMode="decimal"
                      value={item.unit_price}
                      placeholder="Preço do produto"
                      onChange={(event) =>
                        setItemValue(index, 'unit_price', event.target.value)
                      }
                    />
                  )}
                </FieldShell>
              </div>
            </div>
          )
        })}
      </fieldset>

      <div className="pedidos-item-list__add">
        <button type="button" onClick={addItem} disabled={submitting}>
          <IconPlus size={16} aria-hidden="true" />
          Adicionar item
        </button>
      </div>

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
