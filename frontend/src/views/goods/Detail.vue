<template>
  <div class="detail-page" v-loading="loading">
    <template v-if="goods">
      <div class="crumbs">
        <span @click="$router.push('/')">首页</span> &gt;
        <span @click="$router.push({path:'/goods',query:{category:goods.category?.id}})">{{ goods.category?.name }}</span> &gt;
        <span class="cur">{{ goods.name }}</span>
      </div>

      <div class="detail-main">
        <!-- 图片区 -->
        <div class="img-sec">
          <div class="main-img"><img :src="curImg || goods.main_image" /></div>
          <div class="thumbs">
            <img v-for="(img,i) in allImgs" :key="i" :src="img.image_url||img"
              :class="{active:curImg===(img.image_url||img)}" @click="curImg=img.image_url||img" />
          </div>
        </div>

        <!-- 信息区 -->
        <div class="info-sec">
          <h1>{{ goods.name }}</h1>
          <p class="subtitle" v-if="goods.subtitle">{{ goods.subtitle }}</p>

          <div class="price-box">
            <div class="price-row">
              <span class="label">售价</span>
              <span class="price" v-if="selSku">¥{{ selSku.price }}</span>
              <span class="price" v-else>{{ goods.price_range }}</span>
              <span class="old-price" v-if="selSku?.original_price">¥{{ selSku.original_price }}</span>
              <span class="discount" v-if="selSku?.original_price&&selSku.price<selSku.original_price">{{ (selSku.price/selSku.original_price*10).toFixed(1) }}折</span>
            </div>
            <div class="meta">
              <span>销量 {{ fmtSales(goods.sales) }}</span>
              <span v-if="goods.brand">品牌：{{ goods.brand.name }}</span>
              <span>分类：{{ goods.category?.name }}</span>
            </div>
          </div>

          <!-- 规格 -->
          <div class="spec-sec" v-if="goods.skus?.length">
            <div class="spec-row">
              <span class="spec-label">规格</span>
              <div class="spec-btns">
                <button v-for="sku in goods.skus" :key="sku.id"
                  :class="{active:selSku?.id===sku.id, disabled:!sku.is_active||!sku.is_in_stock}"
                  @click="sku.is_active&&sku.is_in_stock&&(selSku=sku)">
                  {{ sku.name }} <em v-if="!sku.is_in_stock">(缺货)</em>
                </button>
              </div>
            </div>
            <div class="spec-detail" v-if="selSku?.specs">
              <span v-for="(v,k) in selSku.specs" :key="k" class="spec-tag">{{ k }}: {{ v }}</span>
            </div>
            <div class="stock" v-if="selSku">
              库存 <b>{{ selSku.stock }}</b> 件
              <span class="stock-warn" v-if="selSku.stock<=10">库存紧张</span>
            </div>
          </div>

          <!-- 数量 -->
          <div class="qty-sec">
            <span class="spec-label">数量</span>
            <div class="qty-box">
              <button @click="qty=Math.max(1,qty-1)">-</button>
              <span>{{ qty }}</span>
              <button @click="qty=Math.min(selSku?.stock||99,qty+1)">+</button>
            </div>
          </div>

          <!-- 按钮 -->
          <div class="actions">
            <button class="btn-buy" @click="buyNow" :disabled="selSku&&!selSku.is_in_stock">立即购买</button>
            <button class="btn-cart" @click="addCart" :disabled="selSku&&!selSku.is_in_stock">加入购物车</button>
          </div>
        </div>
      </div>

      <!-- 详情/评价 -->
      <div class="bottom-sec">
        <div class="tabs">
          <span :class="{active:tab==='desc'}" @click="tab='desc'">商品详情</span>
          <span :class="{active:tab==='review'}" @click="tab='review'">商品评价({{ reviews.length }})</span>
        </div>
        <div v-show="tab==='desc'" class="desc" v-html="sanitizeHtml(goods.description||'暂无详情')"></div>
        <div v-show="tab==='review'">
          <div v-for="r in reviews" :key="r.id" class="review">
            <div class="review-top">
              <span class="review-user">{{ r.user }}</span>
              <span class="review-stars">{{ '★'.repeat(r.rating) }}{{ '☆'.repeat(5-r.rating) }}</span>
              <span class="review-time">{{ r.time }}</span>
            </div>
            <div class="review-text">{{ r.text }}</div>
          </div>
          <div v-if="!reviews.length" class="no-review">暂无评价</div>
          <!-- 评价表单 -->
          <div class="review-form" v-if="userStore.loggedIn">
            <h4>发表评价</h4>
            <div class="rf-row"><label>评分</label><span class="stars"><span v-for="i in 5" :key="i" :class="{on:i<=rf.rating}" @click="rf.rating=i">★</span></span></div>
            <div class="rf-row"><label>内容</label><textarea v-model="rf.content" placeholder="分享使用体验..." rows="3"></textarea></div>
            <div class="rf-row"><label></label><label class="anon"><input type="checkbox" v-model="rf.is_anonymous" /> 匿名</label></div>
            <div class="rf-row"><label></label><button class="btn-submit" :disabled="rfing" @click="submitReview">{{ rfing?'提交中...':'提交评价' }}</button></div>
          </div>
        </div>
      </div>

      <!-- 同类推荐 -->
      <div class="recommend" v-if="related.length">
        <h3>看了又看</h3>
        <div class="rec-grid"><GoodsCard v-for="item in related" :key="item.id" :goods="item" /></div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getGoodsDetail, getGoodsList } from '../../api/goods'
import { getReviews, createReview } from '../../api/review'
import { addToCart as apiAddCart } from '../../api/cart'
import { useUserStore } from '../../store/user'
import { useCartStore } from '../../store/cart'
import { extractData, extractList, extractPage } from '../../utils/response'

// XSS防护：过滤HTML中的危险标签和属性
function sanitizeHtml(html) {
  if (!html) return ''
  return html
    .replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '')
    .replace(/<iframe\b[^<]*(?:(?!<\/iframe>)<[^<]*)*<\/iframe>/gi, '')
    .replace(/\bon\w+\s*=/gi, 'data-blocked=')  // 移除所有on*事件属性
    .replace(/javascript:/gi, 'blocked:')
}
import GoodsCard from '../../components/goods/GoodsCard.vue'
import { ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const cartStore = useCartStore()
const loading = ref(false)
const goods = ref(null)
const selSku = ref(null)
const qty = ref(1)
const curImg = ref('')
const tab = ref('desc')
const related = ref([])
const reviews = ref([])
const rf = ref({ rating:5, content:'', is_anonymous:false })
const rfing = ref(false)

const allImgs = ref([])
watch(goods, g => {
  if (!g) return
  const imgs = (g.images||[]).slice()
  if (g.main_image && !imgs.find(i=>i.image_url===g.main_image)) imgs.unshift({image_url:g.main_image})
  allImgs.value = imgs
  curImg.value = g.main_image || ''
}, { immediate: true })

function fmtSales(n) { if (!n) return '0'; if (n>=10000) return (n/10000).toFixed(1)+'万'; if (n>=1000) return (n/1000).toFixed(1)+'k'; return n+'' }

async function loadGoods() {
  loading.value = true
  try {
    const res = await getGoodsDetail(route.params.id)
    goods.value = extractData(res)
    const def = goods.value.skus?.find(s=>s.is_default&&s.is_in_stock&&s.is_active) || goods.value.skus?.find(s=>s.is_in_stock&&s.is_active)
    if (def) selSku.value = def
    if (goods.value.category?.id) {
      const r = await getGoodsList({ category: goods.value.category.id, page: 1 })
      related.value = extractPage(r).list.filter(g=>g.id!==goods.value.id).slice(0,5)
    }
    try {
      const revRes = await getReviews({ spu_id: route.params.id })
      reviews.value = extractList(revRes).map(r=>({
        id:r.id, user:r.is_anonymous?(r.username||'').slice(0,3)+'***':(r.username||'匿名'),
        rating:r.rating, text:r.content||'用户未填写', time:r.created_at?new Date(r.created_at).toLocaleDateString('zh-CN'):''
      }))
    } catch { reviews.value = [] }
  } catch {} finally { loading.value = false }
}

async function addCart() {
  if (!userStore.loggedIn) { router.push('/login'); return }
  if (goods.value.skus?.length && !selSku.value) { ElMessage.warning('请先选择规格'); return }
  const skuId = selSku.value?.id || goods.value.skus?.[0]?.id
  if (!skuId) return
  try {
    await apiAddCart({ sku_id:skuId, quantity:qty.value })
    // 同步更新本地购物车store
    cartStore.addItem({
      skuId,
      spuId: goods.value.id,
      name: goods.value.name + (selSku.value ? ` (${selSku.value.name})` : ''),
      price: selSku.value?.price || goods.value.skus?.[0]?.price || 0,
      image: selSku.value?.image || goods.value.main_image,
      specText: selSku.value?.name || '',
      quantity: qty.value
    })
    ElMessage.success('已加入购物车')
  } catch {}
}

function buyNow() {
  if (!userStore.loggedIn) { router.push('/login'); return }
  if (goods.value.skus?.length && !selSku.value) { ElMessage.warning('请先选择规格'); return }
  const skuId = selSku.value?.id || goods.value.skus?.[0]?.id
  if (!skuId) return
  sessionStorage.setItem('checkout_items', JSON.stringify([{
    skuId, spuId:goods.value.id, name:goods.value.name+(selSku.value?` (${selSku.value.name})`:''),
    price:selSku.value?.price||0, image:selSku.value?.image||goods.value.main_image,
    specText:selSku.value?.name||'', quantity:qty.value
  }]))
  router.push('/checkout')
}

async function submitReview() {
  if (!rf.value.content) { ElMessage.warning('请输入评价内容'); return }
  // [Bug22] 校验sku_id有效性
  const skuId = selSku.value?.id || goods.value.skus?.[0]?.id
  if (!skuId) { ElMessage.warning('无法获取商品规格信息'); return }
  rfing.value = true
  try {
    await createReview({ spu_id:goods.value.id, sku_id:skuId, rating:rf.value.rating, content:rf.value.content, is_anonymous:rf.value.is_anonymous })
    ElMessage.success('评价成功')
    rf.value = { rating:5, content:'', is_anonymous:false }
    const revRes = await getReviews({ spu_id:route.params.id })
    reviews.value = extractList(revRes).map(r=>({ id:r.id, user:r.is_anonymous?(r.username||'').slice(0,3)+'***':(r.username||'匿名'), rating:r.rating, text:r.content||'', time:r.created_at?new Date(r.created_at).toLocaleDateString('zh-CN'):'' }))
  } catch {} finally { rfing.value = false }
}

watch(()=>route.params.id, ()=>{ if(route.params.id) loadGoods() })
onMounted(loadGoods)
</script>

<style scoped>
.detail-page { max-width:1200px; margin:0 auto; padding:16px; }
.crumbs { font-size:12px; color:#999; padding:8px 0 16px; }
.crumbs span { cursor:pointer; }
.crumbs span:hover { color:#ff4400; }
.crumbs .cur { color:#666; }

.detail-main { display:flex; gap:24px; background:#fff; border-radius:8px; padding:24px; }
.img-sec { width:400px; flex-shrink:0; }
.main-img { width:400px; height:400px; border-radius:8px; overflow:hidden; border:1px solid #f0f0f0; }
.main-img img { width:100%; height:100%; object-fit:cover; }
.thumbs { display:flex; gap:8px; margin-top:10px; }
.thumbs img { width:60px; height:60px; object-fit:cover; border-radius:4px; cursor:pointer; border:2px solid transparent; opacity:.7; }
.thumbs img:hover,.thumbs img.active { border-color:#ff4400; opacity:1; }

.info-sec { flex:1; }
.info-sec h1 { font-size:20px; font-weight:bold; color:#333; line-height:1.4; }
.subtitle { font-size:13px; color:#999; margin-top:6px; }
.price-box { background:#fdf6f0; border-radius:8px; padding:16px; margin-top:16px; }
.price-row { display:flex; align-items:baseline; gap:8px; }
.label { color:#999; font-size:13px; }
.price { font-size:28px; color:#ff4400; font-weight:bold; }
.old-price { font-size:14px; color:#bbb; text-decoration:line-through; }
.discount { background:#ff4400; color:#fff; font-size:11px; padding:2px 6px; border-radius:3px; }
.meta { display:flex; gap:20px; margin-top:10px; font-size:12px; color:#999; }

.spec-sec { margin-top:20px; }
.spec-row { display:flex; align-items:flex-start; gap:12px; margin-bottom:12px; }
.spec-label { width:42px; color:#999; font-size:13px; line-height:32px; flex-shrink:0; }
.spec-btns { display:flex; flex-wrap:wrap; gap:8px; }
.spec-btns button { padding:6px 16px; border:1px solid #e8e8e8; border-radius:4px; background:#fff; cursor:pointer; font-size:13px; color:#333; }
.spec-btns button:hover { border-color:#ff4400; color:#ff4400; }
.spec-btns button.active { border-color:#ff4400; color:#ff4400; background:#fff5f0; }
.spec-btns button.disabled { color:#ccc; border-color:#f0f0f0; cursor:not-allowed; }
.spec-detail { display:flex; flex-wrap:wrap; gap:8px; margin:12px 0; padding:12px; background:#fafafa; border-radius:6px; }
.spec-tag { font-size:12px; background:#f5f5f5; padding:3px 8px; border-radius:3px; color:#666; }
.stock { font-size:13px; color:#666; margin-top:8px; }
.stock b { color:#ff4400; }
.stock-warn { color:#ff4400; font-size:12px; margin-left:8px; background:#fff0e6; padding:1px 6px; border-radius:3px; }

.qty-sec { display:flex; align-items:center; gap:12px; margin-top:16px; }
.qty-box { display:inline-flex; border:1px solid #e8e8e8; border-radius:4px; }
.qty-box button { width:32px; height:32px; border:none; background:#f5f5f5; cursor:pointer; font-size:16px; }
.qty-box span { width:48px; text-align:center; line-height:32px; font-size:14px; }

.actions { display:flex; gap:12px; margin-top:24px; }
.btn-buy { width:180px; height:48px; background:#ff4400; color:#fff; border:none; border-radius:24px; font-size:16px; font-weight:bold; cursor:pointer; }
.btn-buy:hover { background:#e63e00; }
.btn-buy:disabled { background:#ccc; cursor:not-allowed; }
.btn-cart { width:180px; height:48px; background:#fff; color:#ff4400; border:2px solid #ff4400; border-radius:24px; font-size:16px; font-weight:bold; cursor:pointer; }
.btn-cart:hover { background:#fff5f0; }
.btn-cart:disabled { color:#ccc; border-color:#ccc; cursor:not-allowed; }

.bottom-sec { background:#fff; border-radius:8px; margin-top:16px; padding:24px; }
.tabs { display:flex; border-bottom:1px solid #f0f0f0; margin-bottom:20px; }
.tabs span { padding:10px 24px; cursor:pointer; font-size:15px; color:#666; border-bottom:2px solid transparent; }
.tabs span.active { color:#ff4400; border-bottom-color:#ff4400; font-weight:bold; }
.desc { line-height:1.8; color:#333; }
.review { padding:16px 0; border-bottom:1px solid #f5f5f5; }
.review-top { display:flex; align-items:center; gap:12px; margin-bottom:8px; }
.review-user { font-weight:bold; font-size:13px; }
.review-stars { color:#ff9900; font-size:13px; }
.review-time { color:#ccc; font-size:12px; margin-left:auto; }
.review-text { color:#333; font-size:13px; line-height:1.6; }
.no-review { text-align:center; padding:40px 0; color:#ccc; }

.review-form { margin-top:24px; padding:20px; background:#fafafa; border-radius:8px; }
.review-form h4 { margin-bottom:16px; font-size:15px; }
.rf-row { display:flex; align-items:flex-start; margin-bottom:12px; }
.rf-row label { width:70px; font-size:13px; color:#666; line-height:32px; flex-shrink:0; }
.rf-row textarea { flex:1; border:1px solid #e8e8e8; border-radius:4px; padding:8px 10px; font-size:13px; resize:vertical; }
.rf-row textarea:focus { border-color:#ff4400; outline:none; }
.stars span { font-size:22px; color:#ddd; cursor:pointer; }
.stars span.on { color:#ff9900; }
.anon { display:flex; align-items:center; gap:4px; cursor:pointer; width:auto; }
.anon input { accent-color:#ff4400; }
.btn-submit { padding:10px 28px; background:#ff4400; color:#fff; border:none; border-radius:4px; cursor:pointer; font-size:14px; }
.btn-submit:disabled { opacity:.6; }

.recommend { margin-top:24px; }
.recommend h3 { font-size:18px; margin-bottom:12px; }
.rec-grid { display:grid; grid-template-columns:repeat(5,1fr); gap:12px; }
</style>
