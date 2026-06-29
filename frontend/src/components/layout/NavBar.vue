<template>
  <!-- 顶部导航 -->
  <header class="top-bar">
    <div class="top-inner">
      <div class="top-left">
        <span v-if="userStore.loggedIn" class="top-user">Hi，{{ userStore.nickname }}</span>
        <span v-else class="top-user">Hi，请 <router-link to="/login">登录</router-link> <router-link to="/register">注册</router-link></span>
        <span class="top-link" @click="$router.push('/user/orders')">我的订单</span>
        <span class="top-link" @click="$router.push('/user')">个人中心</span>
      </div>
      <div class="top-right">
        <span class="top-link" @click="$router.push('/cart')">🛒 购物车({{ cartStore.totalCount }})</span>
        <span v-if="userStore.isSellerUser" class="top-link seller-link" @click="$router.push('/seller')">🏪 商家后台</span>
        <span v-if="userStore.loggedIn" class="top-link" @click="userStore.logout()">退出</span>
      </div>
    </div>
  </header>

  <div class="header">
    <div class="header-inner">
      <div class="logo" @click="$router.push('/')">
        <span class="logo-icon">🛍️</span>
        <span class="logo-text">淘拼商城</span>
      </div>
      <div class="search-wrap">
        <div class="search-box">
          <el-input v-model="searchText" placeholder="搜索商品、品牌" @keyup.enter="doSearch" clearable>
            <template #append><el-button @click="doSearch">搜索</el-button></template>
          </el-input>
        </div>
        <div class="search-hot">
          <span class="hot-label">热搜：</span>
          <span class="hot-word" v-for="w in hotWords" :key="w" @click="searchText=w;doSearch()">{{ w }}</span>
        </div>
      </div>
      <div class="header-cart" @click="$router.push('/cart')">
        <span class="cart-icon">🛒</span>
        <span class="cart-text">购物车</span>
        <span class="cart-badge" v-if="cartStore.totalCount > 0">{{ cartStore.totalCount }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../../store/user'
import { useCartStore } from '../../store/cart'
import { addSearchHistory } from '../../utils/history'

const router = useRouter()
const userStore = useUserStore()
const cartStore = useCartStore()
const searchText = ref('')
const hotWords = ['手机数码', '运动鞋', '零食', '护肤品', '电脑办公']

function doSearch() {
  if (searchText.value.trim()) {
    addSearchHistory(searchText.value.trim())
    router.push({ path: '/goods', query: { q: searchText.value.trim() } })
  }
}
</script>

<style scoped>
/* 顶部信息条 */
.top-bar { background: #f2f2f2; border-bottom: 1px solid #e8e8e8; font-size: 12px; color: #999; }
.top-inner { max-width: 1200px; margin: 0 auto; display: flex; justify-content: space-between; align-items: center; height: 32px; padding: 0 16px; }
.top-left, .top-right { display: flex; align-items: center; gap: 16px; }
.top-link { cursor: pointer; }
.top-link:hover { color: #ff4400; }
.top-user a { color: #ff4400; text-decoration: none; margin: 0 2px; }
.seller-link { color: #ff4400; font-weight: bold; }

/* 主头部 */
.header { background: #fff; padding: 12px 0; }
.header-inner { max-width: 1200px; margin: 0 auto; display: flex; align-items: center; gap: 32px; padding: 0 16px; }
.logo { display: flex; align-items: center; gap: 8px; cursor: pointer; flex-shrink: 0; }
.logo-icon { font-size: 32px; }
.logo-text { font-size: 24px; font-weight: bold; color: #ff4400; }

/* 搜索框 */
.search-wrap { flex: 1; max-width: 560px; }
.search-box :deep(.el-input__wrapper) { border-radius: 24px; border: 2px solid #ff4400; box-shadow: none !important; height: 40px; }
.search-box :deep(.el-input-group__append) { background: #ff4400; border: 2px solid #ff4400; border-radius: 0 24px 24px 0; }
.search-box :deep(.el-input-group__append .el-button) { color: #fff; margin: 0; }
.search-box :deep(.el-input-group__append:hover) { background: #e63e00; border-color: #e63e00; }
.search-hot { margin-top: 6px; display: flex; align-items: center; gap: 8px; font-size: 12px; }
.hot-label { color: #999; }
.hot-word { color: #666; cursor: pointer; padding: 2px 6px; border-radius: 3px; }
.hot-word:hover { color: #ff4400; background: #fff0e6; }

/* 购物车按钮 */
.header-cart { display: flex; align-items: center; gap: 6px; padding: 8px 20px; border: 1px solid #eee; border-radius: 24px; cursor: pointer; position: relative; flex-shrink: 0; }
.header-cart:hover { border-color: #ff4400; }
.cart-icon { font-size: 20px; }
.cart-text { font-size: 13px; color: #666; }
.cart-badge { position: absolute; top: -4px; right: -4px; background: #ff4400; color: #fff; font-size: 11px; min-width: 18px; height: 18px; line-height: 18px; text-align: center; border-radius: 9px; padding: 0 4px; }
</style>
