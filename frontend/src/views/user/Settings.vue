<template>
  <div class="settings-page">
    <div class="tabs">
      <span :class="{active:tab==='info'}" @click="tab='info'">个人信息</span>
      <span :class="{active:tab==='pwd'}" @click="tab='pwd'">修改密码</span>
    </div>
    <div class="tab-body" v-show="tab==='info'">
      <div class="form-sec">
        <div class="form-row"><label>头像</label><div class="avatar-area"><img :src="info.avatar||'https://via.placeholder.com/64'" class="avatar-img" /><label class="upload">更换<input type="file" accept="image/*" @change="onAvatar" hidden /></label></div></div>
        <div class="form-row"><label>昵称</label><input v-model="info.nickname" /></div>
        <div class="form-row"><label>性别</label><div class="radio-grp"><label><input type="radio" v-model="info.gender" :value="0" /> 未知</label><label><input type="radio" v-model="info.gender" :value="1" /> 男</label><label><input type="radio" v-model="info.gender" :value="2" /> 女</label></div></div>
        <div class="form-row"><label>生日</label><input v-model="info.birthday" type="date" /></div>
        <div class="form-row"><label>邮箱</label><input v-model="info.email" /></div>
        <div class="form-row"><label>手机号</label><input v-model="info.phone" maxlength="11" /></div>
        <div class="form-row"><label>简介</label><textarea v-model="info.bio" rows="3"></textarea></div>
        <div class="form-row"><label></label><button class="btn-save" :disabled="infoSaving" @click="saveInfo">{{ infoSaving?'保存中...':'保存' }}</button></div>
      </div>
    </div>
    <div class="tab-body" v-show="tab==='pwd'">
      <div class="form-sec">
        <div class="form-row"><label>旧密码</label><input v-model="pwd.old_password" type="password" placeholder="当前密码" /></div>
        <div class="form-row"><label>新密码</label><input v-model="pwd.new_password" type="password" placeholder="至少8位" /></div>
        <div class="form-row"><label>确认密码</label><input v-model="pwd.new_password_confirm" type="password" placeholder="再次输入" /></div>
        <div class="form-row"><label></label><button class="btn-save" :disabled="pwdSaving" @click="savePwd">{{ pwdSaving?'修改中...':'修改密码' }}</button></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useUserStore } from '../../store/user'
import { updateUserInfo, changePassword, uploadAvatar } from '../../api/user'
import { ElMessage } from 'element-plus'

const userStore = useUserStore()
const tab = ref('info')
const infoSaving = ref(false)
const pwdSaving = ref(false)
const info = reactive({ nickname:'', gender:0, birthday:'', email:'', phone:'', bio:'', avatar:'' })
const pwd = reactive({ old_password:'', new_password:'', new_password_confirm:'' })

onMounted(() => {
  const u = userStore.userInfo
  if (u) Object.assign(info, { nickname:u.nickname, gender:u.gender, birthday:u.birthday, email:u.email, phone:u.phone, bio:u.bio, avatar:u.avatar })
})
async function onAvatar(e) {
  const file = e.target.files[0]; if (!file) return
  const fd = new FormData(); fd.append('avatar', file)
  try { const res = await uploadAvatar(fd); info.avatar = (res.data||res).avatar; await userStore.fetchUserInfo(); ElMessage.success('头像已更新') } catch {}
}
async function saveInfo() {
  infoSaving.value = true
  try { await updateUserInfo(info); await userStore.fetchUserInfo(); ElMessage.success('保存成功') } catch {} finally { infoSaving.value = false }
}
async function savePwd() {
  if (!pwd.old_password || !pwd.new_password) { ElMessage.warning('请填写完整'); return }
  if (pwd.new_password.length < 8) { ElMessage.warning('至少8位'); return }
  if (pwd.new_password !== pwd.new_password_confirm) { ElMessage.warning('不一致'); return }
  pwdSaving.value = true
  try { await changePassword(pwd); ElMessage.success('修改成功'); Object.assign(pwd, { old_password:'', new_password:'', new_password_confirm:'' }) } catch {} finally { pwdSaving.value = false }
}
</script>

<style scoped>
.tabs { display:flex; background:#fff; border-radius:8px 8px 0 0; border-bottom:1px solid #f0f0f0; }
.tabs span { padding:14px 28px; cursor:pointer; color:#666; font-size:15px; }
.tabs span.active { color:#ff4400; border-bottom:2px solid #ff4400; font-weight:bold; }
.tab-body { background:#fff; border-radius:0 0 8px 8px; padding:24px; }
.form-sec { max-width:500px; }
.form-row { display:flex; align-items:flex-start; margin-bottom:16px; }
.form-row label { width:70px; font-size:13px; color:#666; line-height:36px; flex-shrink:0; }
.form-row input,.form-row textarea { flex:1; height:36px; border:1px solid #e8e8e8; border-radius:4px; padding:0 10px; font-size:13px; }
.form-row textarea { height:auto; padding:8px 10px; resize:vertical; }
.form-row input:focus,.form-row textarea:focus { border-color:#ff4400; outline:none; }
.radio-grp { display:flex; gap:16px; line-height:36px; font-size:13px; }
.radio-grp input { accent-color:#ff4400; }
.avatar-area { display:flex; align-items:center; gap:12px; }
.avatar-img { width:64px; height:64px; border-radius:50%; object-fit:cover; }
.upload { font-size:13px; color:#ff4400; cursor:pointer; }
.btn-save { padding:10px 32px; background:#ff4400; color:#fff; border:none; border-radius:4px; cursor:pointer; }
.btn-save:disabled { opacity:.6; }
</style>
