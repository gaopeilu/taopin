<template>
  <div class="checkout-page">
    <h2>确认订单</h2>
    <!-- 地址选择 -->
    <div class="section">
      <div class="sec-title">收货地址</div>
      <div class="addr-list" v-if="addresses.length">
        <div v-for="addr in addresses" :key="addr.id" class="addr-item" :class="{active:selAddr?.id===addr.id}" @click="selAddr=addr">
          <div><b>{{ addr.receiver_name }}</b> {{ addr.receiver_phone }} <span class="tag" v-if="addr.is_default">默认</span></div>
          <div class="addr-text">{{ addr.province }}{{ addr.city }}{{ addr.district }} {{ addr.detail_address }}</div>
        </div>
      </div>
      <div v-else class="no-addr"><p>暂无地址</p><button @click="$router.push('/')">去添加</button></div>
    </div>
    <!-- 优惠券选择 -->
    <div class="section" v-if="myCoupons.length">
      <div class="sec-title">优惠券</div>
      <div class="coupon-select">
        <div class="coupon-opt" :class="{active: !selCoupon}" @click="selCoupon=null">
          <span>不使用优惠券</span>
        </div>
        <div v-for="c in myCoupons" :key="c.id" class="coupon-opt" :class="{active: selCoupon?.id===c.id, disabled: parseFloat(total) < parseFloat(c.min_amount)}" @click="selectCoupon(c)">
          <div class="coupon-opt-left">
            <span v-if="c.coupon_type==='minus'" class="coupon-val">减¥{{ c.coupon_value }}</span>
            <span v-else-if="c.coupon_type==='discount'" class="coupon-val">{{ c.coupon_value }}折</span>
            <span v-else class="coupon-val">减¥{{ c.coupon_value }}</span>
          </div>
          <div class="coupon-opt-right">
            <div class="coupon-opt-name">{{ c.coupon_name }}</div>
            <div class="coupon-opt-cond">满{{ c.min_amount }}可用</div>
          </div>
          <span v-if="parseFloat(total) < parseFloat(c.min_amount)" class="coupon-not-enough">未满最低消费</span>
        </div>
      </div>
    </div>
    <!-- 商品清单 -->
    <div class="section">
      <div class="sec-title">商品清单</div>
      <div v-for="item in items" :key="item.skuId" class="goods-item">
        <img :src="item.image||'https://via.placeholder.com/60'" />
        <div class="gi-info"><div>{{ item.name }}</div><div class="gi-spec" v-if="item.specText">{{ item.specText }}</div></div>
        <div class="gi-price">¥{{ item.price }} x{{ item.quantity }}</div>
        <div class="gi-sub">¥{{ (item.price*item.quantity).toFixed(2) }}</div>
      </div>
    </div>
    <!-- 结算 -->
    <div class="pay-bar">
      <div class="pay-info">
        <span>共 {{ items.length }} 种商品</span>
        <span v-if="discount > 0" class="discount-info">优惠：<b class="discount-amount">-¥{{ discount.toFixed(2) }}</b></span>
        <span>实付：<b>¥{{ payTotal }}</b></span>
      </div>
      <button class="btn-pay" :disabled="!selAddr||!items.length||submitting" @click="submitOrder">{{ submitting?'提交中...':'提交订单' }}</button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getAddressList } from '../../api/user'
import { createOrder } from '../../api/order'
import { getMyCoupons } from '../../api/coupon'
import { extractList } from '../../utils/response'
import { useCartStore } from '../../store/cart'
import { ElMessage } from 'element-plus'

const router = useRouter()
const cartStore = useCartStore()
const addresses = ref([])
const selAddr = ref(null)
const items = ref([])
const submitting = ref(false)
const myCoupons = ref([])
const selCoupon = ref(null)
const total = computed(() => items.value.reduce((s,i)=>s+i.price*i.quantity,0).toFixed(2))

const discount = computed(() => {
  if (!selCoupon.value) return 0
  const c = selCoupon.value
  const t = parseFloat(total.value)
  if (t < parseFloat(c.min_amount)) return 0
  if (c.coupon_type === 'minus' || c.coupon_type === 'newcomer') return parseFloat(c.coupon_value)
  if (c.coupon_type === 'discount') return t * (1 - parseFloat(c.coupon_value) / 10)
  return 0
})

const payTotal = computed(() => Math.max(0, parseFloat(total.value) - discount.value).toFixed(2))

function selectCoupon(c) {
  if (parseFloat(total.value) < parseFloat(c.min_amount)) {
    ElMessage.warning(`未满最低消费 ¥${c.min_amount}`)
    return
  }
  selCoupon.value = selCoupon.value?.id === c.id ? null : c
}

onMounted(async () => {
  try {
    const res = await getAddressList()
    const list = extractList(res)
    addresses.value = list
    selAddr.value = list.find(a=>a.is_default) || list[0] || null
  } catch {}
  try { items.value = JSON.parse(sessionStorage.getItem('checkout_items')||'[]') } catch {}
  // 加载用户可用优惠券
  try {
    const couponRes = await getMyCoupons({ status: 'unused' })
    myCoupons.value = extractList(couponRes)
  } catch {}
})

async function submitOrder() {
  if (!selAddr.value) { ElMessage.warning('请选择地址'); return }
  submitting.value = true
  try {
    const addr = selAddr.value
    const payload = {
      receiver_name: addr.receiver_name, receiver_phone: addr.receiver_phone,
      receiver_address: `${addr.province}${addr.city}${addr.district} ${addr.detail_address}`,
      items: items.value.map(i=>({ sku_id:i.skuId, quantity:i.quantity, goods_name:i.name, goods_image:i.image||'' }))
    }
    if (selCoupon.value) payload.coupon_id = selCoupon.value.id
    const res = await createOrder(payload)
    const orderNo = (res.data||res).order_no
    items.value.forEach(i => { if(i.cartId) {
      cartStore.removeItem(i.skuId)
      import('../../api/cart').then(m => m.deleteCartItem(i.cartId)).catch(()=>{})
    }})
    sessionStorage.setItem('pay_order_no', orderNo)
    sessionStorage.setItem('pay_total', payTotal.value)
    router.push('/pay')
  } catch {} finally { submitting.value = false }
}
</script>

<style scoped>
.checkout-page { max-width:900px; margin:0 auto; padding:16px; }
h2 { font-size:20px; margin-bottom:16px; }
.section { background:#fff; border-radius:8px; padding:20px; margin-bottom:12px; }
.sec-title { font-size:15px; font-weight:bold; margin-bottom:14px; padding-bottom:10px; border-bottom:1px solid #f0f0f0; }
.addr-list { display:flex; flex-wrap:wrap; gap:10px; }
.addr-item { flex:1; min-width:250px; padding:12px; border:2px solid #f0f0f0; border-radius:6px; cursor:pointer; font-size:13px; }
.addr-item:hover { border-color:#ffcc99; }
.addr-item.active { border-color:#ff4400; background:#fff8f5; }
.tag { background:#ff4400; color:#fff; font-size:11px; padding:1px 6px; border-radius:3px; margin-left:6px; }
.addr-text { font-size:12px; color:#666; margin-top:4px; }
.no-addr { text-align:center; padding:24px; color:#999; }
.no-addr button { margin-top:10px; padding:8px 20px; background:#ff4400; color:#fff; border:none; border-radius:4px; cursor:pointer; }

.coupon-select { display:flex; flex-direction:column; gap:8px; }
.coupon-opt { display:flex; align-items:center; gap:12px; padding:12px; border:2px solid #f0f0f0; border-radius:6px; cursor:pointer; font-size:13px; transition:all .2s; }
.coupon-opt:hover { border-color:#ffcc99; }
.coupon-opt.active { border-color:#ff4400; background:#fff8f5; }
.coupon-opt.disabled { opacity:.5; cursor:not-allowed; }
.coupon-opt-left { flex-shrink:0; }
.coupon-val { font-size:18px; font-weight:bold; color:#ff4400; }
.coupon-opt-right { flex:1; }
.coupon-opt-name { font-size:14px; font-weight:bold; }
.coupon-opt-cond { font-size:12px; color:#999; margin-top:2px; }
.coupon-not-enough { font-size:11px; color:#999; flex-shrink:0; }

.goods-item { display:flex; align-items:center; gap:12px; padding:10px 0; border-bottom:1px solid #f5f5f5; }
.goods-item img { width:60px; height:60px; object-fit:cover; border-radius:4px; }
.gi-info { flex:1; font-size:13px; }
.gi-spec { font-size:12px; color:#999; }
.gi-price { color:#666; width:100px; }
.gi-sub { color:#ff4400; font-weight:bold; width:80px; text-align:right; }
.pay-bar { display:flex; justify-content:flex-end; align-items:center; gap:24px; background:#fff; border-radius:8px; padding:16px 24px; }
.pay-info { display:flex; align-items:center; gap:16px; font-size:14px; }
.pay-info b { color:#ff4400; font-size:24px; }
.discount-info { color:#666; }
.discount-amount { color:#52c41a; font-size:16px !important; }
.btn-pay { padding:14px 48px; background:#ff4400; color:#fff; border:none; border-radius:24px; font-size:16px; font-weight:bold; cursor:pointer; }
.btn-pay:disabled { opacity:.5; cursor:not-allowed; }
</style>
