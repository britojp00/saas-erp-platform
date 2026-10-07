import { useEffect, useId, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { IconCheck, IconPlus, IconTrash, IconX } from '@tabler/icons-react'
import SelecaoProduto, { type StatusProdutos } from '../estoque/SelecaoProduto'
import { ApiError } from '../../services/api'
import type { ApiFieldError } from '../../services/api'
import type { Produto } from '../../types/produtos'
import type {
  Pedido,
  PedidoItem,
  ValoresFormItemPedido,
} from '../../types/pedidos'
import { formatAmount, formatQuantity } from '../../utils/format'
import {
  normalizeDecimal,
  validatePrecoUnitario,
  validateQuantidade,
} from '../../utils/pedido'
import FieldShell from './FieldShell'

interface ItemFormErrors {
  produto_id: string | null
  quantity: string | null
  unit_price: string | null
}

const NO_ERRORS: ItemFormErrors = {
  produto_id: null,
  quantity: null,
  unit_price: null,
}

const BLANK_ITEM: ValoresFormItemPedido = {
  produto_id: '',
  quantity: '',
  unit_price: '',
}

function produtoLabel(produtoId: number, produtos: Produto[]): string {
  const produto = produtos.find((item) => item.id === produtoId)
  return produto?.name ?? `Produto #${produtoId}`
}

function toFieldErrors(errors: ApiFieldError[]): ItemFormErrors | null {
  if (errors.length === 0) return null
  const next: ItemFormErrors = { ...NO_ERRORS }
  let mapped = false
  for (const { field, message } of errors) {
    if (field === 'quantity' || field === 'unit_price') {
      next[field] = message
      mapped = true
    }
  }
  return mapped ? next : null
}

interface ItemSubmitResult {
  fields: ItemFormErrors | null
  message: string | null
}

function applyItemError(error: unknown): ItemSubmitResult {
  if (!(error instanceof ApiError)) {
    return { fields: null, message: 'Não foi possível salvar o item.' }
  }
  if (error.status === 422) {
    const fields = toFieldErrors(error.errors)
    if (fields !== null) return { fields, message: null }
  }
  return { fields: null, message: error.message }
}

interface ItemRowProps {
  item: PedidoItem
  produtos: Produto[]
  editando: boolean
  podeRemover: boolean
  onSalvar: (values: { quantity: string; unit_price: string }) => Promise<void>
  onRemover: () => Promise<void>
}

function ItemRow({
  item,
  produtos,
  editando,
  podeRemover,
  onSalvar,
  onRemover,
}: ItemRowProps) {
  const rowId = `pedido-item-${item.id}`
  const produto = produtoLabel(item.produto_id, produtos)
  const [quantity, setQuantity] = useState(String(item.quantity))
  const [unitPrice, setUnitPrice] = useState(item.unit_price.toFixed(2))
  const [errors, setErrors] = useState<ItemFormErrors>(NO_ERRORS)
  const [message, setMessage] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)
  const [removing, setRemoving] = useState(false)
  const [confirming, setConfirming] = useState(false)
  const confirmButtonRef = useRef<HTMLButtonElement | null>(null)

  useEffect(() => {
    setQuantity(String(item.quantity))
    setUnitPrice(item.unit_price.toFixed(2))
    setErrors(NO_ERRORS)
    setMessage(null)
    setConfirming(false)
  }, [item.id, item.quantity, item.unit_price])

  useEffect(() => {
    if (confirming) confirmButtonRef.current?.focus()
  }, [confirming])

  async function handleSave(): Promise<void> {
    if (saving) return

    const next: ItemFormErrors = {
      ...NO_ERRORS,
      quantity: validateQuantidade(quantity),
      unit_price: validatePrecoUnitario(unitPrice),
    }
    setErrors(next)
    setMessage(null)
    if (next.quantity !== null || next.unit_price !== null) return

    setSaving(true)
    try {
      await onSalvar({
        quantity: normalizeDecimal(quantity),
        unit_price: unitPrice.trim() === '' ? '' : normalizeDecimal(unitPrice),
      })
    } catch (error) {
      const result = applyItemError(error)
      if (result.fields !== null) setErrors(result.fields)
      if (result.message !== null) setMessage(result.message)
    } finally {
      setSaving(false)
    }
  }

  async function handleRemove(): Promise<void> {
    if (removing) return

    setRemoving(true)
    setMessage(null)
    try {
      await onRemover()
    } catch (error) {
      setMessage(
        error instanceof ApiError
          ? error.message
          : 'Não foi possível remover o item.',
      )
    } finally {
      setRemoving(false)
      setConfirming(false)
    }
  }

  if (!editando) {
    return (
      <tr>
        <td>{produto}</td>
        <td>{formatQuantity(item.quantity)}</td>
        <td>{formatAmount(item.unit_price)}</td>
        <td>{formatAmount(item.total_price)}</td>
      </tr>
    )
  }

  return (
    <tr>
      <td>
        <div
          className="pedidos-table__actions"
          role="group"
          aria-label={`Ações do item ${produto}`}
        >
          {confirming ? (
            <>
              <span className="pedidos-table__confirm-text" role="status">
                Remover este item?
              </span>
              <button
                ref={confirmButtonRef}
                type="button"
                className="pedidos-table__action pedidos-table__action--danger"
                disabled={removing}
                aria-busy={removing}
                aria-label={`Confirmar remoção do item ${produto}`}
                onClick={() => {
                  void handleRemove()
                }}
              >
                {removing ? (
                  <>
                    <span
                      className="pedidos-table__spinner"
                      aria-hidden="true"
                    />
                    Removendo...
                  </>
                ) : (
                  <>
                    <IconCheck size={16} aria-hidden="true" />
                    Confirmar
                  </>
                )}
              </button>
              <button
                type="button"
                className="pedidos-table__action"
                disabled={removing}
                aria-label={`Descartar remoção do item ${produto}`}
                onClick={() => setConfirming(false)}
              >
                <IconX size={16} aria-hidden="true" />
                Cancelar
              </button>
            </>
          ) : (
            <>
              <button
                type="button"
                className="pedidos-table__action"
                disabled={saving}
                aria-busy={saving}
                aria-label={`Salvar item ${produto}`}
                onClick={() => {
                  void handleSave()
                }}
              >
                {saving ? (
                  <>
                    <span
                      className="pedidos-table__spinner"
                      aria-hidden="true"
                    />
                    Salvando...
                  </>
                ) : (
                  <>
                    <IconCheck size={16} aria-hidden="true" />
                    Salvar
                  </>
                )}
              </button>
              <button
                type="button"
                className="pedidos-table__action pedidos-table__action--danger"
                disabled={!podeRemover}
                aria-label={`Remover item ${produto}`}
                onClick={() => setConfirming(true)}
              >
                <IconTrash size={16} aria-hidden="true" />
                Remover
              </button>
            </>
          )}
        </div>
        {message !== null && (
          <p className="pedidos-table__message" role="alert">
            {message}
          </p>
        )}
      </td>
      <td>{produto}</td>
      <td>
        <FieldShell
          id={`${rowId}-quantity`}
          label="Quantidade"
          error={errors.quantity}
        >
          {(aria) => (
            <input
              {...aria}
              type="text"
              inputMode="decimal"
              value={quantity}
              onChange={(event) => setQuantity(event.target.value)}
            />
          )}
        </FieldShell>
      </td>
      <td>
        <FieldShell
          id={`${rowId}-unit_price`}
          label="Preço unitário"
          error={errors.unit_price}
        >
          {(aria) => (
            <input
              {...aria}
              type="text"
              inputMode="decimal"
              value={unitPrice}
              onChange={(event) => setUnitPrice(event.target.value)}
            />
          )}
        </FieldShell>
      </td>
      <td>{formatAmount(item.total_price)}</td>
    </tr>
  )
}

interface AdicionarItemProps {
  produtos: Produto[]
  produtosStatus: StatusProdutos
  onAdicionar: (values: ValoresFormItemPedido) => Promise<void>
}

function AdicionarItem({
  produtos,
  produtosStatus,
  onAdicionar,
}: AdicionarItemProps) {
  const formId = useId()
  const [values, setValues] = useState<ValoresFormItemPedido>({
    ...BLANK_ITEM,
  })
  const [errors, setErrors] = useState<ItemFormErrors>(NO_ERRORS)
  const [message, setMessage] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  function setValue(field: keyof ValoresFormItemPedido, value: string): void {
    setValues((previous) => ({ ...previous, [field]: value }))
    setErrors((previous) => {
      const current = previous[field]
      if (current === null) return previous
      const next: ItemFormErrors = { ...previous }
      if (field === 'produto_id') next.produto_id = null
      else if (field === 'quantity') next.quantity = null
      else next.unit_price = null
      return next
    })
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault()
    if (saving) return

    const next: ItemFormErrors = {
      ...NO_ERRORS,
      produto_id:
        values.produto_id.trim() === '' ? 'Informe o produto.' : null,
      quantity: validateQuantidade(values.quantity),
      unit_price: validatePrecoUnitario(values.unit_price),
    }
    setErrors(next)
    setMessage(null)
    if (
      next.produto_id !== null ||
      next.quantity !== null ||
      next.unit_price !== null
    ) {
      return
    }

    setSaving(true)
    try {
      await onAdicionar({
        ...values,
        quantity: normalizeDecimal(values.quantity),
        unit_price:
          values.unit_price.trim() === ''
            ? ''
            : normalizeDecimal(values.unit_price),
      })
      setValues({ ...BLANK_ITEM })
    } catch (error) {
      const result = applyItemError(error)
      if (result.fields !== null) setErrors(result.fields)
      if (result.message !== null) setMessage(result.message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <form className="pedidos-item-add" onSubmit={handleSubmit} noValidate>
      <h3>Adicionar item</h3>

      {message !== null && (
        <p className="form-error" role="alert">
          {message}
        </p>
      )}

      <div className="pedidos-item-add__fields">
        <SelecaoProduto
          id={`${formId}-produto_id`}
          label="Produto"
          value={values.produto_id}
          onChange={(value) => setValue('produto_id', value)}
          produtos={produtos}
          status={produtosStatus}
          emptyLabel="Selecione um produto"
          error={errors.produto_id}
          disabled={saving}
        />

        <FieldShell
          id={`${formId}-quantity`}
          label="Quantidade"
          error={errors.quantity}
        >
          {(aria) => (
            <input
              {...aria}
              type="text"
              inputMode="decimal"
              value={values.quantity}
              onChange={(event) => setValue('quantity', event.target.value)}
            />
          )}
        </FieldShell>

        <FieldShell
          id={`${formId}-unit_price`}
          label="Preço unitário"
          error={errors.unit_price}
        >
          {(aria) => (
            <input
              {...aria}
              type="text"
              inputMode="decimal"
              placeholder="Preço do produto"
              value={values.unit_price}
              onChange={(event) => setValue('unit_price', event.target.value)}
            />
          )}
        </FieldShell>
      </div>

      <div className="entity-form__actions">
        <button type="submit" disabled={saving}>
          {saving ? (
            <>
              <span className="pedidos-table__spinner" aria-hidden="true" />
              Adicionando...
            </>
          ) : (
            <>
              <IconPlus size={16} aria-hidden="true" />
              Adicionar item
            </>
          )}
        </button>
      </div>
    </form>
  )
}

interface ItensPedidoProps {
  pedido: Pedido
  produtos: Produto[]
  produtosStatus: StatusProdutos
  onSalvarItem: (
    item: PedidoItem,
    values: { quantity: string; unit_price: string },
  ) => Promise<void>
  onRemoverItem: (item: PedidoItem) => Promise<void>
  onAdicionarItem: (values: ValoresFormItemPedido) => Promise<void>
}

export default function ItensPedido({
  pedido,
  produtos,
  produtosStatus,
  onSalvarItem,
  onRemoverItem,
  onAdicionarItem,
}: ItensPedidoProps) {
  const editando = pedido.status === 'RASCUNHO'
  const podeRemover = pedido.itens.length > 1

  return (
    <div className="panel">
      <h2>Itens do pedido</h2>

      {pedido.itens.length === 0 ? (
        <p className="empty-state">Nenhum item no pedido</p>
      ) : (
        <div className="table-wrap">
          <table className="pedidos-table">
            <thead>
              <tr>
                {editando && <th scope="col">Ações</th>}
                <th scope="col">Produto</th>
                <th scope="col">Quantidade</th>
                <th scope="col">Preço unitário</th>
                <th scope="col">Total do item</th>
              </tr>
            </thead>
            <tbody>
              {pedido.itens.map((item) => (
                <ItemRow
                  key={item.id}
                  item={item}
                  produtos={produtos}
                  editando={editando}
                  podeRemover={podeRemover}
                  onSalvar={(values) => onSalvarItem(item, values)}
                  onRemover={() => onRemoverItem(item)}
                />
              ))}
            </tbody>
          </table>
        </div>
      )}

      {editando && (
        <AdicionarItem
          produtos={produtos}
          produtosStatus={produtosStatus}
          onAdicionar={onAdicionarItem}
        />
      )}
    </div>
  )
}
