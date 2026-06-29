<template>
  <div class="goods-list-page">
    <div class="search-tip" v-if="keyword">
      搜索 "<span class="kw">{{ keyword }}</span>" 的结果，共 {{ total }} 件商品
      <span class="clear" @click="keyword='';filters.search='';loadGoods()">清除</span>
    </div>

    <div class="list-main">
      <!-- 左侧分类 -->
      <aside class="cat-side">
        <div class="cat-side-title">商品分类</div>
        <div class="cat-scroll">
          <div v-for="cat in categories" :key="cat.id" class="cat-node">
            <div class="cat-p" :class="{active:filters.category===cat.id}" @click="selectCat(cat.id)">{{ cat.name }}</div>
            <div v-for="ch in cat.children" :key="ch.id" class="cat-c" :class="{active:filters.category===ch.id}" @click="selectCat(ch.id)">{{ ch.name }}</div>
          </div>
        </div>
      </aside>

      <!-- 右侧商品 -->
      <div class="list-main-content">
        <div class="sort-bar">
          <span :class="{active:filters.ordering===''}" @click="filters.ordering='';loadGoods()">综合</span>
          <span :class="{active:filters.ordering==='-sales'}" @click="filters.ordering='-sales';loadGoods()">销量</span>
          <span :class="{active:filters.ordering==='-created_at'}" @click="filters.ordering='-created_at';loadGoods()">新品</span>
          <span :class="{active:filters.ordering==='price'}" @click="filters.ordering='price';loadGoods()">价格↑</span>
          <span :class="{active:filters.ordering==='-price'}" @click="filters.ordering='-price';loadGoods()">价格↓</span>
          <span class="cur-cat" v-if="curCatName">当前：{{ curCatName }}</span>
        </div>
        <el-skeleton :loading="loading" animated>
          <template #template>
            <div class="goods-grid">
              <div v-for="i in 8" :key="i" class="skeleton-card">
                <el-skeleton-item variant="image" class="skeleton-img" />
                <div class="skeleton-info">
                  <el-skeleton-item variant="text" style="width: 80%" />
                  <el-skeleton-item variant="text" style="width: 60%" />
                  <el-skeleton-item variant="text" style="width: 40%" />
                </div>
              </div>
            </div>
          </template>
          <template #default>
            <div class="goods-grid">
              <GoodsCard v-for="item in goodsList" :key="item.id" :goods="item" />
            </div>
            <div v-if="!loading&&!goodsList.length" class="empty">😕 没有找到相关商品</div>
          </template>
        </el-skeleton>
        <Pagination :total="total" :current-page="page" @page-change="p=>{page=p;loadGoods()}" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed, watch } from 'vue'
import { useRoute } from 'vue-router'
import { getGoodsList, getCategoryTree } from '../../api/goods'
import { extractList, extractPage } from '../../utils/response'
import GoodsCard from '../../components/goods/GoodsCard.vue'
import Pagination from '../../components/common/Pagination.vue'

const route = useRoute()
const loading = ref(false)
const goodsList = ref([])
const categories = ref([])
const total = ref(0)
const page = ref(1)
const keyword = ref(route.query.q || '')
const filters = reactive({ category: Number(route.query.category)||null, ordering: '', search: keyword.value })

const curCatName = computed(() => {
  if (!filters.category) return ''
  for (const c of categories.value) {
    if (c.id === filters.category) return c.name
    for (const ch of (c.children||[])) { if (ch.id === filters.category) return ch.name }
  }
  return ''
})

function selectCat(id) { filters.category = filters.category===id ? null : id; page.value = 1; loadGoods() }

async function loadCategories() {
  try {
    const res = await getCategoryTree()
    if (Array.isArray(res)) { categories.value = res }
    else if (res && Array.isArray(res.data)) { categories.value = res.data }
    else { categories.value = [] }
  } catch (e) {
    console.error('分类加载失败:', e)
    categories.value = []
  }
}

async function loadGoods() {
  loading.value = true
  try {
    const params = { page: page.value }
    if (filters.category) params.category = filters.category
    if (filters.ordering) params.ordering = filters.ordering
    if (filters.search) params.search = filters.search
    const res = await getGoodsList(params)
    const p = extractPage(res)
    goodsList.value = p.list
    total.value = p.total
  } catch {} finally { loading.value = false }
}

// 监听路由参数变化（从首页搜索跳转时）
watch(() => route.query, (q) => {
  keyword.value = q.q || ''
  filters.search = q.q || ''
  filters.category = Number(q.category) || null
  page.value = 1
  loadGoods()
}, { deep: true })

onMounted(() => { loadCategories(); loadGoods() })
</script>

<style scoped>
.goods-list-page { max-width:1200px; margin:0 auto; padding:16px; }
.search-tip { padding:12px 0; font-size:14px; color:#666; }
.search-tip .kw { color:#ff4400; font-weight:bold; }
.search-tip .clear { color:#999; cursor:pointer; margin-left:12px; font-size:12px; }
.search-tip .clear:hover { color:#ff4400; }

.list-main { display:flex; gap:16px; }
.cat-side { width:200px; background:#fff; border-radius:8px; flex-shrink:0; }
.cat-side-title { font-size:15px; font-weight:bold; padding:16px; border-bottom:1px solid #f0f0f0; }
.cat-scroll { max-height:600px; overflow-y:auto; padding:8px 16px 16px; }
.cat-node { margin-bottom:8px; }
.cat-p { font-size:13px; font-weight:bold; color:#333; padding:6px 8px; cursor:pointer; border-radius:4px; }
.cat-p:hover,.cat-p.active { background:#fff0e6; color:#ff4400; }
.cat-c { font-size:12px; color:#666; padding:4px 8px 4px 20px; cursor:pointer; border-radius:4px; }
.cat-c:hover,.cat-c.active { background:#fff0e6; color:#ff4400; }

.list-main-content { flex:1; min-width:0; }
.sort-bar { background:#fff; border-radius:8px; padding:12px 16px; margin-bottom:12px; display:flex; align-items:center; gap:16px; }
.sort-bar span { font-size:13px; color:#666; cursor:pointer; padding:4px 8px; border-radius:4px; }
.sort-bar span:hover,.sort-bar span.active { color:#ff4400; background:#fff0e6; }
.cur-cat { margin-left:auto; font-size:12px; color:#ff4400; background:#fff0e6; padding:4px 10px; border-radius:10px; }
.goods-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(200px,1fr)); gap:12px; min-height:200px; }
.empty { text-align:center; padding:60px; color:#ccc; }

/* 骨架屏样式 */
.skeleton-card { background:#fff; border-radius:8px; overflow:hidden; }
.skeleton-img { width:100%; padding-top:100%; }
.skeleton-info { padding:10px; display:flex; flex-direction:column; gap:8px; }
</style>
