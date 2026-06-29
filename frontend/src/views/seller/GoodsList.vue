<template>
  <div class="seller-goods">
    <div class="page-top"><h2>商品管理</h2><button class="btn-add" @click="$router.push('/seller/goods/add')">+ 新增商品</button></div>
    <div class="filter"><input v-model="keyword" placeholder="搜索商品" @keyup.enter="load" /><select v-model="statusFilter" @change="load"><option :value="null">全部状态</option><option :value="true">在售</option><option :value="false">下架</option></select></div>
    <table class="goods-table" v-loading="loading">
      <thead><tr><th>商品</th><th>价格</th><th>销量</th><th>状态</th><th>时间</th><th>操作</th></tr></thead>
      <tbody><tr v-for="g in goodsList" :key="g.id">
        <td class="goods-cell"><img :src="g.main_image||'https://via.placeholder.com/50'" /><div><div class="g-name">{{ g.name }}</div><div class="g-sub">{{ g.subtitle }}</div></div></td>
        <td>{{ g.price_range }}</td><td>{{ g.sales }}</td>
        <td><span class="tag" :class="g.is_on_sale?'on':'off'">{{ g.is_on_sale?'在售':'下架' }}</span></td>
        <td class="time">{{ fmtDate(g.created_at) }}</td>
        <td class="acts"><span @click="$router.push(`/seller/goods/edit/${g.id}`)">编辑</span><span @click="toggleSale(g)">{{ g.is_on_sale?'下架':'上架' }}</span><span class="del" @click="handleDel(g)">删除</span></td>
      </tr></tbody>
    </table>
    <div v-if="!loading&&!goodsList.length" class="empty">暂无商品</div>
    <Pagination :total="total" :current-page="page" @page-change="p=>{page=p;load()}" />
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import { useUserStore } from '../../store/user'
import { getGoodsList } from '../../api/goods'
import { toggleGoodsSale, deleteGoods } from '../../api/seller'
import { extractPage } from '../../utils/response'
import Pagination from '../../components/common/Pagination.vue'
import { ElMessage, ElMessageBox } from 'element-plus'
const userStore = useUserStore()
const loading = ref(false)
const goodsList = ref([])
const total = ref(0)
const page = ref(Number(sessionStorage.getItem('seller_goods_page')) || 1)
const keyword = ref('')
const statusFilter = ref(null)
const fmtDate = d => d ? new Date(d).toLocaleDateString('zh-CN') : '-'
async function load() {
  loading.value = true
  sessionStorage.setItem('seller_goods_page', page.value)
  try {
    const params = { page:page.value, seller:'me' }
    if (keyword.value) params.search = keyword.value
    if (statusFilter.value !== null) params.is_on_sale = statusFilter.value
    const p = extractPage(await getGoodsList(params))
    goodsList.value = p.list
    total.value = p.total
  } catch {} finally { loading.value = false }
}
async function toggleSale(g) { try { const r = await toggleGoodsSale(g.id); g.is_on_sale = (r.data||r).is_on_sale; ElMessage.success(r.message) } catch {} }
async function handleDel(g) { await ElMessageBox.confirm(`删除「${g.name}」？`,'提示',{type:'warning'}); try { await deleteGoods(g.id); ElMessage.success('已删除'); load() } catch {} }
onMounted(load)
</script>
<style scoped>
.page-top { display:flex; justify-content:space-between; align-items:center; margin-bottom:16px; }
.page-top h2 { font-size:18px; }
.btn-add { padding:8px 20px; background:#ff4400; color:#fff; border:none; border-radius:4px; cursor:pointer; }
.filter { display:flex; gap:10px; margin-bottom:14px; }
.filter input { height:34px; border:1px solid #e8e8e8; border-radius:4px; padding:0 10px; width:220px; font-size:13px; }
.filter select { height:34px; border:1px solid #e8e8e8; border-radius:4px; padding:0 10px; font-size:13px; }
.goods-table { width:100%; background:#fff; border-radius:8px; border-collapse:collapse; }
.goods-table th { text-align:left; font-size:13px; color:#999; font-weight:normal; padding:12px 10px; border-bottom:1px solid #f0f0f0; }
.goods-table td { padding:14px 10px; border-bottom:1px solid #f5f5f5; font-size:13px; vertical-align:middle; }
.goods-cell { display:flex; align-items:center; gap:10px; }
.goods-cell img { width:50px; height:50px; object-fit:cover; border-radius:4px; }
.g-name { font-weight:bold; }
.g-sub { font-size:12px; color:#999; margin-top:2px; }
.time { color:#999; font-size:12px; }
.acts { display:flex; gap:10px; }
.acts span { color:#1890ff; cursor:pointer; font-size:13px; }
.acts span:hover { text-decoration:underline; }
.acts .del { color:#f56c6c; }
.tag { font-size:12px; padding:2px 8px; border-radius:3px; }
.tag.on { background:#e6f9ee; color:#52c41a; }
.tag.off { background:#f5f5f5; color:#999; }
.empty { text-align:center; padding:40px; color:#ccc; }
</style>
