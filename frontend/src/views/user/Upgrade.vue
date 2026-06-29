<template>
  <div class="upgrade-page">
    <div class="upgrade-card" v-if="!userStore.isSellerUser">
      <div class="icon">🏪</div>
      <h2>升级为商家</h2>
      <p>升级后可发布商品、管理店铺，同时保留买家功能</p>
      <div class="form">
        <div class="form-row"><label>店铺名称 <em>*</em></label><input v-model="form.shop_name" placeholder="请输入店铺名称" /></div>
        <div class="form-row"><label>店铺简介</label><textarea v-model="form.shop_description" rows="3" placeholder="选填"></textarea></div>
        <div class="form-row"><label>联系电话</label><input v-model="form.contact_phone" placeholder="选填" maxlength="11" /></div>
        <button class="btn-submit" :disabled="loading" @click="handleUpgrade">{{ loading?'升级中...':'确认升级' }}</button>
      </div>
    </div>
    <div class="upgrade-card done" v-else>
      <div class="icon">✅</div>
      <h2>您已是商家</h2>
      <p>可前往商家后台管理商品</p>
      <button class="btn-submit" @click="$router.push('/seller')">进入商家后台</button>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../../store/user'
import { upgradeToSeller } from '../../api/user'
import { ElMessage } from 'element-plus'

const router = useRouter()
const userStore = useUserStore()
const loading = ref(false)
const form = reactive({ shop_name:'', shop_description:'', contact_phone:'' })

async function handleUpgrade() {
  if (!form.shop_name) { ElMessage.warning('请输入店铺名称'); return }
  loading.value = true
  try { await upgradeToSeller(form); await userStore.fetchUserInfo(); ElMessage.success('升级成功'); router.push('/seller') } catch {} finally { loading.value = false }
}
</script>

<style scoped>
.upgrade-page { display:flex; justify-content:center; padding:40px 16px; }
.upgrade-card { width:480px; background:#fff; border-radius:12px; padding:40px; text-align:center; }
.icon { font-size:56px; margin-bottom:16px; }
.upgrade-card h2 { margin-bottom:8px; }
.upgrade-card p { color:#999; font-size:14px; margin-bottom:28px; }
.form { text-align:left; }
.form-row { display:flex; align-items:flex-start; margin-bottom:14px; }
.form-row label { width:80px; font-size:13px; color:#666; line-height:36px; flex-shrink:0; }
.form-row label em { color:#ff4400; font-style:normal; }
.form-row input,.form-row textarea { flex:1; height:36px; border:1px solid #e8e8e8; border-radius:4px; padding:0 10px; font-size:13px; }
.form-row textarea { height:auto; padding:8px 10px; resize:vertical; }
.form-row input:focus,.form-row textarea:focus { border-color:#ff4400; outline:none; }
.btn-submit { width:100%; height:44px; background:#ff4400; color:#fff; border:none; border-radius:22px; font-size:15px; font-weight:bold; cursor:pointer; margin-top:8px; }
.btn-submit:disabled { opacity:.6; }
.done p { color:#999; margin-bottom:24px; }
</style>
