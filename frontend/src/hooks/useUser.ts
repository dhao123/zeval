import { useEffect, useState } from 'react'
import type { User, UserContextType } from '@/types/user'

const API_SECURITY_BASE = '/api-security'

/**
 * Fetch user info from security service
 */
const fetchUserInfo = async (): Promise<User> => {
  const response = await fetch(`${API_SECURITY_BASE}/accounts/username`, {
    credentials: 'include', // Important: include cookies
    headers: {
      Accept: 'application/json',
    },
  })

  if (!response.ok) {
    if (response.status === 401) {
      throw new Error('Unauthorized')
    }
    throw new Error(`Failed to fetch user info: ${response.status}`)
  }

  return response.json()
}

/**
 * Hook to get current user information from SSO.
 * 
 * This hook fetches the current user info from the security service.
 * If the user is not logged in, it will return null user.
 * 
 * @returns User context with user info, loading state, and error
 */
export function useUser(): UserContextType {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  useEffect(() => {
    let cancelled = false

    const loadUser = async () => {
      try {
        setIsLoading(true)
        setError(null)
        const userInfo = await fetchUserInfo()
        if (!cancelled) {
          setUser(userInfo)
        }
      } catch (err) {
        if (!cancelled) {
          // Don't treat 401 as an error, just means not logged in
          if (err instanceof Error && err.message === 'Unauthorized') {
            setUser(null)
          } else {
            setError(err instanceof Error ? err : new Error(String(err)))
            setUser(null)
          }
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false)
        }
      }
    }

    loadUser()

    return () => {
      cancelled = true
    }
  }, [])

  return {
    user,
    isLoading,
    isLogin: !!user?.username,
    error,
  }
}

export default useUser
