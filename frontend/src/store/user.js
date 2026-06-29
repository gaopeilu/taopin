/**
 * 用户状态管理 (Pinia)
 * 管理登录状态、用户信息、角色权限
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { getUserInfo, isLoggedIn, isSeller, setLoginData, logout as authLogout, updateLocalUserInfo } from '../utils/auth'
import { login as apiLogin, register as apiRegister, getUserInfo as apiGetUserInfo } from '../api/user'

export const useUserStore = defineStore('user', () => {
  /* ========== 状态 ========== */
  const userInfo = ref(getUserInfo())
  const loggedIn = ref(isLoggedIn())

  /* ========== 计算属性 ========== */
  const isSellerUser = computed(() => userInfo.value?.role === 'seller')
  const userId = computed(() => userInfo.value?.id)
  const username = computed(() => userInfo.value?.username || '')
  const avatar = computed(() => userInfo.value?.avatar || '')
  const nickname = computed(() => userInfo.value?.nickname || username.value)
  const role = computed(() => userInfo.value?.role || 'user')

  /* ========== 方法 ========== */

  /** 登录 */
  async function login(form) {
    const res = await apiLogin(form)
    setLoginData(res.data)
    userInfo.value = res.data.user
    loggedIn.value = true
    return res
  }

  /** 注册 */
  async function register(form) {
    const res = await apiRegister(form)
    setLoginData(res.data)
    userInfo.value = res.data.user
    loggedIn.value = true
    return res
  }

  /** 刷新用户信息（从后端重新获取） */
  async function fetchUserInfo() {
    const res = await apiGetUserInfo()
    userInfo.value = res.data
    updateLocalUserInfo(res.data)
    return res.data
  }

  /** 退出登录 */
  function logout() {
    userInfo.value = null
    loggedIn.value = false
    authLogout()
    // 跳转到登录页（不用reload，避免白屏闪烁）
    window.location.href = '/login'
  }

  return {
    userInfo, loggedIn,
    isSellerUser, userId, username, avatar, nickname, role,
    login, register, fetchUserInfo, logout
  }
})
