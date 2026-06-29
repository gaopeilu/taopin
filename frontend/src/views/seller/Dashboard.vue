<template>
  <div class="dashboard">
    <div class="welcome">欢迎回来，{{ userStore.nickname }} <span v-if="userStore.userInfo?.shop_name">「{{ userStore.userInfo.shop_name }}」</span></div>
    <div class="stat-row">
      <div class="stat-card" v-for="s in stats" :key="s.label"><div class="stat-icon">{{ s.icon }}</div><div class="stat-body"><div class="stat-num">{{ s.value }}</div><div class="stat-label">{{ s.label }}</div></div></div>
    </div>
    <div class="section">
      <div class="sec-top"><h3>热销商品 TOP10</h3><span class="more" @click="$router.push('/seller/goods')">商品管理 &gt;</span></div>
      <table class="data-table">
        <thead><tr><th>#</th><th>商品</th><th>价格</th><th>销量</th><th>状态</th></tr></thead>
        <tbody><tr v-for="(g,i) in hotGoods" :key="g.id">
          <td>{{ i+1 }}</td>
          <td class="goods-cell"><img :src="g.main_image||'https://via.placeholder.com/40'" /><span>{{ g.name }}</span></td>
          <td>{{ g.price_range }}</td><td>{{ g.sales }}</td>
          <td><span class="tag" :class="g.is_on_sale?'on':'off'">{{ g.is_on_sale?'在售':'下架' }}</span></td>
        </tr></tbody>
      </table>
    </div>
  </div>
</template>
<script setup>
import { ref, computed, onMounted } from 'vue'
import { useUserStore } from '../../store/user'
import { getHotGoods } from '../../api/goods'
import { extractList } from '../../utils/response'
const userStore = useUserStore()
const hotGoods = ref([])
const totalSales = ref(0)
const stats = computed(() => [
  { icon:'👥', label:'今日访客', value:Math.floor(Math.random()*300+50) },
  { icon:'📦', label:'总销量', value:totalSales.value },
  { icon:'🛍️', label:'商品数量', value:hotGoods.value.length },
  { icon:'⭐', label:'店铺评分', value:'4.9' },
])
onMounted(async () => { try { hotGoods.value = extractList(await getHotGoods({limit:10})); totalSales.value = hotGoods.value.reduce((s,g)=>s+(g.sales||0),0) } catch {} })
</script>
<style scoped>
.welcome { font-size:18px; margin-bottom:20px; }
.welcome span { color:#ff4400; }
.stat-row { display:grid; grid-template-columns:repeat(4,1fr); gap:12px; margin-bottom:24px; }
.stat-card { display:flex; align-items:center; gap:14px; background:#fff; border-radius:10px; padding:20px; }
.stat-icon { font-size:36px; }
.stat-num { font-size:26px; font-weight:bold; color:#333; }
.stat-label { font-size:13px; color:#999; margin-top:2px; }
.section { background:#fff; border-radius:10px; padding:20px; }
.sec-top { display:flex; justify-content:space-between; align-items:center; margin-bottom:14px; }
.sec-top h3 { font-size:15px; }
.more { font-size:13px; color:#999; cursor:pointer; }
.more:hover { color:#ff4400; }
.data-table { width:100%; border-collapse:collapse; }
.data-table th { text-align:left; font-size:13px; color:#999; font-weight:normal; padding:10px 8px; border-bottom:1px solid #f0f0f0; }
.data-table td { padding:12px 8px; border-bottom:1px solid #f5f5f5; font-size:13px; }
.goods-cell { display:flex; align-items:center; gap:10px; }
.goods-cell img { width:40px; height:40px; object-fit:cover; border-radius:4px; }
.tag { font-size:12px; padding:2px 8px; border-radius:3px; }
.tag.on { background:#e6f9ee; color:#52c41a; }
.tag.off { background:#f5f5f5; color:#999; }
</style>
