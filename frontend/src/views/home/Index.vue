<template>
  <div class="home">
    <!-- 顶部分类导航 -->
    <div class="cat-nav">
      <div class="cat-nav-inner">
        <span class="cat-item" :class="{active: activeCat===null}" @click="activeCat=null">全部</span>
        <span class="cat-item" v-for="cat in topCategories" :key="cat.id" :class="{active: activeCat===cat.id}" @click="goCategory(cat.id)">{{ cat.name }}</span>
      </div>
    </div>

    <div class="home-main">
      <!-- 左侧分类侧栏 -->
      <aside class="side-cats">
        <div class="side-title">全部分类</div>
        <div class="side-cats-scroll">
          <div v-for="cat in categories" :key="cat.id" class="side-group">
            <div class="side-group-title" @click="goCategory(cat.id)">{{ cat.name }}</div>
            <div v-for="child in cat.children" :key="child.id" class="side-child" @click="goCategory(child.id)">{{ child.name }}</div>
          </div>
        </div>
      </aside>

      <!-- 中间内容 -->
      <div class="home-center">
        <el-carousel height="420px" class="banner" :interval="4000" indicator-position="outside">
          <el-carousel-item v-for="(b,i) in banners" :key="i">
            <div class="banner-card" :style="{background: b.bg}">
              <div>
                <div class="banner-tag">{{ b.tag }}</div>
                <h2>{{ b.title }}</h2>
                <p>{{ b.desc }}</p>
                <button class="banner-btn" @click="$router.push('/goods')">立即查看</button>
              </div>
              <div class="banner-icon">{{ b.icon }}</div>
            </div>
          </el-carousel-item>
        </el-carousel>
        <div class="brand-bar">
          <div class="brand-title">热门品牌</div>
          <div class="brand-list">
            <span v-for="b in brands" :key="b.id" class="brand-chip" @click="$router.push({path:'/goods',query:{q:b.name}})">{{ b.name }}</span>
          </div>
        </div>
      </div>

      <!-- 右侧用户栏 -->
      <aside class="side-user">
        <template v-if="userStore.loggedIn">
          <div class="user-card">
            <el-avatar :size="48" :src="userStore.avatar" />
            <div class="user-name">{{ userStore.nickname }}</div>
            <div class="user-role">{{ userStore.isSellerUser ? '商家' : '会员' }}</div>
          </div>
          <div class="user-links">
            <div @click="$router.push('/user/orders')">📦 我的订单</div>
            <div @click="$router.push('/cart')">🛒 购物车({{ cartStore.totalCount }})</div>
            <div @click="$router.push('/coupons')">🎫 领券中心</div>
            <div @click="openAddrDialog">📍 收货地址</div>
            <div @click="$router.push('/user/settings')">⚙️ 个人设置</div>
            <div v-if="userStore.isSellerUser" @click="$router.push('/seller')">🏪 商家后台</div>
          </div>
        </template>
        <template v-else>
          <div class="user-card">
            <div class="user-name">Hi，欢迎来到淘拼商城</div>
            <el-button type="primary" size="small" @click="$router.push('/login')" style="margin-top:12px">登录</el-button>
            <el-button size="small" @click="$router.push('/login')" style="margin-top:8px">注册</el-button>
          </div>
        </template>
        <div class="notice-box">
          <div class="notice-title">📢 平台公告</div>
          <div class="notice-item">618年中大促，全场满减</div>
          <div class="notice-item">新人注册享专属优惠</div>
        </div>
      </aside>
    </div>

    <!-- 热销商品 -->
    <div class="section">
      <div class="section-header">
        <div class="section-title">🔥 热销爆款</div>
        <span class="section-more" @click="$router.push({path:'/goods',query:{ordering:'-sales'}})">查看更多 &gt;</span>
      </div>
      <div class="goods-grid"><GoodsCard v-for="item in hotGoods" :key="item.id" :goods="item" /></div>
    </div>

    <!-- 新品上架 -->
    <div class="section">
      <div class="section-header">
        <div class="section-title">🆕 新品上架</div>
        <span class="section-more" @click="$router.push({path:'/goods',query:{ordering:'-created_at'}})">查看更多 &gt;</span>
      </div>
      <div class="goods-grid"><GoodsCard v-for="item in newGoods" :key="item.id" :goods="item" /></div>
    </div>

    <!-- 分类精选 -->
    <div class="section" v-for="cat in featuredCats" :key="cat.id">
      <div class="section-header">
        <div class="section-title">{{ cat.icon }} {{ cat.name }}</div>
        <span class="section-more" @click="goCategory(cat.id)">查看更多 &gt;</span>
      </div>
      <div class="goods-grid"><GoodsCard v-for="item in cat.goods" :key="item.id" :goods="item" /></div>
    </div>

    <!-- 收货地址弹窗 -->
    <AddrDialog v-model:visible="addrDialogVisible" />
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { getCategoryTree, getHotGoods, getGoodsList, getBrands } from '../../api/goods'
import { useUserStore } from '../../store/user'
import { useCartStore } from '../../store/cart'
import { extractList, extractPage } from '../../utils/response'
import GoodsCard from '../../components/goods/GoodsCard.vue'
import AddrDialog from '../../components/common/AddrDialog.vue'

const router = useRouter()
const userStore = useUserStore()
const cartStore = useCartStore()
const categories = ref([])
const brands = ref([])
const hotGoods = ref([])
const newGoods = ref([])
const activeCat = ref(null)
const featuredCats = ref([])
const addrDialogVisible = ref(false)

const topCategories = computed(() => categories.value.map(c => ({ id: c.id, name: c.name })))
const catIcons = { '手机数码':'📱','电脑办公':'💻','服装鞋包':'👗','食品生鲜':'🍎','食品饮料':'🥤','美妆个护':'💄','家居家装':'🏠','母婴玩具':'🧸','运动户外':'⚽','Clothing':'👔' }
const banners = [
  { tag:'限时折扣', title:'618年中大促', desc:'爆款商品低至5折起', bg:'linear-gradient(135deg,#ff4e50,#f9d423)', icon:'🎉' },
  { tag:'新品首发', title:'数码新品季', desc:'手机电脑新品首发', bg:'linear-gradient(135deg,#4facfe,#00f2fe)', icon:'📱' },
  { tag:'品质好物', title:'品牌特卖', desc:'大牌折扣', bg:'linear-gradient(135deg,#a18cd1,#fbc2eb)', icon:'🏷️' },
]

function goCategory(id) { router.push({ path: '/goods', query: { category: id } }) }
function openAddrDialog() {
  if (!userStore.loggedIn) { router.push('/login'); return }
  addrDialogVisible.value = true
}

onMounted(async () => {
  // 加载分类树
  try {
    const catRes = await getCategoryTree()
    // 兼容多种响应格式
    if (Array.isArray(catRes)) {
      categories.value = catRes
    } else if (catRes && Array.isArray(catRes.data)) {
      categories.value = catRes.data
    } else if (catRes && catRes.results) {
      categories.value = catRes.results
    } else {
      categories.value = []
    }
  } catch (e) {
    categories.value = []
  }

  // 加载热销商品（hot接口返回 {code, data} 格式）
  try {
    const hotRes = await getHotGoods({ limit: 10 })
    if (Array.isArray(hotRes)) {
      hotGoods.value = hotRes
    } else if (hotRes && Array.isArray(hotRes.data)) {
      hotGoods.value = hotRes.data
    } else {
      hotGoods.value = []
    }
  } catch {}

  // 加载新品（spus接口返回 DRF分页 {count, results} 格式）
  try {
    const newRes = await getGoodsList({ ordering: '-created_at', page: 1 })
    const list = newRes?.results || newRes?.data?.results || []
    newGoods.value = list.slice(0, 10)
  } catch {}

  // 加载品牌
  try {
    const brandRes = await getBrands()
    const list = brandRes?.results || brandRes?.data?.results || []
    brands.value = list.slice(0, 15)
  } catch {}

  // 分类精选（等分类加载完再处理）
  const featured = []
  for (const cat of categories.value) {
    const children = cat.children || []
    for (const child of children.slice(0, 2)) {
      try {
        const res = await getGoodsList({ category: child.id, page: 1 })
        const goods = (res?.results || []).slice(0, 5)
        if (goods.length) featured.push({ id: child.id, name: child.name, icon: catIcons[cat.name]||'📦', goods })
      } catch {}
    }
    if (!children.length) {
      try {
        const res = await getGoodsList({ category: cat.id, page: 1 })
        const goods = (res?.results || []).slice(0, 5)
        if (goods.length) featured.push({ id: cat.id, name: cat.name, icon: catIcons[cat.name]||'📦', goods })
      } catch {}
    }
  }
  featuredCats.value = featured
})
</script>

<style scoped>
.home { background: #f5f5f5; min-height: 100vh; }
.cat-nav { background: #fff; border-bottom: 1px solid #eee; }
.cat-nav-inner { max-width: 1200px; margin: 0 auto; display: flex; overflow-x: auto; }
.cat-item { padding: 12px 20px; cursor: pointer; white-space: nowrap; font-size: 14px; color: #666; border-bottom: 2px solid transparent; }
.cat-item:hover, .cat-item.active { color: #ff4400; border-bottom-color: #ff4400; font-weight: bold; }

.home-main { max-width: 1200px; margin: 12px auto; display: flex; gap: 12px; align-items: stretch; }

.side-cats { width: 200px; background: #fff; border-radius: 8px; flex-shrink: 0; display: flex; flex-direction: column; }
.side-title { font-weight: bold; font-size: 15px; padding: 16px; border-bottom: 1px solid #f0f0f0; }
.side-cats-scroll { flex: 1; overflow-y: auto; padding: 8px 16px 16px; }
.side-cats-scroll::-webkit-scrollbar { width: 4px; }
.side-cats-scroll::-webkit-scrollbar-thumb { background: #ddd; border-radius: 2px; }
.side-group { margin-bottom: 10px; }
.side-group-title { font-size: 13px; font-weight: bold; color: #333; cursor: pointer; padding: 4px 0; }
.side-group-title:hover { color: #ff4400; }
.side-child { font-size: 12px; color: #666; padding: 3px 0 3px 12px; cursor: pointer; }
.side-child:hover { color: #ff4400; }

.home-center { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 10px; }
.banner { border-radius: 8px; overflow: hidden; flex-shrink: 0; }
.banner-card { height: 100%; display: flex; align-items: center; justify-content: space-between; padding: 0 48px; color: #fff; }
.banner-tag { display: inline-block; background: rgba(255,255,255,.25); padding: 4px 12px; border-radius: 12px; font-size: 12px; margin-bottom: 12px; }
.banner-card h2 { font-size: 32px; margin-bottom: 8px; }
.banner-card p { font-size: 15px; opacity: .9; margin-bottom: 16px; }
.banner-btn { background: #fff; color: #ff4400; border: none; padding: 8px 24px; border-radius: 20px; font-size: 14px; font-weight: bold; cursor: pointer; }
.banner-icon { font-size: 80px; opacity: .3; }
.brand-bar { background: #fff; border-radius: 8px; padding: 14px 16px; }
.brand-title { font-size: 14px; font-weight: bold; margin-bottom: 10px; }
.brand-list { display: flex; flex-wrap: wrap; gap: 8px; }
.brand-chip { padding: 4px 14px; background: #f5f5f5; border-radius: 14px; font-size: 12px; color: #666; cursor: pointer; }
.brand-chip:hover { background: #fff0e6; color: #ff4400; }

.side-user { width: 200px; flex-shrink: 0; display: flex; flex-direction: column; gap: 10px; }
.user-card { background: #fff; border-radius: 8px; padding: 20px; text-align: center; }
.user-name { font-weight: bold; margin-top: 8px; font-size: 14px; }
.user-role { color: #999; font-size: 12px; margin-top: 4px; }
.user-links { background: #fff; border-radius: 8px; padding: 12px; flex: 1; }
.user-links > div { padding: 10px 12px; cursor: pointer; font-size: 13px; color: #666; border-radius: 4px; }
.user-links > div:hover { background: #f5f5f5; color: #ff4400; }
.notice-box { background: #fff; border-radius: 8px; padding: 12px; }
.notice-title { font-size: 13px; font-weight: bold; margin-bottom: 8px; }
.notice-item { font-size: 12px; color: #999; padding: 4px 0; }

.section { max-width: 1200px; margin: 10px auto 0; }
.section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.section-title { font-size: 18px; font-weight: bold; color: #333; }
.section-more { font-size: 13px; color: #999; cursor: pointer; }
.section-more:hover { color: #ff4400; }
.goods-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 12px; }
</style>
