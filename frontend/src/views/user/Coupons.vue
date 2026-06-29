<template>
  <div class="coupons-page"><h2>我的优惠券</h2>
    <div class="tabs">
      <span :class="{active:status===''}" @click="status='';load()">全部</span>
      <span :class="{active:status==='unused'}" @click="status='unused';load()">未使用</span>
      <span :class="{active:status==='used'}" @click="status='used';load()">已使用</span>
      <span :class="{active:status==='expired'}" @click="status='expired';load()">已过期</span>
    </div>
    <div v-loading="loading">
      <div v-for="c in coupons" :key="c.id" class="coupon" :class="c.status">
        <div class="c-left"><div class="c-val"><span v-if="c.coupon_type==='minus'">¥{{ c.coupon_value }}</span><span v-else-if="c.coupon_type==='discount'">{{ c.coupon_value }}折</span><span v-else>¥{{ c.coupon_value }}</span></div><div class="c-cond" v-if="c.min_amount!=='0.00'">满{{ c.min_amount }}可用</div></div>
        <div class="c-right"><div class="c-name">{{ c.coupon_name }}</div><div class="c-time">{{ fmtDate(c.claimed_at) }}</div><div class="c-status">{{ statusText(c.status) }}</div></div>
      </div>
      <div v-if="!loading&&!coupons.length" class="empty">暂无优惠券</div>
    </div>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import { getMyCoupons } from '../../api/coupon'
import { extractList } from '../../utils/response'
const loading = ref(false)
const coupons = ref([])
const status = ref('')
const statusText = s => ({unused:'未使用',used:'已使用',expired:'已过期'}[s]||s)
const fmtDate = d => d ? new Date(d).toLocaleDateString('zh-CN') : '-'
async function load() { loading.value = true; try { const params = {}; if (status.value) params.status = status.value; coupons.value = extractList(await getMyCoupons(params)) } catch {} finally { loading.value = false } }
onMounted(load)
</script>
<style scoped>
.coupons-page { max-width:800px; margin:0 auto; }
h2 { font-size:20px; margin-bottom:16px; }
.tabs { display:flex; background:#fff; border-radius:8px 8px 0 0; border-bottom:1px solid #f0f0f0; margin-bottom:12px; }
.tabs span { padding:12px 20px; cursor:pointer; color:#666; font-size:14px; }
.tabs span.active { color:#ff4400; border-bottom:2px solid #ff4400; font-weight:bold; }
.coupon { display:flex; background:#fff; border-radius:8px; margin-bottom:10px; overflow:hidden; }
.coupon.used,.coupon.expired { opacity:.6; }
.c-left { width:120px; background:linear-gradient(135deg,#ff4400,#ff6633); color:#fff; display:flex; flex-direction:column; align-items:center; justify-content:center; padding:16px; }
.coupon.used .c-left,.coupon.expired .c-left { background:#ccc; }
.c-val { font-size:24px; font-weight:bold; }
.c-cond { font-size:11px; margin-top:4px; }
.c-right { flex:1; padding:16px; display:flex; flex-direction:column; justify-content:center; }
.c-name { font-size:14px; font-weight:bold; margin-bottom:4px; }
.c-time { font-size:12px; color:#999; }
.c-status { font-size:12px; color:#ff4400; margin-top:4px; }
.coupon.used .c-status,.coupon.expired .c-status { color:#999; }
.empty { text-align:center; padding:60px; color:#ccc; background:#fff; border-radius:8px; }
</style>
