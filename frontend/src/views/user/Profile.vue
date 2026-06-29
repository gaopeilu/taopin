<template>
  <div class="profile-page">
    <div class="profile-card">
      <img :src="userStore.avatar||'https://via.placeholder.com/80'" class="avatar" />
      <div class="meta">
        <div class="name">{{ userStore.nickname }}</div>
        <div class="id">ID: {{ userStore.userId }}</div>
        <div class="role">{{ userStore.isSellerUser ? '🏪 商家' : '👤 普通用户' }}</div>
      </div>
      <button v-if="!userStore.isSellerUser" class="btn-upgrade" @click="$router.push('/user/upgrade')">升级为商家</button>
    </div>

    <div class="order-overview">
      <div class="ov-title">我的订单</div>
      <div class="ov-stats">
        <div @click="$router.push('/user/orders')"><span class="num">{{ counts.total }}</span><span>全部</span></div>
        <div @click="$router.push('/user/orders')"><span class="num">{{ counts.pending }}</span><span>待付款</span></div>
        <div @click="$router.push('/user/orders')"><span class="num">{{ counts.paid }}</span><span>待发货</span></div>
        <div @click="$router.push('/user/orders')"><span class="num">{{ counts.shipped }}</span><span>已发货</span></div>
        <div @click="$router.push('/user/orders')"><span class="num">{{ counts.completed }}</span><span>已完成</span></div>
      </div>
    </div>

    <div class="menu-grid">
      <div @click="$router.push('/user/orders')">📦 我的订单</div>
      <div @click="$router.push('/cart')">🛒 购物车</div>
      <div @click="$router.push('/user/address')">📍 收货地址</div>
      <div @click="$router.push('/user/settings')">⚙️ 个人设置</div>
      <div @click="$router.push('/user/reviews')">⭐ 我的评价</div>
      <div @click="$router.push('/user/coupons')">🎫 我的优惠券</div>
      <div @click="$router.push('/coupons')">🎁 领券中心</div>
      <div v-if="userStore.isSellerUser" @click="$router.push('/seller')">🏪 商家后台</div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useUserStore } from '../../store/user'
import { getOrderList } from '../../api/order'
import { extractList } from '../../utils/response'

const userStore = useUserStore()
const counts = ref({ total:0, pending:0, paid:0, shipped:0, completed:0 })

onMounted(async () => {
  try {
    const orders = extractList(await getOrderList())
    counts.value = {
      total: orders.length,
      pending: orders.filter(o=>o.status==='pending').length,
      paid: orders.filter(o=>o.status==='paid').length,
      shipped: orders.filter(o=>o.status==='shipped').length,
      completed: orders.filter(o=>o.status==='completed').length,
    }
  } catch {}
})
</script>

<style scoped>
.profile-page { max-width:800px; margin:0 auto; }
.profile-card { display:flex; align-items:center; gap:20px; background:#fff; border-radius:12px; padding:28px; margin-bottom:16px; }
.avatar { width:80px; height:80px; border-radius:50%; object-fit:cover; }
.meta { flex:1; }
.name { font-size:20px; font-weight:bold; }
.id { font-size:12px; color:#999; margin-top:4px; }
.role { font-size:13px; color:#ff4400; margin-top:4px; }
.btn-upgrade { padding:8px 20px; background:#fff; color:#ff4400; border:1px solid #ff4400; border-radius:20px; cursor:pointer; font-size:13px; }
.order-overview { background:#fff; border-radius:12px; padding:20px; margin-bottom:16px; }
.ov-title { font-size:15px; font-weight:bold; margin-bottom:16px; }
.ov-stats { display:flex; justify-content:space-around; }
.ov-stats div { display:flex; flex-direction:column; align-items:center; cursor:pointer; padding:8px 16px; border-radius:8px; }
.ov-stats div:hover { background:#f5f5f5; }
.num { font-size:24px; font-weight:bold; color:#ff4400; }
.ov-stats span:last-child { font-size:12px; color:#999; margin-top:4px; }
.menu-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(140px,1fr)); gap:12px; }
.menu-grid div { display:flex; flex-direction:column; align-items:center; gap:10px; padding:24px; background:#fff; border-radius:12px; cursor:pointer; font-size:14px; transition:box-shadow .2s; }
.menu-grid div:hover { box-shadow:0 4px 12px rgba(0,0,0,.06); }
</style>
