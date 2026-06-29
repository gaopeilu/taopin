<template>
  <div class="goods-form">
    <h2>{{ isEdit ? '编辑商品' : '新增商品' }}</h2>
    <div class="form-body">
      <div class="form-row"><label>商品名称 <em>*</em></label><input v-model="form.name" placeholder="至少2个字符" /></div>
      <div class="form-row"><label>副标题</label><input v-model="form.subtitle" placeholder="一句话描述" /></div>
      <div class="form-row"><label>分类 <em>*</em></label><select v-model="form.category"><option :value="null">请选择</option><template v-for="cat in categoryTree" :key="cat.id"><option :value="cat.id">{{ cat.name }}</option><option v-for="ch in cat.children" :key="ch.id" :value="ch.id">&nbsp;&nbsp;└ {{ ch.name }}</option></template></select></div>
      <div class="form-row"><label>品牌</label><select v-model="form.brand"><option :value="null">可选</option><option v-for="b in brands" :key="b.id" :value="b.id">{{ b.name }}</option></select></div>
      <div class="form-row"><label>主图URL</label><input v-model="form.main_image" placeholder="图片URL" /></div>
      <div class="form-row" v-if="form.main_image"><label></label><img :src="getFullUrl(form.main_image)" style="max-width:200px;border-radius:6px" /></div>
      <div class="form-row"><label>描述</label><textarea v-model="form.description" rows="5" placeholder="支持HTML"></textarea></div>
      <div class="form-row"><label>上架</label><label class="switch"><input type="checkbox" v-model="form.is_on_sale" /> {{ form.is_on_sale?'立即上架':'暂不上架' }}</label></div>

      <template v-if="isEdit">
        <div class="divider">SKU 规格管理</div>
        <div v-for="(sku,i) in skuList" :key="sku.id||i" class="sku-row">
          <input v-model="sku.name" placeholder="规格名" /><input v-model="sku.price" placeholder="售价" /><input v-model="sku.original_price" placeholder="原价" /><input v-model.number="sku.stock" type="number" placeholder="库存" />
          <button class="sku-save" @click="saveSku(sku)">{{ sku.id?'更新':'添加' }}</button><button class="sku-del" @click="removeSku(sku,i)">×</button>
        </div>
        <button class="add-sku" @click="addSku">+ 添加SKU</button>

        <div class="divider">商品图片</div>
        <div class="img-list">
          <div v-for="img in imageList" :key="img.id" class="img-item">
            <img :src="getFullUrl(img.image_url)" />
            <span v-if="img.is_main" class="main-label">主图</span>
            <div class="img-actions">
              <button v-if="!img.is_main" class="btn-set-main" @click="handleSetMain(img)">设为主图</button>
              <button class="btn-delete-img" @click="handleDeleteImg(img)">删除</button>
            </div>
          </div>
        </div>
        <label class="upload-label">上传图片<input type="file" accept="image/*" @change="uploadImg" hidden /></label>
      </template>

      <div class="form-actions"><button class="btn-save" :disabled="saving" @click="handleSave">{{ saving?'保存中...':(isEdit?'保存修改':'创建商品') }}</button><button class="btn-back" @click="$router.back()">返回</button></div>
    </div>
  </div>
</template>
<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getCategoryTree, getBrands, getGoodsDetail, getGoodsSkus, getGoodsImages } from '../../api/goods'
import { createGoods, updateGoods, createSku, updateSku, deleteSku, uploadGoodsImage, deleteGoodsImage, setMainImage } from '../../api/seller'
import { extractData, extractList } from '../../utils/response'
import { ElMessage, ElMessageBox } from 'element-plus'
const route = useRoute()
const router = useRouter()
const isEdit = computed(() => !!route.params.id)
const saving = ref(false)
const categoryTree = ref([])
const brands = ref([])
const skuList = ref([])
const imageList = ref([])
const form = reactive({ name:'', subtitle:'', category:null, brand:null, main_image:'', description:'', is_on_sale:false })

// 处理图片URL
function getFullUrl(url) {
  if (!url) return 'https://via.placeholder.com/100'
  return url  // 相对路径直接用，Vite代理会转发到后端
}
onMounted(async () => {
  try {
    const [c,b] = await Promise.all([getCategoryTree(), getBrands()])
    categoryTree.value = Array.isArray(c) ? c : (c.data || [])
    brands.value = Array.isArray(b) ? b : (b.results || b.data || [])
  } catch {}
  if (isEdit.value) {
    try {
      const [d,s,i] = await Promise.all([getGoodsDetail(route.params.id), getGoodsSkus(route.params.id), getGoodsImages(route.params.id)])
      const g = extractData(d)
      Object.assign(form, { name:g.name, subtitle:g.subtitle, category:g.category?.id, brand:g.brand?.id, main_image:g.main_image, description:g.description, is_on_sale:g.is_on_sale })
      skuList.value = extractList(s); imageList.value = extractList(i)
    } catch {}
  }
})
async function handleSave() {
  if (!form.name||form.name.length<2) { ElMessage.warning('名称至少2字符'); return }
  if (!form.category) { ElMessage.warning('请选择分类'); return }
  saving.value = true
  try {
    if (isEdit.value) { await updateGoods(route.params.id, form); ElMessage.success('保存成功') }
    else { const r = await createGoods(form); ElMessage.success('创建成功'); router.replace(`/seller/goods/edit/${(r.data||r).id}`) }
  } catch {} finally { saving.value = false }
}
function addSku() { skuList.value.push({ name:'', price:'', original_price:'', stock:0, spu:route.params.id, specs:{} }) }
async function saveSku(sku) {
  try { if (sku.id) { await updateSku(sku.id, sku); ElMessage.success('已更新') } else { await createSku(sku); ElMessage.success('已添加'); skuList.value = extractList(await getGoodsSkus(route.params.id)) } } catch {}
}
async function removeSku(sku, i) { if (!sku.id) { skuList.value.splice(i,1); return }; await ElMessageBox.confirm('删除？','提示',{type:'warning'}); await deleteSku(sku.id); skuList.value.splice(i,1); ElMessage.success('已删除') }
async function uploadImg(e) {
  const file = e.target.files[0]
  if (!file) return
  const fd = new FormData()
  fd.append('image', file)
  fd.append('is_main', 'true')  // 默认设为主图
  try {
    const res = await uploadGoodsImage(route.params.id, fd)
    // 刷新图片列表
    imageList.value = extractList(await getGoodsImages(route.params.id))
    // 自动更新主图URL
    if (res.data && res.data.image_url) {
      form.main_image = res.data.image_url
    }
    ElMessage.success('上传成功')
  } catch {}
}
async function handleDeleteImg(img) {
  await ElMessageBox.confirm('确定删除这张图片？', '提示', { type: 'warning' })
  try {
    await deleteGoodsImage(img.id)
    imageList.value = imageList.value.filter(i => i.id !== img.id)
    ElMessage.success('已删除')
  } catch {}
}
async function handleSetMain(img) {
  try {
    await setMainImage(img.id)
    // 更新本地状态
    imageList.value.forEach(i => i.is_main = (i.id === img.id))
    form.main_image = img.image_url
    ElMessage.success('已设为主图')
  } catch {}
}
</script>
<style scoped>
.goods-form { background:#fff; border-radius:10px; padding:24px; }
.goods-form h2 { font-size:18px; margin-bottom:20px; }
.form-body { max-width:640px; }
.form-row { display:flex; align-items:flex-start; margin-bottom:14px; }
.form-row label { width:80px; font-size:13px; color:#666; line-height:36px; flex-shrink:0; }
.form-row label em { color:#ff4400; font-style:normal; }
.form-row input,.form-row select,.form-row textarea { flex:1; height:36px; border:1px solid #e8e8e8; border-radius:4px; padding:0 10px; font-size:13px; }
.form-row select { background:#fff; }
.form-row textarea { height:auto; padding:8px 10px; resize:vertical; }
.form-row input:focus,.form-row select:focus,.form-row textarea:focus { border-color:#ff4400; outline:none; }
.switch { display:flex; align-items:center; gap:6px; cursor:pointer; line-height:36px; width:auto; }
.switch input { accent-color:#ff4400; }
.divider { font-size:14px; font-weight:bold; margin:20px 0 12px; padding-bottom:8px; border-bottom:1px solid #f0f0f0; }
.sku-row { display:flex; gap:6px; margin-bottom:6px; }
.sku-row input { height:32px; border:1px solid #e8e8e8; border-radius:4px; padding:0 8px; font-size:12px; flex:1; }
.sku-save { padding:0 12px; background:#1890ff; color:#fff; border:none; border-radius:4px; cursor:pointer; font-size:12px; }
.sku-del { width:32px; background:#f56c6c; color:#fff; border:none; border-radius:4px; cursor:pointer; }
.add-sku { padding:6px 16px; background:#f5f5f5; border:1px dashed #ddd; border-radius:4px; cursor:pointer; font-size:13px; color:#666; }
.img-list { display:flex; flex-wrap:wrap; gap:10px; margin-bottom:10px; }
.img-item { position:relative; width:100px; height:100px; }
.img-item img { width:100%; height:100%; object-fit:cover; border-radius:6px; }
.main-label { position:absolute; top:4px; left:4px; background:#ff4400; color:#fff; font-size:11px; padding:1px 6px; border-radius:3px; }
.img-actions { position:absolute; bottom:0; left:0; right:0; display:flex; gap:2px; padding:2px; background:rgba(0,0,0,0.5); border-radius:0 0 6px 6px; opacity:0; transition:opacity 0.2s; }
.img-item:hover .img-actions { opacity:1; }
.btn-set-main, .btn-delete-img { flex:1; padding:3px 0; border:none; border-radius:3px; font-size:11px; cursor:pointer; color:#fff; }
.btn-set-main { background:#1890ff; }
.btn-delete-img { background:#ff4d4f; }
.upload-label { display:inline-block; padding:8px 16px; background:#f5f5f5; border:1px dashed #ddd; border-radius:4px; cursor:pointer; font-size:13px; color:#666; }
.form-actions { display:flex; gap:12px; margin-top:24px; }
.btn-save { padding:12px 36px; background:#ff4400; color:#fff; border:none; border-radius:4px; cursor:pointer; font-size:14px; }
.btn-save:disabled { opacity:.6; }
.btn-back { padding:12px 24px; background:#f5f5f5; border:1px solid #ddd; border-radius:4px; cursor:pointer; font-size:14px; color:#666; }
</style>
