import axios from 'axios'
import { message } from 'antd'

// Create axios instance
const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor
request.interceptors.request.use(
  (config) => {
    // Add token to headers
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor
request.interceptors.response.use(
  (response) => {
    const { data } = response
    
    // Handle business errors
    if (data.code !== 0) {
      message.error(data.message || 'Request failed')
      return Promise.reject(new Error(data.message))
    }
    
    return data
  },
  (error) => {
    if (error.response) {
      const { status } = error.response
      
      if (status === 401) {
        message.error('登录已过期，请重新登录')
        localStorage.removeItem('token')
        window.location.href = '/login'
      } else if (status === 403) {
        message.error('没有权限执行此操作')
      } else if (status === 500) {
        message.error('服务器错误')
      } else {
        message.error(error.response.data?.message || '请求失败')
      }
    } else {
      message.error('网络错误')
    }
    
    return Promise.reject(error)
  }
)

export default request
