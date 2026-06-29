<template>
  <!-- 商家后台布局：左侧菜单 + 右侧内容 -->
  <el-container class="seller-layout">
    <!-- 左侧菜单 -->
    <el-aside width="220px" class="seller-aside">
      <div class="seller-logo" @click="$router.push('/seller/dashboard')">🏪 商家管理后台</div>
      <el-menu :default-active="$route.path" router background-color="#001529" text-color="#ffffffa6" active-text-color="#fff">
        <el-menu-item index="/seller/dashboard"><el-icon><DataBoard /></el-icon><span>数据看板</span></el-menu-item>
        <el-menu-item index="/seller/goods"><el-icon><Goods /></el-icon><span>商品管理</span></el-menu-item>
        <el-menu-item index="/seller/orders">
          <el-icon><Document /></el-icon>
          <span>订单管理</span>
          <el-badge v-if="pendingCount > 0" :value="pendingCount" class="menu-badge" />
        </el-menu-item>
        <el-menu-item index="/seller/stats"><el-icon><TrendCharts /></el-icon><span>销量统计</span></el-menu-item>
        <el-menu-item index="/seller/settings"><el-icon><Setting /></el-icon><span>店铺设置</span></el-menu-item>
      </el-menu>
      <div class="seller-back" @click="$router.push('/')">← 返回商城</div>
    </el-aside>

    <!-- 右侧内容 -->
    <el-container>
      <el-header class="seller-header">
        <div class="header-left">
          <span class="shop-name">{{ userStore.userInfo?.shop_name || '我的店铺' }}</span>
          <el-badge v-if="pendingCount > 0" :value="pendingCount" class="notify-badge">
            <span class="notify-text">📦 待发货订单</span>
          </el-badge>
        </div>
        <div class="header-right">
          <span class="user-name">{{ userStore.nickname }}</span>
          <el-button text @click="handleLogout">退出登录</el-button>
        </div>
      </el-header>
      <el-main class="seller-main"><router-view /></el-main>
    </el-container>
  </el-container>
</template>

<script setup>
/* 商家后台布局组件（含订单轮询通知） */
import { ref, onMounted, onUnmounted } from 'vue'
import { useUserStore } from '../../store/user'
import { getOrderList } from '../../api/order'
import { extractList } from '../../utils/response'
import { DataBoard, Goods, Document, TrendCharts, Setting } from '@element-plus/icons-vue'

const userStore = useUserStore()
const pendingCount = ref(0)
let pollTimer = null

// 轮询待发货订单数量
async function checkPendingOrders() {
  try {
    const orders = extractList(await getOrderList({ status: 'paid', type: 'seller' }))
    const newCount = orders.length
    // 如果有新订单，浏览器通知
    if (newCount > pendingCount.value && pendingCount.value > 0) {
      notifyNewOrder(newCount)
    }
    pendingCount.value = newCount
  } catch {}
}

// 浏览器通知
function notifyNewOrder(count) {
  if ('Notification' in window && Notification.permission === 'granted') {
    new Notification('新订单提醒', {
      body: `您有 ${count} 个待发货订单`,
      icon: '📦'
    })
  }
}

// 请求通知权限
function requestNotifyPermission() {
  if ('Notification' in window && Notification.permission === 'default') {
    Notification.requestPermission()
  }
}

function handleLogout() {
  if (pollTimer) clearInterval(pollTimer)
  userStore.logout()
}

onMounted(() => {
  requestNotifyPermission()
  checkPendingOrders()
  // 每30秒轮询一次
  pollTimer = setInterval(checkPendingOrders, 30000)
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
})
</script>

<style scoped>
.seller-layout { min-height: 100vh; }
.seller-aside { background: #001529; overflow-y: auto; position: relative; }
.seller-logo { color: #fff; font-size: 18px; font-weight: bold; padding: 20px; text-align: center; cursor: pointer; border-bottom: 1px solid #ffffff1a; }
.seller-back { color: #ffffffa6; padding: 20px; cursor: pointer; position: absolute; bottom: 0; width: 220px; text-align: center; }
.seller-back:hover { color: #fff; }

.seller-header { display: flex; justify-content: space-between; align-items: center; background: #fff; border-bottom: 1px solid #f0f0f0; padding: 0 20px; }
.header-left { display: flex; align-items: center; gap: 20px; }
.header-right { display: flex; align-items: center; gap: 12px; }
.shop-name { font-weight: bold; font-size: 15px; color: #333; }
.user-name { font-size: 14px; color: #666; }
.notify-text { font-size: 13px; color: #ff4400; cursor: pointer; }
.notify-text:hover { text-decoration: underline; }

.menu-badge { margin-left: 8px; }
.menu-badge :deep(.el-badge__content) { font-size: 10px; }

.notify-badge :deep(.el-badge__content) {
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0% { transform: scale(1); }
  50% { transform: scale(1.2); }
  100% { transform: scale(1); }
}

.seller-main { background: #f5f5f5; min-height: calc(100vh - 60px); }
</style>
