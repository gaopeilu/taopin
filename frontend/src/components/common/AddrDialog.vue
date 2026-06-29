<template>
  <!-- 收货地址弹窗组件 -->
  <div class="addr-mask" v-if="visible" @click.self="close">
    <div class="addr-dialog">
      <div class="addr-header">
        <span>收货地址管理</span>
        <span class="addr-close" @click="close">✕</span>
      </div>

      <!-- 地址列表 -->
      <div class="addr-body" v-if="!showForm">
        <div v-for="addr in list" :key="addr.id" class="addr-item">
          <div class="addr-info">
            <div class="addr-name">{{ addr.receiver_name }} <span class="addr-phone">{{ addr.receiver_phone }}</span>
              <span class="addr-tag" v-if="addr.is_default">默认</span>
            </div>
            <div class="addr-text">{{ addr.province }}{{ addr.city }}{{ addr.district }} {{ addr.detail_address }}</div>
          </div>
          <div class="addr-acts">
            <span @click="edit(addr)">编辑</span>
            <span @click="setDefault(addr)" v-if="!addr.is_default">设为默认</span>
            <span class="del" @click="del(addr)">删除</span>
          </div>
        </div>
        <div v-if="!list.length" class="addr-empty">暂无收货地址</div>
        <button class="addr-add" @click="add">+ 新增地址</button>
      </div>

      <!-- 地址表单 -->
      <div class="addr-body" v-else>
        <div class="form-row">
          <label>收货人 <em>*</em></label>
          <input v-model="form.receiver_name" placeholder="请输入收货人姓名" />
          <span class="err" v-if="errs.receiver_name">{{ errs.receiver_name }}</span>
        </div>
        <div class="form-row">
          <label>手机号 <em>*</em></label>
          <input v-model="form.receiver_phone" placeholder="11位手机号" maxlength="11" />
          <span class="err" v-if="errs.receiver_phone">{{ errs.receiver_phone }}</span>
        </div>
        <div class="form-row">
          <label>省份 <em>*</em></label>
          <input v-model="form.province" placeholder="省份" />
          <span class="err" v-if="errs.province">{{ errs.province }}</span>
        </div>
        <div class="form-row">
          <label>城市 <em>*</em></label>
          <input v-model="form.city" placeholder="城市" />
          <span class="err" v-if="errs.city">{{ errs.city }}</span>
        </div>
        <div class="form-row">
          <label>区/县</label>
          <input v-model="form.district" placeholder="区/县" />
        </div>
        <div class="form-row">
          <label>详细地址 <em>*</em></label>
          <input v-model="form.detail_address" placeholder="街道门牌号" />
          <span class="err" v-if="errs.detail_address">{{ errs.detail_address }}</span>
        </div>
        <div class="form-row">
          <label></label>
          <label class="switch"><input type="checkbox" v-model="form.is_default" /> 设为默认</label>
        </div>
        <div class="form-btns">
          <button class="btn-cancel" @click="showForm=false">取消</button>
          <button class="btn-save" :disabled="saving" @click="save">{{ saving?'保存中...':'保存' }}</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { getAddressList, createAddress, updateAddress, deleteAddress, setDefaultAddress } from '../../api/user'
import { extractList } from '../../utils/response'
import { ElMessage, ElMessageBox } from 'element-plus'

const props = defineProps({ visible: Boolean })
const emit = defineEmits(['update:visible'])

const list = ref([])
const showForm = ref(false)
const saving = ref(false)
const editId = ref(null)
const form = ref(initForm())
const errs = ref({})

function initForm() { return { receiver_name:'', receiver_phone:'', province:'', city:'', district:'', detail_address:'', is_default:false } }

watch(() => props.visible, v => { if (v) load() })

async function load() {
  try { list.value = extractList(await getAddressList()) } catch {}
}
function close() { emit('update:visible', false) }
function add() { editId.value = null; form.value = initForm(); errs.value = {}; showForm.value = true }
function edit(addr) { editId.value = addr.id; form.value = { ...addr }; errs.value = {}; showForm.value = true }

function validate() {
  const e = {}
  if (!form.value.receiver_name?.trim()) e.receiver_name = '请输入收货人'
  if (!form.value.receiver_phone?.trim()) e.receiver_phone = '请输入手机号'
  else if (!/^1[3-9]\d{9}$/.test(form.value.receiver_phone)) e.receiver_phone = '手机号格式不正确'
  if (!form.value.province?.trim()) e.province = '请输入省份'
  if (!form.value.city?.trim()) e.city = '请输入城市'
  if (!form.value.detail_address?.trim()) e.detail_address = '请输入详细地址'
  errs.value = e
  return !Object.keys(e).length
}

async function save() {
  if (!validate()) return
  saving.value = true
  try {
    if (editId.value) { await updateAddress(editId.value, form.value); ElMessage.success('修改成功') }
    else { await createAddress(form.value); ElMessage.success('添加成功') }
    showForm.value = false; load()
  } catch {} finally { saving.value = false }
}
async function del(addr) {
  await ElMessageBox.confirm('确定删除？','提示',{type:'warning'})
  try { await deleteAddress(addr.id); ElMessage.success('已删除'); load() } catch {}
}
async function setDefault(addr) {
  try { await setDefaultAddress(addr.id); ElMessage.success('已设为默认'); load() } catch {}
}
</script>

<style scoped>
.addr-mask { position: fixed; top:0;left:0;right:0;bottom:0; background: rgba(0,0,0,.45); display:flex; align-items:center; justify-content:center; z-index:2000; }
.addr-dialog { width:520px; max-height:80vh; background:#fff; border-radius:12px; overflow:hidden; display:flex; flex-direction:column; }
.addr-header { display:flex; justify-content:space-between; align-items:center; padding:16px 20px; border-bottom:1px solid #f0f0f0; font-size:16px; font-weight:bold; }
.addr-close { cursor:pointer; color:#999; font-size:18px; }
.addr-close:hover { color:#333; }
.addr-body { padding:16px 20px; overflow-y:auto; max-height:65vh; }
.addr-item { padding:12px; border:1px solid #f0f0f0; border-radius:8px; margin-bottom:10px; }
.addr-name { font-weight:bold; font-size:14px; margin-bottom:4px; }
.addr-phone { font-weight:normal; color:#666; margin-left:8px; }
.addr-tag { background:#ff4400; color:#fff; font-size:11px; padding:1px 6px; border-radius:3px; margin-left:8px; }
.addr-text { font-size:13px; color:#666; margin-bottom:8px; }
.addr-acts { display:flex; gap:12px; }
.addr-acts span { font-size:12px; color:#1890ff; cursor:pointer; }
.addr-acts span:hover { text-decoration:underline; }
.addr-acts .del { color:#f56c6c; }
.addr-empty { text-align:center; padding:24px; color:#ccc; }
.addr-add { width:100%; padding:10px; background:#fff5f0; color:#ff4400; border:1px dashed #ffcc99; border-radius:6px; cursor:pointer; font-size:14px; margin-top:8px; }
.addr-add:hover { background:#ffe8d6; }

.form-row { display:flex; align-items:flex-start; margin-bottom:12px; position:relative; }
.form-row label { width:80px; font-size:13px; color:#666; line-height:36px; flex-shrink:0; }
.form-row label em { color:#ff4400; font-style:normal; }
.form-row input { flex:1; height:36px; border:1px solid #e8e8e8; border-radius:6px; padding:0 10px; font-size:13px; }
.form-row input:focus { border-color:#ff4400; outline:none; }
.switch { display:flex; align-items:center; gap:6px; cursor:pointer; width:auto; line-height:36px; }
.switch input { accent-color:#ff4400; }
.err { position:absolute; right:0; top:38px; font-size:11px; color:#f56c6c; }
.form-btns { display:flex; justify-content:flex-end; gap:10px; margin-top:16px; padding-top:12px; border-top:1px solid #f0f0f0; }
.form-btns button { padding:8px 24px; border-radius:6px; cursor:pointer; font-size:14px; }
.btn-cancel { background:#f5f5f5; border:1px solid #ddd; color:#666; }
.btn-save { background:#ff4400; border:none; color:#fff; }
.btn-save:disabled { opacity:.6; }
</style>
