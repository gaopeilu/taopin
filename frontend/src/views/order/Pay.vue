<template>
  <div class="pay-page">
    <div class="pay-card" v-if="!paid">
      <h2>订单支付</h2>
      <div class="order-no">订单号：{{ orderNo }}</div>
      <div class="amount">¥<span>{{ amount }}</span></div>
      <div class="methods">
        <div :class="{active:method==='wechat'}" @click="method='wechat'">💚 微信支付</div>
        <div :class="{active:method==='alipay'}" @click="method='alipay'">💙 支付宝</div>
        <div :class="{active:method==='card'}" @click="method='card'">💳 银行卡</div>
      </div>
      <button class="btn-pay" :disabled="paying" @click="handlePay">{{ paying?'处理中...':'确认支付 ¥'+amount }}</button>
      <div class="tip">（模拟支付，点击即完成）</div>
    </div>
    <div class="pay-card success" v-else>
      <div class="icon">✅</div>
      <h2>支付成功</h2>
      <p class="amount">¥{{ amount }}</p>
      <p class="msg">感谢您的购买！</p>
      <div class="btns"><button @click="$router.push('/user/orders')">查看订单</button><button @click="$router.push('/')">继续购物</button></div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { createPayment, mockPay } from '../../api/payment'
import { ElMessage } from 'element-plus'

const paid = ref(false)
const paying = ref(false)
const method = ref('wechat')
const amount = ref('0.00')
const orderNo = ref('')

onMounted(() => {
  orderNo.value = sessionStorage.getItem('pay_order_no') || ''
  amount.value = sessionStorage.getItem('pay_total') || '0.00'
})

async function handlePay() {
  if (!orderNo.value) return
  paying.value = true
  try {
    const res = await createPayment({ order_no: orderNo.value, pay_method: method.value })
    const payNo = (res.data||res).pay_no
    await mockPay(payNo)
    paid.value = true
    ElMessage.success('支付成功')
  } catch {} finally { paying.value = false }
}
</script>

<style scoped>
.pay-page { display:flex; justify-content:center; padding:60px 16px; }
.pay-card { width:460px; background:#fff; border-radius:12px; padding:40px; text-align:center; box-shadow:0 4px 20px rgba(0,0,0,.06); }
.pay-card h2 { margin-bottom:8px; }
.order-no { font-size:12px; color:#999; margin-bottom:20px; }
.amount { color:#ff4400; margin-bottom:28px; }
.amount span { font-size:42px; font-weight:bold; }
.methods { display:flex; gap:10px; margin-bottom:24px; }
.methods div { flex:1; padding:14px; border:2px solid #f0f0f0; border-radius:8px; cursor:pointer; font-size:14px; }
.methods div:hover { border-color:#ddd; }
.methods div.active { border-color:#ff4400; background:#fff8f5; }
.btn-pay { width:100%; height:48px; background:#ff4400; color:#fff; border:none; border-radius:24px; font-size:16px; font-weight:bold; cursor:pointer; }
.btn-pay:disabled { opacity:.6; }
.tip { margin-top:12px; font-size:12px; color:#ccc; }
.success { padding:60px 40px; }
.icon { font-size:64px; margin-bottom:16px; }
.success h2 { color:#52c41a; margin-bottom:8px; }
.msg { color:#999; margin-bottom:28px; }
.btns { display:flex; gap:12px; justify-content:center; }
.btns button { padding:10px 28px; border-radius:22px; font-size:14px; cursor:pointer; }
.btns button:first-child { background:#ff4400; color:#fff; border:none; }
.btns button:last-child { background:#fff; color:#666; border:1px solid #ddd; }
</style>
