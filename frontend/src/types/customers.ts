import type { PaginatedResponse } from './dashboard'

export interface Customer {
  id: number
  name: string
  document: string | null
  email: string | null
  phone: string | null
  notes: string | null
  created_at: string
  updated_at: string
}

export type CustomerListResponse = PaginatedResponse<Customer>

export type CustomerSortField = 'id' | 'name' | 'created_at'

export type SortOrder = 'asc' | 'desc'
