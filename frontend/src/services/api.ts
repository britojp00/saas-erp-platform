const baseUrl: string = import.meta.env.VITE_API_URL

if (!baseUrl) {
  throw new Error(
    'VITE_API_URL não configurada. Copie frontend/.env.example para frontend/.env.',
  )
}

const API_BASE_URL = baseUrl.replace(/\/+$/, '')
const DEFAULT_TIMEOUT_MS = 10_000

let authToken: string | null = null
let unauthorizedHandler: (() => void) | null = null

export function setAuthToken(token: string | null): void {
  authToken = token
}

export function setUnauthorizedHandler(handler: (() => void) | null): void {
  unauthorizedHandler = handler
}

export class ApiError extends Error {
  readonly status: number
  readonly detail: string | null

  constructor(status: number, message: string, detail: string | null = null) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.detail = detail
  }
}

export interface RequestOptions {
  body?: unknown
  headers?: Record<string, string>
  signal?: AbortSignal
}

type HttpMethod = 'GET' | 'POST' | 'PATCH' | 'DELETE'

function defaultMessage(status: number): string {
  if (status === 401) return 'Não autenticado.'
  if (status === 403) return 'Acesso negado.'
  if (status === 404) return 'Recurso não encontrado.'
  if (status === 409) return 'Conflito com o estado atual.'
  if (status === 422) return 'Dados inválidos.'
  return 'Erro interno do servidor.'
}

function extractDetail(payload: unknown): string | null {
  if (typeof payload !== 'object' || payload === null) return null
  const { detail } = payload as { detail?: unknown }
  if (typeof detail === 'string') return detail
  if (!Array.isArray(detail)) return null
  const messages = detail.flatMap((item) => {
    if (typeof item === 'object' && item !== null && 'msg' in item) {
      const msg = (item as { msg?: unknown }).msg
      return typeof msg === 'string' ? [msg] : []
    }
    return []
  })
  return messages.length > 0 ? messages.join(' ') : null
}

async function readError(response: Response): Promise<ApiError> {
  let detail: string | null = null
  try {
    const payload: unknown = await response.json()
    detail = extractDetail(payload)
  } catch {
    detail = null
  }
  return new ApiError(
    response.status,
    detail ?? defaultMessage(response.status),
    detail,
  )
}

async function request<T>(
  method: HttpMethod,
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const headers: Record<string, string> = {
    Accept: 'application/json',
    ...(authToken !== null ? { Authorization: `Bearer ${authToken}` } : {}),
    ...(options.body !== undefined
      ? { 'Content-Type': 'application/json' }
      : {}),
    ...options.headers,
  }

  const init: RequestInit = {
    method,
    headers,
    signal: options.signal ?? AbortSignal.timeout(DEFAULT_TIMEOUT_MS),
  }
  if (options.body !== undefined) {
    init.body = JSON.stringify(options.body)
  }

  let response: Response
  try {
    response = await fetch(`${API_BASE_URL}${path}`, init)
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw error
    }
    if (error instanceof DOMException && error.name === 'TimeoutError') {
      throw new ApiError(0, 'Tempo limite da requisição excedido.')
    }
    throw new ApiError(0, 'Falha de rede ao acessar a API.')
  }

  if (!response.ok) {
    const apiError = await readError(response)
    if (apiError.status === 401 && authToken !== null) {
      unauthorizedHandler?.()
    }
    throw apiError
  }

  if (response.status === 204) {
    return undefined as T
  }

  const text = await response.text()
  if (text === '') {
    return undefined as T
  }
  return JSON.parse(text) as T
}

export const api = {
  get<T>(path: string, options: RequestOptions = {}): Promise<T> {
    return request<T>('GET', path, options)
  },
  post<T>(path: string, body?: unknown, options: RequestOptions = {}): Promise<T> {
    return request<T>('POST', path, { ...options, body })
  },
  patch<T>(path: string, body?: unknown, options: RequestOptions = {}): Promise<T> {
    return request<T>('PATCH', path, { ...options, body })
  },
  delete<T>(path: string, options: RequestOptions = {}): Promise<T> {
    return request<T>('DELETE', path, options)
  },
}
