<template>
  <div class="seller-orders"><h2>订单管理</h2>
    <div class="tabs">
      <span :class="{active:status===''}" @click="status='';load()">全部</span>
      <span :class="{active:status==='pending'}" @click="status='pending';load()">待付款</span>
      <span :class="{active:status==='paid'}" @click="status='paid';load()">待发货</span>
      <span :class="{active:status==='shipped'}" @click="status='shipped';load()">已发货</span>
      <span :class="{active:status==='completed'}" @click="status='completed';load()">已完成</span>
      <span :class="{active:status==='refund'}" @click="status='refund';load()">退款</span>
    </div>
    <table class="order-table" v-loading="loading">
      <thead><tr><th>订单号</th><th>商品</th><th>买家</th><th>金额</th><th>状态</th><th>时间</th><th>操作</th></tr></thead>
      <tbody><tr v-for="o in orders" :key="o.order_no">
        <td class="ono">{{ o.order_no }}</td>
        <td><div v-for="item in o.items" :key="item.id" class="o-goods"><img :src="item.goods_image||'https://via.placeholder.com/36'" /><span>{{ item.goods_name }} x{{ item.quantity }}</span></div></td>
        <td>{{ o.receiver_name }}</td>
        <td class="oprice">¥{{ o.pay_amount }}</td>
        <td><span class="tag" :class="o.status">{{ statusText(o.status) }}</span></td>
        <td class="otime">{{ fmtDate(o.created_at) }}</td>
        <td class="oact"><button v-if="o.status==='paid'" @click="handleShip(o)">发货</button><button v-if="o.status==='refund'" @click="handleRefund(o)">处理</button></td>
      </tr></tbody>
    </table>
    <div v-if="!loading&&!orders.length" class="empty">暂无订单</div>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import { getOrderList, shipOrder, refundOrder } from '../../api/order'
import { extractList } from '../../utils/response'
import { ElMessage, ElMessageBox } from 'element-plus'
const loading = ref(false)
const orders = ref([])
const status = ref('')
const statusText = s => ({pending:'待付款',paid:'待发货',shipped:'已发货',completed:'已完成',cancelled:'已取消',refund:'退款中'}[s]||s)
const fmtDate = d => d ? new Date(d).toLocaleString('zh-CN') : '-'
async function load() { loading.value = true; try { const params = { type: 'seller' }; if (status.value) params.status = status.value; orders.value = extractList(await getOrderList(params)) } catch {} finally { loading.value = false } }
async function handleShip(o) { await ElMessageBox.confirm(`订单 ${o.order_no} 确认发货？`); try { await shipOrder(o.order_no); ElMessage.success('已发货'); load() } catch {} }
async function handleRefund(o) { await ElMessageBox.confirm(`订单 ${o.order_no} 确认退款？`); try { await refundOrder(o.order_no); ElMessage.success('已处理'); load() } catch {} }
onMounted(load)
</script>
<style scoped>
h2 { font-size:18px; margin-bottom:16px; }
.tabs { display:flex; background:#fff; border-radius:8px 8px 0 0; border-bottom:1px solid #f0f0f0; margin-bottom:0; }
.tabs span { padding:12px 20px; cursor:pointer; color:#666; font-size:14px; }
.tabs span.active { color:#ff4400; border-bottom:2px solid #ff4400; font-weight:bold; }
.order-table { width:100%; background:#fff; border-collapse:collapse; }
.order-table th { text-align:left; font-size:13px; color:#999; font-weight:normal; padding:12px 10px; border-bottom:1px solid #f0f0f0; }
.order-table td { padding:14px 10px; border-bottom:1px solid #f5f5f5; font-size:13px; vertical-align:top; }
.ono { font-family:monospace; color:#666; }
.o-goods { display:flex; align-items:center; gap:8px; margin-bottom:4px; }
.o-goods img { width:36px; height:36px; object-fit:cover; border-radius:3px; }
.oprice { color:#ff4400; font-weight:bold; }
.otime { color:#999; font-size:12px; }
.oact button { padding:4px 12px; background:#1890ff; color:#fff; border:none; border-radius:3px; cursor:pointer; font-size:12px; }
.tag { font-size:12px; padding:2px 8px; border-radius:3px; }
.tag.pending { background:#fff7e6; color:#fa8c16; }
.tag.paid { background:#e6f7ff; color:#1890ff; }
.tag.shipped { background:#e6f9ee; color:#52c41a; }
.tag.completed { background:#f5f5f5; color:#999; }
.tag.refund { background:#fff1f0; color:#f56c6c; }
.empty { text-align:center; padding:40px; color:#ccc; background:#fff; }
</style>
