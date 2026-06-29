<template>
  <div class="my-reviews"><h2>我的评价</h2>
    <div v-loading="loading">
      <div v-for="r in reviews" :key="r.id" class="review-card">
        <div class="review-top"><span class="stars">{{ '★'.repeat(r.rating) }}{{ '☆'.repeat(5-r.rating) }}</span><span class="time">{{ fmtDate(r.created_at) }}</span></div>
        <div class="content">{{ r.content || '用户未填写' }}</div>
        <div class="meta"><span>商品ID: {{ r.spu_id }}</span><span v-if="r.order_no">订单: {{ r.order_no }}</span><span v-if="r.is_anonymous" class="anon">匿名</span></div>
      </div>
      <div v-if="!loading&&!reviews.length" class="empty">暂无评价</div>
    </div>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import { getMyReviews } from '../../api/review'
import { extractList } from '../../utils/response'
const loading = ref(false)
const reviews = ref([])
const fmtDate = d => d ? new Date(d).toLocaleString('zh-CN') : '-'
onMounted(async () => { loading.value = true; try { reviews.value = extractList(await getMyReviews()) } catch {} finally { loading.value = false } })
</script>
<style scoped>
.my-reviews { max-width:800px; margin:0 auto; }
h2 { font-size:20px; margin-bottom:16px; }
.review-card { background:#fff; border-radius:8px; padding:16px; margin-bottom:10px; }
.review-top { display:flex; justify-content:space-between; margin-bottom:8px; }
.stars { color:#ff9900; font-size:14px; }
.time { color:#999; font-size:12px; }
.content { font-size:14px; color:#333; line-height:1.6; margin-bottom:8px; }
.meta { display:flex; gap:12px; font-size:12px; color:#999; }
.anon { background:#f5f5f5; padding:1px 6px; border-radius:3px; }
.empty { text-align:center; padding:60px; color:#ccc; background:#fff; border-radius:8px; }
</style>
