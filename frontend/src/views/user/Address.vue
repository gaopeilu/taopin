<template>
  <div class="addr-page">
    <div class="page-top"><h3>收货地址</h3><button class="btn-add" @click="openForm()">+ 新增地址</button></div>
    <div v-loading="loading">
      <div v-for="addr in list" :key="addr.id" class="addr-card">
        <div class="addr-body">
          <div class="addr-name">{{ addr.receiver_name }} <span class="addr-phone">{{ addr.receiver_phone }}</span>
            <span class="addr-tag" v-if="addr.is_default">默认</span>
          </div>
          <div class="addr-text">{{ addr.province }}{{ addr.city }}{{ addr.district }} {{ addr.detail_address }}</div>
        </div>
        <div class="addr-acts">
          <span @click="setDefault(addr)" v-if="!addr.is_default">设为默认</span>
          <span @click="openForm(addr)">编辑</span>
          <span class="del" @click="handleDel(addr)">删除</span>
        </div>
      </div>
      <div v-if="!loading&&!list.length" class="empty">暂无地址</div>
    </div>

    <!-- 弹窗表单 -->
    <div class="mask" v-if="dialogVisible" @click.self="dialogVisible=false">
      <div class="dialog">
        <div class="dialog-title">{{ editId ? '编辑地址' : '新增地址' }}</div>
        <div class="form-row"><label>收货人 <em>*</em></label><input v-model="form.receiver_name" placeholder="收货人姓名" /><span class="err" v-if="errs.receiver_name">{{ errs.receiver_name }}</span></div>
        <div class="form-row"><label>手机号 <em>*</em></label><input v-model="form.receiver_phone" placeholder="11位手机号" maxlength="11" /><span class="err" v-if="errs.receiver_phone">{{ errs.receiver_phone }}</span></div>
        <div class="form-row"><label>省份 <em>*</em></label><input v-model="form.province" placeholder="省份" /><span class="err" v-if="errs.province">{{ errs.province }}</span></div>
        <div class="form-row"><label>城市 <em>*</em></label><input v-model="form.city" placeholder="城市" /><span class="err" v-if="errs.city">{{ errs.city }}</span></div>
        <div class="form-row"><label>区/县</label><input v-model="form.district" placeholder="区/县" /></div>
        <div class="form-row"><label>详细地址 <em>*</em></label><input v-model="form.detail_address" placeholder="街道门牌号" /><span class="err" v-if="errs.detail_address">{{ errs.detail_address }}</span></div>
        <div class="form-row"><label></label><label class="switch"><input type="checkbox" v-model="form.is_default" /> 设为默认</label></div>
        <div class="dialog-btns"><button class="btn-cancel" @click="dialogVisible=false">取消</button><button class="btn-save" :disabled="saving" @click="handleSave">{{ saving?'保存中...':'保存' }}</button></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getAddressList, createAddress, updateAddress, deleteAddress, setDefaultAddress } from '../../api/user'
import { extractList } from '../../utils/response'
import { ElMessage, ElMessageBox } from 'element-plus'

const loading = ref(false)
const saving = ref(false)
const list = ref([])
const dialogVisible = ref(false)
const editId = ref(null)
const initForm = () => ({ receiver_name:'', receiver_phone:'', province:'', city:'', district:'', detail_address:'', is_default:false })
const form = ref(initForm())
const errs = ref({})

async function load() {
  loading.value = true
  try { list.value = extractList(await getAddressList()) } catch {} finally { loading.value = false }
}
function openForm(addr) {
  editId.value = addr ? addr.id : null
  form.value = addr ? { ...addr } : initForm()
  errs.value = {}
  dialogVisible.value = true
}
function validate() {
  const e = {}
  if (!form.value.receiver_name?.trim()) e.receiver_name = '请输入'
  if (!form.value.receiver_phone?.trim()) e.receiver_phone = '请输入'
  else if (!/^1[3-9]\d{9}$/.test(form.value.receiver_phone)) e.receiver_phone = '格式不正确'
  if (!form.value.province?.trim()) e.province = '请输入'
  if (!form.value.city?.trim()) e.city = '请输入'
  if (!form.value.detail_address?.trim()) e.detail_address = '请输入'
  errs.value = e
  return !Object.keys(e).length
}
async function handleSave() {
  if (!validate()) return
  saving.value = true
  try {
    if (editId.value) { await updateAddress(editId.value, form.value); ElMessage.success('修改成功') }
    else { await createAddress(form.value); ElMessage.success('添加成功') }
    dialogVisible.value = false; load()
  } catch {} finally { saving.value = false }
}
async function handleDel(addr) {
  await ElMessageBox.confirm('确定删除？','提示',{type:'warning'})
  try { await deleteAddress(addr.id); ElMessage.success('已删除'); load() } catch {}
}
async function setDefault(addr) {
  try { await setDefaultAddress(addr.id); ElMessage.success('已设为默认'); load() } catch {}
}
onMounted(load)
</script>

<style scoped>
.page-top { display:flex; justify-content:space-between; align-items:center; margin-bottom:16px; }
.page-top h3 { font-size:18px; }
.btn-add { padding:8px 20px; background:#ff4400; color:#fff; border:none; border-radius:4px; cursor:pointer; font-size:13px; }
.addr-card { display:flex; justify-content:space-between; align-items:center; background:#fff; border-radius:8px; padding:16px; margin-bottom:10px; }
.addr-name { font-weight:bold; margin-bottom:6px; }
.addr-phone { font-weight:normal; color:#666; margin-left:8px; }
.addr-tag { background:#ff4400; color:#fff; font-size:11px; padding:1px 6px; border-radius:3px; margin-left:8px; }
.addr-text { font-size:13px; color:#666; }
.addr-acts { display:flex; gap:12px; font-size:13px; }
.addr-acts span { color:#999; cursor:pointer; }
.addr-acts span:hover { color:#ff4400; }
.addr-acts .del:hover { color:#f56c6c; }
.empty { text-align:center; padding:40px; color:#ccc; background:#fff; border-radius:8px; }

.mask { position:fixed; top:0;left:0;right:0;bottom:0; background:rgba(0,0,0,.4); display:flex; align-items:center; justify-content:center; z-index:1000; }
.dialog { background:#fff; border-radius:12px; width:480px; padding:24px; }
.dialog-title { font-size:16px; font-weight:bold; margin-bottom:20px; }
.form-row { display:flex; align-items:center; margin-bottom:12px; position:relative; }
.form-row label { width:70px; font-size:13px; color:#666; flex-shrink:0; }
.form-row label em { color:#ff4400; font-style:normal; }
.form-row input { flex:1; height:36px; border:1px solid #e8e8e8; border-radius:4px; padding:0 10px; font-size:13px; }
.form-row input:focus { border-color:#ff4400; outline:none; }
.switch { display:flex; align-items:center; gap:6px; cursor:pointer; width:auto; }
.switch input { accent-color:#ff4400; }
.err { position:absolute; right:0; top:38px; font-size:11px; color:#f56c6c; }
.dialog-btns { display:flex; justify-content:flex-end; gap:10px; margin-top:20px; }
.dialog-btns button { padding:8px 24px; border-radius:4px; cursor:pointer; font-size:13px; }
.btn-cancel { background:#f5f5f5; border:1px solid #ddd; color:#666; }
.btn-save { background:#ff4400; border:none; color:#fff; }
.btn-save:disabled { opacity:.6; }
</style>
