import { useCallback, useEffect, useRef, useState } from 'react'
import { ApiError, api } from '../services/api'
import { ORDER_STATUSES } from '../types/dashboard'
import type {
  AuditLogItem,
  DashboardSummary,
  InventoryItem,
  InventorySummary,
  OrderListItem,
  PaginatedResponse,
} from '../types/dashboard'

const INVENTORY_PAGE_SIZE = 100
const MAX_INVENTORY_PAGES = 10
const RECENT_LIMIT = 5

export type AsyncState<T> =
  | { status: 'loading' }
  | { status: 'error'; message: string }
  | { status: 'ready'; data: T }

export type DashboardSection = 'summary' | 'orders' | 'activity'

function errorMessage(error: unknown): string {
  if (error instanceof ApiError) return error.message
  return 'Não foi possível carregar os dados da API.'
}

async function fetchInventorySummary(): Promise<InventorySummary> {
  const first = await api.get<PaginatedResponse<InventoryItem>>(
    `/api/v1/inventory?page=1&page_size=${INVENTORY_PAGE_SIZE}`,
  )

  let items = first.items

  if (items.length < first.total) {
    const remainingPages =
      Math.min(
        Math.ceil(first.total / INVENTORY_PAGE_SIZE),
        MAX_INVENTORY_PAGES,
      ) - 1

    const pages = await Promise.all(
      Array.from({ length: remainingPages }, (_, index) =>
        api.get<PaginatedResponse<InventoryItem>>(
          `/api/v1/inventory?page=${index + 2}&page_size=${INVENTORY_PAGE_SIZE}`,
        ),
      ),
    )

    items = items.concat(...pages.map((page) => page.items))
  }

  const complete = items.length >= first.total

  if (!complete) {
    return {
      total: first.total,
      complete: false,
      quantity: null,
      reserved: null,
      available: null,
    }
  }

  let quantity = 0
  let reserved = 0
  for (const item of items) {
    quantity += Number(item.quantity)
    reserved += Number(item.reserved_quantity)
  }

  return {
    total: first.total,
    complete: true,
    quantity,
    reserved,
    available: quantity - reserved,
  }
}

async function fetchSummary(): Promise<DashboardSummary> {
  const [
    customersRes,
    productsRes,
    activeProductsRes,
    ordersRes,
    draftRes,
    confirmedRes,
    completedRes,
    cancelledRes,
    inventoryRes,
    movementsRes,
    reservationsRes,
  ] = await Promise.all([
    api.get<PaginatedResponse<unknown>>(
      '/api/v1/customers?page=1&page_size=1',
    ),
    api.get<PaginatedResponse<unknown>>('/api/v1/products?page=1&page_size=1'),
    api.get<PaginatedResponse<unknown>>(
      '/api/v1/products?page=1&page_size=1&is_active=true',
    ),
    api.get<PaginatedResponse<unknown>>('/api/v1/orders?page=1&page_size=1'),
    api.get<PaginatedResponse<unknown>>(
      '/api/v1/orders?page=1&page_size=1&status=DRAFT',
    ),
    api.get<PaginatedResponse<unknown>>(
      '/api/v1/orders?page=1&page_size=1&status=CONFIRMED',
    ),
    api.get<PaginatedResponse<unknown>>(
      '/api/v1/orders?page=1&page_size=1&status=COMPLETED',
    ),
    api.get<PaginatedResponse<unknown>>(
      '/api/v1/orders?page=1&page_size=1&status=CANCELLED',
    ),
    fetchInventorySummary(),
    api.get<PaginatedResponse<unknown>>(
      '/api/v1/inventory/movements/list?page=1&page_size=1',
    ),
    api.get<PaginatedResponse<unknown>>(
      '/api/v1/inventory/reservations/list?page=1&page_size=1',
    ),
  ])

  const ordersByStatus = {
    DRAFT: draftRes.total,
    CONFIRMED: confirmedRes.total,
    COMPLETED: completedRes.total,
    CANCELLED: cancelledRes.total,
  }

  const classified = ORDER_STATUSES.reduce(
    (sum, status) => sum + ordersByStatus[status],
    0,
  )

  return {
    customersTotal: customersRes.total,
    productsTotal: productsRes.total,
    activeProductsTotal: activeProductsRes.total,
    ordersTotal: ordersRes.total,
    ordersByStatus,
    ordersUnclassified: Math.max(ordersRes.total - classified, 0),
    inventory: inventoryRes,
    movementsTotal: movementsRes.total,
    reservationsTotal: reservationsRes.total,
  }
}

async function fetchRecentOrders(): Promise<OrderListItem[]> {
  const response = await api.get<PaginatedResponse<OrderListItem>>(
    `/api/v1/orders?page=1&page_size=${RECENT_LIMIT}&sort=created_at&order=desc`,
  )
  return response.items
}

async function fetchRecentActivity(): Promise<AuditLogItem[]> {
  const response = await api.get<PaginatedResponse<AuditLogItem>>(
    `/api/v1/audit-logs?page=1&page_size=${RECENT_LIMIT}&sort=created_at&order=desc`,
  )
  return response.items
}

export function useDashboardData() {
  const [summary, setSummary] = useState<AsyncState<DashboardSummary>>({
    status: 'loading',
  })
  const [recentOrders, setRecentOrders] = useState<AsyncState<OrderListItem[]>>(
    { status: 'loading' },
  )
  const [recentActivity, setRecentActivity] = useState<
    AsyncState<AuditLogItem[]>
  >({ status: 'loading' })

  const sequence = useRef({ summary: 0, orders: 0, activity: 0 })

  const loadSummary = useCallback(async () => {
    const current = ++sequence.current.summary
    setSummary({ status: 'loading' })
    try {
      const data = await fetchSummary()
      if (current === sequence.current.summary) setSummary({ status: 'ready', data })
    } catch (error) {
      if (current === sequence.current.summary) {
        setSummary({ status: 'error', message: errorMessage(error) })
      }
    }
  }, [])

  const loadOrders = useCallback(async () => {
    const current = ++sequence.current.orders
    setRecentOrders({ status: 'loading' })
    try {
      const data = await fetchRecentOrders()
      if (current === sequence.current.orders) {
        setRecentOrders({ status: 'ready', data })
      }
    } catch (error) {
      if (current === sequence.current.orders) {
        setRecentOrders({ status: 'error', message: errorMessage(error) })
      }
    }
  }, [])

  const loadActivity = useCallback(async () => {
    const current = ++sequence.current.activity
    setRecentActivity({ status: 'loading' })
    try {
      const data = await fetchRecentActivity()
      if (current === sequence.current.activity) {
        setRecentActivity({ status: 'ready', data })
      }
    } catch (error) {
      if (current === sequence.current.activity) {
        setRecentActivity({ status: 'error', message: errorMessage(error) })
      }
    }
  }, [])

  useEffect(() => {
    void loadSummary()
    void loadOrders()
    void loadActivity()
  }, [loadSummary, loadOrders, loadActivity])

  const retry = useCallback(
    (section: DashboardSection) => {
      if (section === 'summary') void loadSummary()
      else if (section === 'orders') void loadOrders()
      else void loadActivity()
    },
    [loadSummary, loadOrders, loadActivity],
  )

  return { summary, recentOrders, recentActivity, retry }
}
