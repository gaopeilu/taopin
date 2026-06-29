/**
 * 用户相关接口
 * 对应后端: /api/v1/users/
 */
import request from './request'

/**
 * 用户注册
 * POST /api/v1/users/register/
 * @param {Object} data - { username, email, phone, password, password_confirm, role, shop_name }
 * @returns {Object} { user: {}, tokens: { access, refresh } }
 * 无需认证
 */
export function register(data) {
  return request.post('/api/v1/users/register/', data)
}

/**
 * 用户登录（支持用户名/邮箱/手机号）
 * POST /api/v1/users/login/
 * @param {Object} data - { username, password }
 * @returns {Object} { user: {}, tokens: { access, refresh } }
 * 无需认证
 */
export function login(data) {
  return request.post('/api/v1/users/login/', data)
}

/**
 * 刷新Token
 * POST /api/v1/users/token/refresh/
 * @param {Object} data - { refresh: "jwt_refresh_token" }
 * 无需认证
 */
export function refreshToken(data) {
  return request.post('/api/v1/users/token/refresh/', data)
}

/**
 * 获取当前用户信息
 * GET /api/v1/users/me/
 * @returns {Object} { id, username, email, phone, avatar, nickname, gender, birthday, bio, role, is_seller, shop_name, date_joined }
 */
export function getUserInfo() {
  return request.get('/api/v1/users/me/')
}

/**
 * 修改用户信息
 * PUT /api/v1/users/me/
 * @param {Object} data - { nickname, gender, birthday, bio, email, phone }
 */
export function updateUserInfo(data) {
  return request.put('/api/v1/users/me/', data)
}

/**
 * 修改密码
 * PUT /api/v1/users/me/password/
 * @param {Object} data - { old_password, new_password, new_password_confirm }
 */
export function changePassword(data) {
  return request.put('/api/v1/users/me/password/', data)
}

/**
 * 上传头像
 * POST /api/v1/users/me/avatar/
 * Content-Type: multipart/form-data
 * @param {FormData} formData - { avatar: File }
 */
export function uploadAvatar(formData) {
  return request.post('/api/v1/users/me/avatar/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

/**
 * 收货地址列表
 * GET /api/v1/users/address/
 * @returns {Array} [AddressSerializer...]
 */
export function getAddressList() {
  return request.get('/api/v1/users/address/')
}

/**
 * 创建收货地址
 * POST /api/v1/users/address/
 * @param {Object} data - { receiver_name, receiver_phone, province, city, district, detail_address, is_default }
 */
export function createAddress(data) {
  return request.post('/api/v1/users/address/', data)
}

/**
 * 修改收货地址
 * PUT /api/v1/users/address/<id>/
 * @param {Number} id
 * @param {Object} data
 */
export function updateAddress(id, data) {
  return request.put(`/api/v1/users/address/${id}/`, data)
}

/**
 * 删除收货地址
 * DELETE /api/v1/users/address/<id>/
 * @param {Number} id
 */
export function deleteAddress(id) {
  return request.delete(`/api/v1/users/address/${id}/`)
}

/**
 * 设置默认地址
 * PUT /api/v1/users/address/<id>/default/
 * @param {Number} id
 */
export function setDefaultAddress(id) {
  return request.put(`/api/v1/users/address/${id}/default/`)
}

/**
 * 获取用户偏好设置
 * GET /api/v1/users/preferences/
 * @returns {Object} { order_notify, promotion_notify, public_purchase, public_review }
 */
export function getPreferences() {
  return request.get('/api/v1/users/preferences/')
}

/**
 * 修改用户偏好设置
 * PUT /api/v1/users/preferences/
 * @param {Object} data
 */
export function updatePreferences(data) {
  return request.put('/api/v1/users/preferences/', data)
}

/**
 * 升级为商家
 * POST /api/v1/users/upgrade/
 * @param {Object} data - { shop_name, shop_description, contact_phone }
 * @returns {Object} { role, shop_name }
 */
export function upgradeToSeller(data) {
  return request.post('/api/v1/users/upgrade/', data)
}

/**
 * 发送验证码
 * POST /api/v1/users/send_code/
 * @param {Object} data - { target: '手机号或邮箱', code_type: 'register|login|bind_phone|bind_email' }
 * @returns {Object} { code: 200, message: '验证码已发送' }
 */
export function sendCode(data) {
  return request.post('/api/v1/users/send_code/', data)
}

/**
 * 绑定手机号
 * POST /api/v1/users/me/phone/bind/
 * @param {Object} data - { phone, code }
 * @returns {Object} { code: 200, message: '绑定成功' }
 */
export function bindPhone(data) {
  return request.post('/api/v1/users/me/phone/bind/', data)
}
