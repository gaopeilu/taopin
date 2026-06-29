/**
 * Axios 请求封装
 * 统一处理：请求拦截（token注入）、响应拦截（错误处理、401跳转）
 */
import axios from 'axios'
import { getToken, getRefreshToken, logout } from '../utils/auth'
import { ElMessage, ElNotification } from 'element-plus'

const request = axios.create({
  baseURL: '',
  timeout: 15000
})

/* [Bug16] 防止多个401请求并发刷新token */
let isRefreshing = false
let pendingRequests = []

/* 请求拦截：自动携带token */
request.interceptors.request.use(config => {
  const token = getToken()
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

/* 响应拦截：统一处理 */
request.interceptors.response.use(
  response => {
    const res = response.data
    // {code, message, data} 格式 → 返回整个对象
    if (res && typeof res === 'object' && res.code !== undefined) {
      if (res.code === 200) return res
      // 业务错误提示
      ElMessage.error({
        message: res.message || '请求失败',
        duration: 3000,
        showClose: true
      })
      return Promise.reject(new Error(res.message))
    }
    // DRF分页 {count, results} 或 纯list → 直接返回
    return res
  },
  async error => {
    const { response, code, message } = error

    // 网络错误
    if (!response) {
      if (code === 'ECONNABORTED') {
        ElNotification({
          title: '请求超时',
          message: '服务器响应超时，请稍后重试',
          type: 'warning',
          duration: 5000
        })
      } else if (message.includes('Network Error')) {
        ElNotification({
          title: '网络错误',
          message: '请检查网络连接后重试',
          type: 'error',
          duration: 5000
        })
      } else {
        ElMessage.error('网络异常，请稍后重试')
      }
      return Promise.reject(error)
    }

    // 401 未授权 - [Bug16] 防并发刷新token
    if (response.status === 401) {
      const refreshToken = getRefreshToken()
      if (refreshToken && !error.config._retry) {
        if (isRefreshing) {
          // 已有请求在刷新token，将当前请求加入队列等待
          return new Promise((resolve, reject) => {
            pendingRequests.push({ resolve, reject, config: error.config })
          })
        }
        isRefreshing = true
        error.config._retry = true
        try {
          const { data } = await axios.post('/api/v1/users/token/refresh/', { refresh: refreshToken })
          localStorage.setItem('access_token', data.access)
          if (data.refresh) localStorage.setItem('refresh_token', data.refresh)
          error.config.headers.Authorization = `Bearer ${data.access}`
          // 重发队列中的所有请求
          pendingRequests.forEach(p => {
            p.config.headers.Authorization = `Bearer ${data.access}`
            request(p.config).then(p.resolve).catch(p.reject)
          })
          pendingRequests = []
          return request(error.config)
        } catch {
          ElMessage.warning('登录已过期，请重新登录')
          pendingRequests.forEach(p => p.reject(error))
          pendingRequests = []
          logout()
          return Promise.reject(error)
        } finally {
          isRefreshing = false
        }
      } else {
        ElMessage.warning('请先登录')
        logout()
        return Promise.reject(error)
      }
    }

    // 403 无权限
    if (response.status === 403) {
      ElMessage.error('暂无权限执行此操作')
      return Promise.reject(error)
    }

    // 404 未找到
    if (response.status === 404) {
      ElMessage.error('请求的资源不存在')
      return Promise.reject(error)
    }

    // 500 服务器错误
    if (response.status === 500) {
      ElNotification({
        title: '服务器错误',
        message: '服务器内部错误，请稍后重试',
        type: 'error',
        duration: 5000
      })
      return Promise.reject(error)
    }

    // 其他错误
    const msg = response.data?.message || response.data?.detail || '请求失败'
    ElMessage.error({
      message: msg,
      duration: 3000,
      showClose: true
    })
    return Promise.reject(error)
  }
)

export default request
