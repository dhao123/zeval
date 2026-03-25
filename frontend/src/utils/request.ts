import axios from 'axios'
import { message } from 'antd'
import { getItem } from './storage'

// AITest compatible auth URL
const AUTH_LOGIN_URL = '/api-auth/login'

// Create axios instance
const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
  // Important: include cookies for cross-origin requests
  withCredentials: true,
})

// Request interceptor
request.interceptors.request.use(
  (config) => {
    // Add token to headers from cookie (for SSO)
    const token = getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    
    // Also support localStorage token for backward compatibility
    const localToken = localStorage.getItem('token')
    if (localToken && !config.headers.Authorization) {
      config.headers.Authorization = `Bearer ${localToken}`
    }
    
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Flag to prevent multiple redirect loops
let isRedirecting = false

// Response interceptor
request.interceptors.response.use(
  (response) => {
    const { data } = response
    
    // Handle business errors (custom API format with code/message/data)
    if (data && typeof data === 'object' && 'code' in data) {
      if (data.code !== 0 && data.code !== 200) {
        message.error(data.message || '请求失败')
        return Promise.reject(new Error(data.message || 'Request failed'))
      }
      // Return the full response data (including code, message, data)
      // Frontend expects to access data.code and data.data
      return data
    }
    
    return data
  },
  (error) => {
    if (error.response) {
      const { status, data } = error.response
      
      if (status === 401) {
        // AITest: Redirect to company SSO login service
        if (!isRedirecting) {
          isRedirecting = true
          message.error('登录已过期，请重新登录')
          
          // Clear local tokens
          localStorage.removeItem('token')
          localStorage.removeItem('refresh_token')
          
          // AITest compatible: Redirect to /api-auth/login (proxied to company SSO)
          const returnUrl = encodeURIComponent(window.location.href)
          window.location.href = `${AUTH_LOGIN_URL}?returnUrl=${returnUrl}`
          
          // Reset flag after a delay (in case redirect fails)
          setTimeout(() => {
            isRedirecting = false
          }, 5000)
        }
      } else if (status === 403) {
        message.error(data?.message || '没有权限执行此操作')
      } else if (status === 500) {
        message.error(data?.message || '服务器错误')
      } else {
        message.error(data?.message || `请求失败 (${status})`)
      }
    } else if (error.request) {
      // Request was made but no response received
      message.error('网络错误，请检查网络连接')
    } else {
      // Something else happened
      message.error(error.message || '请求失败')
    }
    
    return Promise.reject(error)
  }
)

/**
 * Redirect to auth login page (AITest compatible)
 * @param returnUrl - URL to return after login (defaults to current page)
 */
export function redirectToSSOLogin(returnUrl?: string): void {
  const url = returnUrl || window.location.href
  const encodedReturnUrl = encodeURIComponent(url)
  window.location.href = `${AUTH_LOGIN_URL}?returnUrl=${encodedReturnUrl}`
}

/**
 * Redirect to logout page
 */
export function redirectToSSOLogout(): void {
  // Clear local tokens first
  localStorage.removeItem('token')
  localStorage.removeItem('refresh_token')
  
  // Redirect to auth login page
  window.location.href = AUTH_LOGIN_URL
}

export default request
