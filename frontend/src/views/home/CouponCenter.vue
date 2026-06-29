<template>
  <div class="coupon-center">
    <h2>🎫 优惠券中心</h2>
    <div class="coupon-list" v-loading="loading">
      <div v-for="c in coupons" :key="c.id" class="coupon-item" :class="{claimed: c.is_claimed}">
        <div class="coupon-left">
          <div class="coupon-value">
            <span v-if="c.coupon_type==='minus'">¥{{ c.value }}</span>
            <span v-else-if="c.coupon_type==='discount'">{{ c.value }}折</span>
            <span v-else>¥{{ c.value }}</span>
          </div>
          <div class="coupon-cond" v-if="c.min_amount != 0">满{{ c.min_amount }}可用</div>
          <div class="coupon-cond" v-else>无门槛</div>
        </div>
        <div class="coupon-center-info">
          <div class="coupon-name">{{ c.name }}</div>
          <div class="coupon-time">{{ fmtDate(c.start_time) }} - {{ fmtDate(c.end_time) }}</div>
          <div class="coupon-remain">剩余 {{ c.remaining }} 张</div>
        </div>
        <div class="coupon-right">
          <button
            class="claim-btn"
            :class="{disabled: c.is_claimed}"
            :disabled="c.is_claimed || claimingId===c.id"
            @click="handleClaim(c)"
          >
            {{ claimingId===c.id ? '领取中...' : (c.is_claimed ? '每个账号限领一次，已领取' : '立即领取') }}
          </button>
        </div>
      </div>
      <div v-if="!loading && coupons.length===0" class="empty">暂无可领取的优惠券</div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getCouponList, claimCoupon } from '../../api/coupon'
import { useUserStore } from '../../store/user'
import { ElMessage } from 'element-plus'

const router = useRouter()
const userStore = useUserStore()
const loading = ref(false)
const coupons = ref([])
const claimingId = ref(null)
const fmtDate = d => d ? new Date(d).toLocaleDateString('zh-CN') : '-'

async function loadCoupons() {
  loading.value = true
  try {
    const res = await getCouponList()
    coupons.value = res.data || res.results || []
  } catch {} finally { loading.value = false }
}

async function handleClaim(c) {
  if (!userStore.loggedIn) { router.push('/login'); return }
  claimingId.value = c.id
  try {
    await claimCoupon(c.id)
    ElMessage.success('领取成功')
    c.remaining--
    c.claimed_count++
    c.is_claimed = true
  } catch {} finally { claimingId.value = null }
}

onMounted(loadCoupons)
</script>

<style scoped>
.coupon-center { max-width: 800px; margin: 0 auto; padding: 20px; }
h2 { font-size: 20px; margin-bottom: 20px; }
.coupon-item { display: flex; align-items: center; background: #fff; border-radius: 8px; margin-bottom: 10px; overflow: hidden; transition: opacity .3s; }
.coupon-item.claimed { opacity: .7; }
.coupon-left { width: 130px; background: linear-gradient(135deg, #ff4400, #ff6633); color: #fff; text-align: center; padding: 20px 12px; flex-shrink: 0; }
.coupon-item.claimed .coupon-left { background: linear-gradient(135deg, #ccc, #999); }
.coupon-value { font-size: 28px; font-weight: bold; }
.coupon-cond { font-size: 11px; margin-top: 4px; }
.coupon-center-info { flex: 1; padding: 16px; }
.coupon-name { font-size: 15px; font-weight: bold; margin-bottom: 6px; }
.coupon-time { font-size: 12px; color: #999; }
.coupon-remain { font-size: 12px; color: #ff4400; margin-top: 4px; }
.coupon-right { padding: 16px; flex-shrink: 0; }
.claim-btn { padding: 8px 16px; background: #ff4400; color: #fff; border: none; border-radius: 20px; cursor: pointer; font-size: 12px; white-space: nowrap; transition: all .3s; }
.claim-btn:hover:not(:disabled) { background: #e63e00; }
.claim-btn.disabled,
.claim-btn:disabled { background: #ccc; color: #999; cursor: not-allowed; }
.empty { text-align: center; padding: 60px; color: #ccc; background: #fff; border-radius: 8px; }
</style>
