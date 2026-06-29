/**
 * 路由配置
 * 区分买家端和商家后台路由，商家路由需要seller权限
 */
import { createRouter, createWebHistory } from 'vue-router'
import { isLoggedIn, isSeller } from '../utils/auth'
import { ElMessage } from 'element-plus'

/* 路由表 */
const routes = [
  /* ===== 认证 ===== */
  { path: '/login', name: 'Login', component: () => import('../views/auth/Login.vue'), meta: { guest: true } },
  { path: '/register', redirect: '/login' },

  /* ===== 买家端 ===== */
  {
    path: '/',
    component: () => import('../components/layout/UserLayout.vue'),
    children: [
      { path: '', name: 'Home', component: () => import('../views/home/Index.vue') },
      { path: 'goods', name: 'GoodsList', component: () => import('../views/goods/List.vue') },
      { path: 'goods/:id', name: 'GoodsDetail', component: () => import('../views/goods/Detail.vue') },
      { path: 'cart', name: 'Cart', component: () => import('../views/cart/Index.vue'), meta: { auth: true } },
      { path: 'checkout', name: 'Checkout', component: () => import('../views/order/Checkout.vue'), meta: { auth: true } },
      { path: 'pay', name: 'Pay', component: () => import('../views/order/Pay.vue'), meta: { auth: true } },
      { path: 'user', name: 'UserProfile', component: () => import('../views/user/Profile.vue'), meta: { auth: true } },
      { path: 'user/orders', name: 'UserOrders', component: () => import('../views/user/Orders.vue'), meta: { auth: true } },
      { path: 'user/orders/:orderNo', name: 'OrderDetail', component: () => import('../views/user/OrderDetail.vue'), meta: { auth: true } },
      { path: 'user/address', name: 'UserAddress', component: () => import('../views/user/Address.vue'), meta: { auth: true } },
      { path: 'user/settings', name: 'UserSettings', component: () => import('../views/user/Settings.vue'), meta: { auth: true } },
      { path: 'user/upgrade', name: 'UserUpgrade', component: () => import('../views/user/Upgrade.vue'), meta: { auth: true } },
      { path: 'user/reviews', name: 'MyReviews', component: () => import('../views/user/MyReviews.vue'), meta: { auth: true } },
      { path: 'user/coupons', name: 'MyCoupons', component: () => import('../views/user/Coupons.vue'), meta: { auth: true } },
      { path: 'coupons', name: 'CouponCenter', component: () => import('../views/home/CouponCenter.vue') },
      { path: 'search/history', name: 'SearchHistory', component: () => import('../views/search/History.vue'), meta: { auth: true } },
    ]
  },

  /* ===== 商家后台 ===== */
  {
    path: '/seller',
    component: () => import('../components/layout/SellerLayout.vue'),
    meta: { auth: true, requiresSeller: true },
    redirect: '/seller/dashboard',
    children: [
      { path: 'dashboard', name: 'SellerDashboard', component: () => import('../views/seller/Dashboard.vue') },
      { path: 'goods', name: 'SellerGoods', component: () => import('../views/seller/GoodsList.vue') },
      { path: 'goods/add', name: 'SellerGoodsAdd', component: () => import('../views/seller/GoodsForm.vue') },
      { path: 'goods/edit/:id', name: 'SellerGoodsEdit', component: () => import('../views/seller/GoodsForm.vue') },
      { path: 'orders', name: 'SellerOrders', component: () => import('../views/seller/Orders.vue') },
      { path: 'stats', name: 'SellerStats', component: () => import('../views/seller/Stats.vue') },
      { path: 'settings', name: 'SellerSettings', component: () => import('../views/seller/ShopSettings.vue') },
    ]
  },

  /* 404 */
  { path: '/:pathMatch(.*)*', redirect: '/' }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior: () => ({ top: 0 })
})

/* ========== 全局路由守卫 ========== */
router.beforeEach((to, from) => {
  const logged = isLoggedIn()
  const seller = isSeller()

  // 已登录访问登录/注册页 → 跳首页
  if (to.meta.guest && logged) return '/'

  // 需要登录但未登录 → 跳登录
  if (to.meta.auth && !logged) return '/login'

  // 需要商家权限但不是商家 → 跳首页
  if (to.meta.requiresSeller && !seller) {
    ElMessage.warning('无访问权限')
    return '/'
  }
})

export default router
