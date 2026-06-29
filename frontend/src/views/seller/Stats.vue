<template>
  <div class="stats-page"><h2>销量统计</h2>
    <div class="overview-row">
      <div class="ov-card"><div class="ov-num">{{ totalSales }}</div><div class="ov-label">全店总销量</div></div>
      <div class="ov-card"><div class="ov-num">{{ goodsList.length }}</div><div class="ov-label">在售商品</div></div>
      <div class="ov-card"><div class="ov-num">¥{{ totalRevenue }}</div><div class="ov-label">估算营收</div></div>
    </div>
    <div class="chart-section"><h3>单品销量排行</h3>
      <div class="bar-list"><div v-for="item in goodsList" :key="item.id" class="bar-row"><span class="bar-name" :title="item.name">{{ item.name }}</span><div class="bar-track"><div class="bar-fill" :style="{width:barWidth(item.sales)+'%'}"></div></div><span class="bar-val">{{ item.sales }}</span></div>
        <div v-if="!goodsList.length" class="empty">暂无数据</div>
      </div>
    </div>
    <div class="table-section"><h3>销量明细</h3>
      <table class="detail-table"><thead><tr><th>#</th><th>商品</th><th>价格</th><th>销量</th><th>状态</th></tr></thead>
        <tbody><tr v-for="(g,i) in goodsList" :key="g.id"><td>{{ i+1 }}</td><td>{{ g.name }}</td><td>{{ g.price_range }}</td><td class="sales-num">{{ g.sales }}</td><td><span class="tag" :class="g.is_on_sale?'on':'off'">{{ g.is_on_sale?'在售':'下架' }}</span></td></tr></tbody>
      </table>
    </div>
  </div>
</template>
<script setup>
import { ref, computed, onMounted } from 'vue'
import { getGoodsList } from '../../api/goods'
import { extractPage } from '../../utils/response'
const goodsList = ref([])
const maxSales = ref(1)
const totalSales = computed(() => goodsList.value.reduce((s,g)=>s+(g.sales||0),0))
const totalRevenue = computed(() => { let t=0; goodsList.value.forEach(g=>{ t+=(parseFloat(g.price_range?.replace(/[^0-9.]/g,''))||0)*(g.sales||0) }); return t.toFixed(2) })
function barWidth(s) { return maxSales.value>0 ? Math.max((s/maxSales.value)*100,2) : 2 }
onMounted(async () => { try { const p = extractPage(await getGoodsList({ordering:'-sales',page:1})); goodsList.value = p.list; maxSales.value = Math.max(...goodsList.value.map(g=>g.sales||0),1) } catch {} })
</script>
<style scoped>
h2 { font-size:18px; margin-bottom:20px; }
.overview-row { display:grid; grid-template-columns:repeat(3,1fr); gap:12px; margin-bottom:24px; }
.ov-card { background:#fff; border-radius:10px; padding:24px; text-align:center; }
.ov-num { font-size:30px; font-weight:bold; color:#ff4400; }
.ov-label { font-size:13px; color:#999; margin-top:4px; }
.chart-section,.table-section { background:#fff; border-radius:10px; padding:20px; margin-bottom:16px; }
.chart-section h3,.table-section h3 { font-size:15px; margin-bottom:14px; }
.bar-row { display:flex; align-items:center; gap:10px; margin-bottom:8px; }
.bar-name { width:120px; font-size:13px; color:#666; text-align:right; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.bar-track { flex:1; height:20px; background:#f5f5f5; border-radius:10px; overflow:hidden; }
.bar-fill { height:100%; background:linear-gradient(90deg,#ff4400,#ff7733); border-radius:10px; min-width:2%; transition:width .5s; }
.bar-val { width:50px; font-weight:bold; font-size:13px; }
.detail-table { width:100%; border-collapse:collapse; }
.detail-table th { text-align:left; font-size:13px; color:#999; font-weight:normal; padding:10px 8px; border-bottom:1px solid #f0f0f0; }
.detail-table td { padding:12px 8px; border-bottom:1px solid #f5f5f5; font-size:13px; }
.sales-num { color:#ff4400; font-weight:bold; }
.tag { font-size:12px; padding:2px 8px; border-radius:3px; }
.tag.on { background:#e6f9ee; color:#52c41a; }
.tag.off { background:#f5f5f5; color:#999; }
.empty { text-align:center; padding:30px; color:#ccc; }
</style>
