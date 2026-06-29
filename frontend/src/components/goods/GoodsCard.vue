<template>
  <div class="goods-card" @click="$router.push(`/goods/${goods.id}`)">
    <div class="card-img-box">
      <img v-lazy="goods.main_image || defaultImg" :alt="goods.name" />
      <div class="card-tag" v-if="goods.brand_name">{{ goods.brand_name }}</div>
    </div>
    <div class="card-info">
      <div class="card-name">{{ goods.name }}</div>
      <div class="card-sub" v-if="goods.subtitle">{{ goods.subtitle }}</div>
      <div class="card-bottom">
        <span class="card-price">{{ goods.price_range || '暂无报价' }}</span>
        <span class="card-sales" v-if="goods.sales > 0">{{ goods.sales }}人付款</span>
      </div>
      <div class="card-shop" v-if="goods.seller_name">
        <span class="shop-icon">🏪</span>{{ goods.seller_name }}
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({ goods: { type: Object, required: true } })
const defaultImg = 'data:image/svg+xml,' + encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="220" height="220" viewBox="0 0 220 220"><rect fill="#f5f5f5" width="220" height="220"/><text fill="#ccc" font-family="Arial" font-size="14" x="50%" y="50%" text-anchor="middle" dy=".3em">暂无图片</text></svg>')
</script>

<style scoped>
.goods-card { background: #fff; border-radius: 8px; overflow: hidden; cursor: pointer; transition: all .2s; }
.goods-card:hover { box-shadow: 0 6px 20px rgba(0,0,0,.08); transform: translateY(-3px); }
.card-img-box { position: relative; width: 100%; padding-top: 100%; overflow: hidden; background: #f9f9f9; }
.card-img-box img { position: absolute; top: 0; left: 0; width: 100%; height: 100%; object-fit: cover; transition: transform .3s; }
.goods-card:hover .card-img-box img { transform: scale(1.05); }
.card-tag { position: absolute; top: 8px; left: 0; background: rgba(255,68,0,.85); color: #fff; font-size: 11px; padding: 2px 8px 2px 6px; border-radius: 0 10px 10px 0; }
.card-info { padding: 10px 10px 12px; }
.card-name { font-size: 13px; color: #333; line-height: 1.4; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.card-sub { font-size: 11px; color: #999; margin-top: 2px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.card-bottom { display: flex; justify-content: space-between; align-items: baseline; margin-top: 8px; }
.card-price { color: #ff4400; font-size: 17px; font-weight: bold; }
.card-sales { font-size: 11px; color: #999; }
.card-shop { font-size: 11px; color: #999; margin-top: 4px; }
.shop-icon { margin-right: 2px; }
</style>
