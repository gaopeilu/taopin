<template>
  <div class="shop-settings"><h2>店铺设置</h2>
    <div class="form-body" v-loading="loading">
      <div class="form-row"><label>店铺名称</label><input v-model="form.shop_name" placeholder="请输入店铺名称" maxlength="100" /></div>
      <div class="form-row"><label>店铺简介</label><textarea v-model="form.shop_description" rows="4" placeholder="介绍你的店铺" maxlength="500"></textarea><div class="char-count">{{ (form.shop_description||'').length }}/500</div></div>
      <div class="form-row"><label>联系电话</label><input :value="form.contact_phone" disabled /><span class="tip">（来自个人手机号）</span></div>
      <div class="form-actions"><button class="btn-save" :disabled="saving" @click="handleSave">{{ saving?'保存中...':'保存设置' }}</button></div>
    </div>
  </div>
</template>
<script setup>
import { ref, reactive, onMounted } from 'vue'
import { getShopSettings, updateShopSettings } from '../../api/seller'
import { extractData } from '../../utils/response'
import { ElMessage } from 'element-plus'
const loading = ref(false)
const saving = ref(false)
const form = reactive({ shop_name:'', shop_description:'', contact_phone:'' })
onMounted(async () => { loading.value = true; try { Object.assign(form, extractData(await getShopSettings())) } catch {} finally { loading.value = false } })
async function handleSave() {
  if (!form.shop_name) { ElMessage.warning('请输入店铺名称'); return }
  saving.value = true
  try { await updateShopSettings({ shop_name:form.shop_name, shop_description:form.shop_description }); ElMessage.success('保存成功') } catch {} finally { saving.value = false }
}
</script>
<style scoped>
.shop-settings { background:#fff; border-radius:10px; padding:24px; }
h2 { font-size:18px; margin-bottom:20px; }
.form-body { max-width:500px; }
.form-row { margin-bottom:16px; }
.form-row label { display:block; font-size:13px; color:#666; margin-bottom:6px; }
.form-row input,.form-row textarea { width:100%; height:36px; border:1px solid #e8e8e8; border-radius:4px; padding:0 10px; font-size:13px; }
.form-row textarea { height:auto; padding:8px 10px; resize:vertical; }
.form-row input:focus,.form-row textarea:focus { border-color:#ff4400; outline:none; }
.form-row input:disabled { background:#f5f5f5; color:#999; }
.char-count { text-align:right; font-size:12px; color:#ccc; margin-top:4px; }
.tip { font-size:12px; color:#ccc; margin-top:4px; display:block; }
.form-actions { margin-top:24px; }
.btn-save { padding:12px 36px; background:#ff4400; color:#fff; border:none; border-radius:4px; cursor:pointer; font-size:14px; }
.btn-save:disabled { opacity:.6; }
</style>
