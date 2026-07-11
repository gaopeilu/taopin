<template>
  <div class="login-page">
    <div class="login-box">
      <div class="login-header">
        <div class="login-logo" @click="$router.push('/')">🛍️ 淘拼商城</div>
        <div class="login-tabs">
          <span :class="{active: mode==='login'}" @click="mode='login'">登录</span>
          <span :class="{active: mode==='register'}" @click="mode='register'">注册</span>
        </div>
      </div>

      <!-- 登录表单 -->
      <div class="login-form" v-if="mode==='login'">
        <div class="input-group">
          <span class="input-icon">👤</span>
          <input v-model="loginForm.username" placeholder="用户名 / 手机号 / 邮箱" @keyup.enter="handleLogin" />
        </div>
        <div class="input-group">
          <span class="input-icon">🔒</span>
          <input v-model="loginForm.password" type="password" placeholder="密码" @keyup.enter="handleLogin" />
        </div>
        <button class="submit-btn" :disabled="loginLoading" @click="handleLogin">
          {{ loginLoading ? '登录中...' : '登 录' }}
        </button>
        <div class="form-footer">
          <span>还没有账号？</span>
          <a @click="mode='register'">立即注册</a>
        </div>
      </div>

      <!-- 注册表单 -->
      <div class="login-form" v-else>
        <div class="input-group">
          <span class="input-icon">👤</span>
          <input v-model="regForm.username" placeholder="用户名（至少3个字符）" />
        </div>
        <div class="input-group">
          <span class="input-icon">📱</span>
          <input v-model="regForm.phone" placeholder="手机号（11位）" maxlength="11" />
        </div>
        <div class="input-group">
          <span class="input-icon">🔒</span>
          <input v-model="regForm.password" type="password" placeholder="密码（8-20位）" />
        </div>
        <div class="input-group">
          <span class="input-icon">🔒</span>
          <input v-model="regForm.password_confirm" type="password" placeholder="确认密码" />
        </div>
        <div class="role-select">
          <label><input type="radio" v-model="regForm.role" value="user" /> 普通用户</label>
          <label><input type="radio" v-model="regForm.role" value="seller" /> 商家入驻</label>
        </div>
        <div class="input-group" v-if="regForm.role==='seller'">
          <span class="input-icon">🏪</span>
          <input v-model="regForm.shop_name" placeholder="店铺名称（商家必填）" />
        </div>
        <button class="submit-btn" :disabled="regLoading" @click="handleRegister">
          {{ regLoading ? '注册中...' : '注 册' }}
        </button>
        <div class="form-footer">
          <span>已有账号？</span>
          <a @click="mode='login'">去登录</a>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../../store/user'
import { ElMessage } from 'element-plus'

const router = useRouter()
const userStore = useUserStore()
const mode = ref('login')
const loginLoading = ref(false)
const regLoading = ref(false)

const loginForm = reactive({ username: '', password: '' })
const regForm = reactive({ username: '', phone: '', email: '', password: '', password_confirm: '', role: 'user', shop_name: '' })

async function handleLogin() {
  if (!loginForm.username || !loginForm.password) { ElMessage.warning('请填写完整'); return }
  loginLoading.value = true
  try {
    await userStore.login(loginForm)
    router.push('/')
  } catch {} finally { loginLoading.value = false }
}

async function handleRegister() {
  if (!regForm.username || regForm.username.length < 3) { ElMessage.warning('用户名至少3个字符'); return }
  if (!regForm.password || regForm.password.length < 8) { ElMessage.warning('密码至少8位'); return }
  if (regForm.password !== regForm.password_confirm) { ElMessage.warning('两次密码不一致'); return }
  if (regForm.role === 'seller' && !regForm.shop_name) { ElMessage.warning('商家必须填写店铺名称'); return }
  regLoading.value = true
  try {
    await userStore.register(regForm)
    router.push('/')
  } catch {} finally { regLoading.value = false }
}
</script>

<style scoped>
.login-page { min-height: 100vh; display: flex; align-items: center; justify-content: center; background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%); }
.login-box { width: 400px; background: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08); }
.login-header { padding: 36px 32px 0; text-align: center; }
.login-logo { font-size: 24px; font-weight: 600; color: #1e293b; cursor: pointer; margin-bottom: 24px; display: flex; align-items: center; justify-content: center; gap: 8px; }
.login-tabs { display: flex; border-bottom: 1px solid #e2e8f0; }
.login-tabs span { flex: 1; padding: 12px; text-align: center; cursor: pointer; color: #64748b; border-bottom: 2px solid transparent; font-size: 14px; font-weight: 500; transition: all 0.2s; }
.login-tabs span.active { color: #3b82f6; border-bottom-color: #3b82f6; }

.login-form { padding: 24px 32px 32px; }
.input-group { display: flex; align-items: center; border: 1px solid #e2e8f0; border-radius: 10px; margin-bottom: 16px; padding: 0 14px; height: 48px; transition: border-color 0.2s; }
.input-group:focus-within { border-color: #3b82f6; box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1); }
.input-icon { margin-right: 12px; font-size: 16px; color: #94a3b8; }
.input-group input { flex: 1; border: none; outline: none; font-size: 14px; color: #1e293b; background: transparent; }
.input-group input::placeholder { color: #94a3b8; }

.role-select { display: flex; gap: 24px; margin-bottom: 16px; font-size: 13px; color: #64748b; }
.role-select label { display: flex; align-items: center; gap: 6px; cursor: pointer; }
.role-select input { accent-color: #3b82f6; width: 14px; height: 14px; }

.submit-btn { width: 100%; height: 48px; background: #3b82f6; color: #ffffff; border: none; border-radius: 10px; font-size: 15px; font-weight: 500; cursor: pointer; margin-top: 8px; transition: background 0.2s; }
.submit-btn:hover { background: #2563eb; }
.submit-btn:disabled { opacity: .5; cursor: not-allowed; }
.form-footer { text-align: center; margin-top: 20px; font-size: 13px; color: #64748b; }
.form-footer a { color: #3b82f6; cursor: pointer; margin-left: 4px; font-weight: 500; }
</style>