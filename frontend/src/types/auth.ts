export interface LoginRequest {
  email: string
  password: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
}

export interface UserResponse {
  id: number
  email: string
  full_name: string
  is_active: boolean
  tenant_id: number
  created_at: string
  roles: string[]
  permissions: string[]
}
