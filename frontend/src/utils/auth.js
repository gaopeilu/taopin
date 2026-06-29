/**
 * 认证工具函数
 * 管理localStorage中的token和用户信息
 */

const TOKEN_KEY = 'access_token'
const REFRESH_KEY = 'refresh_token'
const ROLE_KEY = 'user_role'
const USER_KEY = 'user_info'

/** 获取access_token */
export function getToken() {
  return localStorage.getItem(TOKEN_KEY)
}

/** 获取refresh_token */
export function getRefreshToken() {
  return localStorage.getItem(REFRESH_KEY)
}

/** 获取用户角色: 'user' | 'seller' | null */
export function getUserRole() {
  return localStorage.getItem(ROLE_KEY)
}

/** 获取用户信息对象 */
export function getUserInfo() {
  const raw = localStorage.getItem(USER_KEY)
  return raw ? JSON.parse(raw) : null
}

/** 是否已登录 */
export function isLoggedIn() {
  return !!getToken()
}

/** 是否为商家 */
export function isSeller() {
  return getUserRole() === 'seller'
}

/** 存储登录信息 */
export function setLoginData(data) {
  localStorage.setItem(TOKEN_KEY, data.tokens.access)
  localStorage.setItem(REFRESH_KEY, data.tokens.refresh)
  localStorage.setItem(ROLE_KEY, data.user.role)
  localStorage.setItem(USER_KEY, JSON.stringify(data.user))
}

/** 清除所有登录信息 */
export function logout() {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(REFRESH_KEY)
  localStorage.removeItem(ROLE_KEY)
  localStorage.removeItem(USER_KEY)
}

/** 更新本地用户信息（修改个人信息后调用） */
export function updateLocalUserInfo(user) {
  localStorage.setItem(USER_KEY, JSON.stringify(user))
  localStorage.setItem(ROLE_KEY, user.role)
}
