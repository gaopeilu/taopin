<template>
  <div class="order-detail" v-loading="loading">
    <div class="back" @click="$router.push('/user/orders')">← 返回订单列表</div>
    <template v-if="order">
      <div class="o-header">
        <span class="o-no">订单号：{{ order.order_no }}</span>
        <span class="tag" :class="order.status">{{ statusText(order.status) }}</span>
      </div>
      <div class="section">
        <div class="sec-title">收货信息</div>
        <div><b>{{ order.receiver_name }}</b> {{ order.receiver_phone }}</div>
        <div class="addr-text">{{ order.receiver_address }}</div>
      </div>
      <div class="section">
        <div class="sec-title">商品清单</div>
        <div v-for="item in order.items" :key="item.id" class="goods-item">
          <img :src="item.goods_image||'https://via.placeholder.com/60'" />
          <div class="gi-info"><div>{{ item.goods_name }}</div><div class="gi-spec" v-if="item.sku_name">{{ item.sku_name }}</div></div>
          <div class="gi-price">¥{{ item.price }} x{{ item.quantity }}</div>
          <div class="gi-sub">¥{{ item.subtotal }}</div>
        </div>
      </div>
      <div class="section">
        <div class="sec-title">订单信息</div>
        <div class="info-row"><span>状态</span><span>{{ statusText(order.status) }}</span></div>
        <div class="info-row"><span>下单时间</span><span>{{ fmtDate(order.created_at) }}</span></div>
        <div class="info-row" v-if="order.pay_time"><span>支付时间</span><span>{{ fmtDate(order.pay_time) }}</span></div>
        <div class="info-row" v-if="order.pay_method"><span>支付方式</span><span>{{ order.pay_method }}</span></div>
        <div class="info-row"><span>订单总额</span><span class="price">¥{{ order.total_amount }}</span></div>
        <div class="info-row"><span>实付金额</span><span class="price">¥{{ order.pay_amount }}</span></div>
      </div>
      <div class="actions">
        <button v-if="order.status==='pending'" class="btn-pay" @click="goPay">去付款</button>
        <button v-if="order.status==='pending'" class="btn-cancel" @click="handleCancel">取消</button>
        <button v-if="order.status==='shipped'" class="btn-confirm" @click="handleComplete">确认收货</button>
        <button v-if="['paid','shipped','completed'].includes(order.status)" class="btn-refund" @click="handleRefund">退款</button>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getOrderDetail, cancelOrder, completeOrder, refundOrder } from '../../api/order'
import { extractData } from '../../utils/response'
import { ElMessage, ElMessageBox } from 'element-plus'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const order = ref(null)
const statusText = s => ({pending:'待付款',paid:'待发货',shipped:'已发货',completed:'已完成',cancelled:'已取消',refund:'退款中'}[s]||s)
const fmtDate = d => d ? new Date(d).toLocaleString('zh-CN') : '-'

async function load() {
  loading.value = true
  try { order.value = extractData(await getOrderDetail(route.params.orderNo)) } catch {} finally { loading.value = false }
}
function goPay() {
  sessionStorage.setItem('pay_order_no', order.value.order_no)
  sessionStorage.setItem('pay_total', order.value.pay_amount)
  router.push('/pay')
}
async function handleCancel() {
  await ElMessageBox.confirm('确定取消？','提示',{type:'warning'})
  try { await cancelOrder(order.value.order_no); ElMessage.success('已取消'); load() } catch {}
}
async function handleComplete() {
  await ElMessageBox.confirm('确认收货？')
  try { await completeOrder(order.value.order_no); ElMessage.success('已确认'); load() } catch {}
}
async function handleRefund() {
  await ElMessageBox.confirm('申请退款？',{type:'warning'})
  try { await refundOrder(order.value.order_no); ElMessage.success('已申请'); load() } catch {}
}
onMounted(load)
</script>

<style scoped>
.order-detail { max-width:800px; margin:0 auto; }
.back { font-size:13px; color:#999; cursor:pointer; margin-bottom:16px; }
.back:hover { color:#ff4400; }
.o-header { display:flex; align-items:center; gap:12px; background:#fff; border-radius:8px; padding:16px; margin-bottom:12px; }
.o-no { font-size:15px; font-weight:bold; }
.tag { font-size:12px; padding:3px 10px; border-radius:3px; }
.tag.pending { background:#fff7e6; color:#fa8c16; }
.tag.paid { background:#e6f7ff; color:#1890ff; }
.tag.shipped { background:#e6f9ee; color:#52c41a; }
.tag.completed { background:#f5f5f5; color:#999; }
.tag.refund { background:#fff1f0; color:#f56c6c; }
.section { background:#fff; border-radius:8px; padding:16px; margin-bottom:12px; }
.sec-title { font-size:14px; font-weight:bold; margin-bottom:12px; padding-bottom:8px; border-bottom:1px solid #f0f0f0; }
.addr-text { font-size:13px; color:#666; margin-top:4px; }
.goods-item { display:flex; align-items:center; gap:12px; padding:10px 0; border-bottom:1px solid #f5f5f5; }
.goods-item:last-child { border-bottom:none; }
.goods-item img { width:60px; height:60px; object-fit:cover; border-radius:4px; }
.gi-info { flex:1; font-size:13px; }
.gi-spec { font-size:12px; color:#999; }
.gi-price { color:#666; width:100px; font-size:13px; }
.gi-sub { color:#ff4400; font-weight:bold; width:80px; text-align:right; }
.info-row { display:flex; justify-content:space-between; padding:6px 0; font-size:13px; }
.info-row span:first-child { color:#999; }
.price { color:#ff4400; font-weight:bold; }
.actions { display:flex; gap:10px; justify-content:flex-end; padding:16px 0; }
.actions button { padding:10px 24px; border-radius:4px; cursor:pointer; font-size:14px; }
.btn-pay { background:#ff4400; color:#fff; border:none; }
.btn-cancel { background:#fff; color:#666; border:1px solid #ddd; }
.btn-confirm { background:#52c41a; color:#fff; border:none; }
.btn-refund { background:#fff; color:#f56c6c; border:1px solid #f56c6c; }
</style>
