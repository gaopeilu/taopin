<template>
  <div class="cart-page">
    <h2>我的购物车</h2>
    <div v-if="!items.length" class="empty">
      <div class="empty-icon">🛒</div>
      <p>购物车空空如也</p>
      <button @click="$router.push('/')">去购物</button>
    </div>
    <div v-else>
      <table class="cart-table">
        <thead><tr><th><input type="checkbox" :checked="allSel" @change="toggleAll" /></th><th>商品</th><th>单价</th><th>数量</th><th>小计</th><th>操作</th></tr></thead>
        <tbody>
          <tr v-for="item in items" :key="item.id">
            <td><input type="checkbox" v-model="item.is_selected" @change="updateSel(item)" /></td>
            <td class="goods-cell">
              <img :src="item.goods_image||'https://via.placeholder.com/80'" />
              <div>
                <div class="g-name" @click="$router.push(`/goods/${item.spu_id}`)">{{ item.goods_name }}</div>
                <div class="g-spec" v-if="item.sku_name">{{ item.sku_name }}</div>
              </div>
            </td>
            <td>¥{{ item.price }}</td>
            <td><div class="qty"><button @click="changeQty(item,item.quantity-1)">-</button><span>{{ item.quantity }}</span><button @click="changeQty(item,item.quantity+1)">+</button></div></td>
            <td class="subtotal">¥{{ item.subtotal }}</td>
            <td><span class="del" @click="handleDel(item)">删除</span></td>
          </tr>
        </tbody>
      </table>
      <div class="cart-footer">
        <div><label><input type="checkbox" :checked="allSel" @change="toggleAll" /> 全选</label></div>
        <div class="footer-right">
          <span>已选 <b>{{ selCount }}</b> 件</span>
          <span>合计：<b class="total">¥{{ selTotal }}</b></span>
          <button class="btn-checkout" :disabled="!selCount" @click="goCheckout">去结算</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getCartList, updateCart, deleteCartItem, selectAllCart } from '../../api/cart'
import { extractList } from '../../utils/response'
import { ElMessage, ElMessageBox } from 'element-plus'

const router = useRouter()
const items = ref([])
const allSel = computed(() => items.value.length>0 && items.value.every(i=>i.is_selected))
const selItems = computed(() => items.value.filter(i=>i.is_selected))
const selCount = computed(() => selItems.value.reduce((s,i)=>s+i.quantity,0))
const selTotal = computed(() => selItems.value.reduce((s,i)=>s+parseFloat(i.subtotal||0),0).toFixed(2))

async function load() {
  try { items.value = extractList(await getCartList()) } catch {}
}
async function changeQty(item, q) {
  if (q<1) return
  try { await updateCart(item.id,{quantity:q}); item.quantity=q; item.subtotal=(parseFloat(item.price)*q).toFixed(2) } catch {}
}
async function updateSel(item) {
  try { await updateCart(item.id,{is_selected:item.is_selected}) } catch {}
}
async function toggleAll() {
  const v = !allSel.value
  try { await selectAllCart(v); items.value.forEach(i=>i.is_selected=v) } catch {}
}
async function handleDel(item) {
  await ElMessageBox.confirm('确定删除？','提示',{type:'warning'})
  try { await deleteCartItem(item.id); items.value=items.value.filter(i=>i.id!==item.id); ElMessage.success('已删除') } catch {}
}
function goCheckout() {
  if (!selItems.value.length) return
  sessionStorage.setItem('checkout_items', JSON.stringify(selItems.value.map(i=>({
    skuId:i.sku_id, spuId:i.spu_id, name:i.goods_name, price:parseFloat(i.price),
    image:i.goods_image, specText:i.sku_name, quantity:i.quantity, cartId:i.id
  }))))
  router.push('/checkout')
}
onMounted(load)
</script>

<style scoped>
.cart-page { max-width:1200px; margin:0 auto; padding:16px; }
h2 { font-size:20px; margin-bottom:16px; }
.empty { text-align:center; padding:80px 0; background:#fff; border-radius:8px; }
.empty-icon { font-size:64px; margin-bottom:16px; }
.empty p { color:#999; margin-bottom:20px; }
.empty button { padding:10px 32px; background:#ff4400; color:#fff; border:none; border-radius:22px; cursor:pointer; }
.cart-table { width:100%; background:#fff; border-radius:8px; border-collapse:collapse; }
.cart-table th { background:#f5f5f5; padding:12px; font-size:13px; color:#666; font-weight:normal; text-align:left; }
.cart-table td { padding:16px 12px; border-bottom:1px solid #f0f0f0; vertical-align:middle; }
.goods-cell { display:flex; align-items:center; gap:12px; }
.goods-cell img { width:80px; height:80px; object-fit:cover; border-radius:4px; }
.g-name { cursor:pointer; font-size:13px; }
.g-name:hover { color:#ff4400; }
.g-spec { font-size:12px; color:#999; margin-top:4px; }
.qty { display:inline-flex; border:1px solid #e8e8e8; border-radius:4px; }
.qty button { width:28px; height:28px; border:none; background:#f5f5f5; cursor:pointer; font-size:14px; }
.qty span { width:36px; text-align:center; line-height:28px; font-size:13px; }
.subtotal { color:#ff4400; font-weight:bold; }
.del { color:#999; cursor:pointer; font-size:13px; }
.del:hover { color:#ff4400; }
.cart-footer { display:flex; justify-content:space-between; align-items:center; padding:16px 20px; background:#f5f5f5; border-radius:0 0 8px 8px; position:sticky; bottom:0; }
.footer-right { display:flex; align-items:center; gap:20px; }
.footer-right b { color:#ff4400; }
.total { font-size:22px; }
.btn-checkout { padding:12px 40px; background:#ff4400; color:#fff; border:none; border-radius:22px; font-size:16px; font-weight:bold; cursor:pointer; }
.btn-checkout:disabled { opacity:.5; cursor:not-allowed; }
</style>
