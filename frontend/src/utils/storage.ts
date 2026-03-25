/**
 * Cookie storage utilities for SSO authentication.
 * 
 * The access_token is set by the SSO service as an HTTP-only cookie,
 * but we need js-cookie to read it for API requests.
 */
import Cookies from 'js-cookie'

export type StorageKey = 'access_token' | 'refresh_token'

/**
 * Get item from cookies
 * @param key - The cookie key
 * @returns The cookie value or undefined
 */
export function getItem(key: StorageKey): string | undefined {
  return Cookies.get(key)
}

/**
 * Set item in cookies
 * @param key - The cookie key
 * @param value - The cookie value
 * @param options - Optional cookie options
 */
export function setItem(
  key: StorageKey,
  value: string,
  options?: Cookies.CookieAttributes
): void {
  Cookies.set(key, value, {
    path: '/',
    sameSite: 'lax',
    ...options,
  })
}

/**
 * Remove item from cookies
 * @param key - The cookie key
 */
export function removeItem(key: StorageKey): void {
  Cookies.remove(key, { path: '/' })
}

/**
 * Clear all auth-related cookies
 */
export function clearAuthCookies(): void {
  removeItem('access_token')
  removeItem('refresh_token')
}
