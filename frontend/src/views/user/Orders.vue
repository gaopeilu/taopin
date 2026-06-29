<template>
  <div class="my-orders">
    <h2>我的订单</h2>
    <div class="tabs">
      <span :class="{active:status===''}" @click="status='';load()">全部</span>
      <span :class="{active:status==='pending'}" @click="status='pending';load()">待付款</span>
      <span :class="{active:status==='paid'}" @click="status='paid';load()">待发货</span>
      <span :class="{active:status==='shipped'}" @click="status='shipped';load()">已发货</span>
      <span :class="{active:status==='completed'}" @click="status='completed';load()">已完成</span>
      <span :class="{active:status==='refund'}" @click="status='refund';load()">退款</span>
    </div>
    <div v-loading="loading">
      <div v-for="o in orders" :key="o.order_no" class="order-card">
        <div class="o-header">
          <span>订单号：{{ o.order_no }}</span>
          <span class="o-time">{{ fmtDate(o.created_at) }}</span>
          <span class="tag" :class="o.status">{{ statusText(o.status) }}</span>
        </div>
        <div class="o-items">
          <div v-for="item in o.items" :key="item.id" class="o-item">
            <img :src="item.goods_image||'https://via.placeholder.com/60'" />
            <div class="oi-info"><div>{{ item.goods_name }}</div><div class="oi-spec" v-if="item.sku_name">{{ item.sku_name }}</div></div>
            <div class="oi-price">¥{{ item.price }} x{{ item.quantity }}</div>
          </div>
        </div>
        <div class="o-footer">
          <span>共 {{ o.items?.length||0 }} 件，合计：<b>¥{{ o.pay_amount }}</b></span>
          <div class="o-acts">
            <button v-if="o.status==='pending'" class="btn-pay" @click="goPay(o)">去付款</button>
            <button v-if="o.status==='pending'" class="btn-cancel" @click="handleCancel(o)">取消</button>
            <button v-if="o.status==='shipped'" class="btn-confirm" @click="handleComplete(o)">确认收货</button>
            <button v-if="['paid','shipped','completed'].includes(o.status)" class="btn-refund" @click="handleRefund(o)">退款</button>
            <button class="btn-detail" @click="$router.push(`/user/orders/${o.order_no}`)">详情</button>
          </div>
        </div>
      </div>
      <div v-if="!loading&&!orders.length" class="empty">暂无订单</div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getOrderList, cancelOrder, completeOrder, refundOrder } from '../../api/order'
import { extractList } from '../../utils/response'
import { ElMessage, ElMessageBox } from 'element-plus'

const router = useRouter()
const loading = ref(false)
const orders = ref([])
const status = ref('')
const statusText = s => ({pending:'待付款',paid:'待发货',shipped:'已发货',completed:'已完成',cancelled:'已取消',refund:'退款中'}[s]||s)
const fmtDate = d => d ? new Date(d).toLocaleString('zh-CN') : '-'

async function load() {
  loading.value = true
  try {
    const params = {}
    if (status.value) params.status = status.value
    orders.value = extractList(await getOrderList(params))
  } catch {} finally { loading.value = false }
}
function goPay(o) {
  sessionStorage.setItem('pay_order_no', o.order_no)
  sessionStorage.setItem('pay_total', o.pay_amount)
  router.push('/pay')
}
async function handleCancel(o) {
  await ElMessageBox.confirm('确定取消？','提示',{type:'warning'})
  try { await cancelOrder(o.order_no); ElMessage.success('已取消'); load() } catch {}
}
async function handleComplete(o) {
  await ElMessageBox.confirm('确认收货？','提示')
  try { await completeOrder(o.order_no); ElMessage.success('已确认'); load() } catch {}
}
async function handleRefund(o) {
  await ElMessageBox.confirm('申请退款？','提示',{type:'warning'})
  try { await refundOrder(o.order_no); ElMessage.success('已申请'); load() } catch {}
}
onMounted(load)
</script>

<style scoped>
.my-orders { max-width:900px; margin:0 auto; }
h2 { font-size:20px; margin-bottom:16px; }
.tabs { display:flex; background:#fff; border-radius:8px 8px 0 0; border-bottom:1px solid #f0f0f0; margin-bottom:12px; }
.tabs span { padding:12px 20px; cursor:pointer; color:#666; font-size:14px; }
.tabs span.active { color:#ff4400; border-bottom:2px solid #ff4400; font-weight:bold; }
.order-card { background:#fff; border-radius:8px; margin-bottom:12px; overflow:hidden; }
.o-header { display:flex; align-items:center; gap:12px; padding:12px 16px; background:#fafafa; font-size:13px; color:#666; }
.o-time { margin-left:auto; }
.tag { font-size:12px; padding:2px 8px; border-radius:3px; }
.tag.pending { background:#fff7e6; color:#fa8c16; }
.tag.paid { background:#e6f7ff; color:#1890ff; }
.tag.shipped { background:#e6f9ee; color:#52c41a; }
.tag.completed { background:#f5f5f5; color:#999; }
.tag.refund { background:#fff1f0; color:#f56c6c; }
.o-items { padding:12px 16px; }
.o-item { display:flex; align-items:center; gap:12px; padding:8px 0; }
.o-item img { width:60px; height:60px; object-fit:cover; border-radius:4px; }
.oi-info { flex:1; font-size:13px; }
.oi-spec { font-size:12px; color:#999; }
.oi-price { color:#666; font-size:13px; white-space:nowrap; }
.o-footer { display:flex; justify-content:space-between; align-items:center; padding:12px 16px; border-top:1px solid #f0f0f0; }
.o-footer b { color:#ff4400; font-size:16px; }
.o-acts { display:flex; gap:8px; }
.o-acts button { padding:6px 14px; border-radius:4px; cursor:pointer; font-size:12px; }
.btn-pay { background:#ff4400; color:#fff; border:none; }
.btn-cancel { background:#fff; color:#666; border:1px solid #ddd; }
.btn-confirm { background:#52c41a; color:#fff; border:none; }
.btn-refund { background:#fff; color:#f56c6c; border:1px solid #f56c6c; }
.btn-detail { background:#fff; color:#999; border:1px solid #eee; }
.empty { text-align:center; padding:60px; color:#ccc; background:#fff; border-radius:8px; }
</style>
