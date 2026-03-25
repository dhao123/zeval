/**
 * User types for SSO authentication.
 */

export interface User {
  /** User ID */
  id: number
  /** Username (login name) */
  username: string
  /** Display name */
  nickname: string
  /** User email */
  email: string
  /** User phone number */
  phoneNum?: string
  /** Role IDs assigned to user */
  roleIds: number[]
  /** Whether user is admin */
  is_admin?: boolean
}

export interface UserContextType {
  user: User | null
  isLoading: boolean
  isLogin: boolean
  error: Error | null
}
