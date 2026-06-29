/**
 * 商家后台相关接口
 * 对应后端: /api/v1/goods/ (seller权限) + /api/v1/users/ (seller权限)
 */
import request from './request'

/* ========== 商品SPU管理（商家） ========== */

/**
 * 创建商品SPU
 * POST /api/v1/goods/spus/
 * @param {Object} data - { name, category, brand, subtitle, description, main_image, is_on_sale }
 * name: min 2 chars
 */
export function createGoods(data) {
  return request.post('/api/v1/goods/spus/', data)
}

/**
 * 修改商品SPU
 * PUT /api/v1/goods/spus/<id>/
 * @param {Number} id
 * @param {Object} data - 同创建
 */
export function updateGoods(id, data) {
  return request.put(`/api/v1/goods/spus/${id}/`, data)
}

/**
 * 删除商品（软删除，设置is_deleted=True）
 * DELETE /api/v1/goods/spus/<id>/
 * @param {Number} id
 */
export function deleteGoods(id) {
  return request.delete(`/api/v1/goods/spus/${id}/`)
}

/**
 * 上下架切换
 * PUT /api/v1/goods/spus/<id>/toggle_sale/
 * @param {Number} id
 * 返回: { is_on_sale: bool }
 */
export function toggleGoodsSale(id) {
  return request.put(`/api/v1/goods/spus/${id}/toggle_sale/`)
}

/**
 * 上传商品图片
 * POST /api/v1/goods/spus/<id>/upload_image/
 * Content-Type: multipart/form-data
 * @param {Number} spuId
 * @param {FormData} formData - { image: File, is_main: boolean }
 */
export function uploadGoodsImage(spuId, formData) {
  return request.post(`/api/v1/goods/spus/${spuId}/upload_image/`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

/**
 * 删除商品图片
 * DELETE /api/v1/goods/images/<id>/
 * @param {Number} imageId
 */
export function deleteGoodsImage(imageId) {
  return request.delete(`/api/v1/goods/images/${imageId}/`)
}

/**
 * 设置主图
 * PUT /api/v1/goods/images/<id>/set_main/
 * @param {Number} imageId
 */
export function setMainImage(imageId) {
  return request.put(`/api/v1/goods/images/${imageId}/set_main/`)
}

/* ========== SKU管理（商家） ========== */

/**
 * 创建SKU
 * POST /api/v1/goods/skus/
 * @param {Object} data - { spu, name, price, original_price, stock, specs, image, is_default, is_active, barcode }
 */
export function createSku(data) {
  return request.post('/api/v1/goods/skus/', data)
}

/**
 * 修改SKU
 * PUT /api/v1/goods/skus/<id>/
 * @param {Number} id
 * @param {Object} data
 */
export function updateSku(id, data) {
  return request.put(`/api/v1/goods/skus/${id}/`, data)
}

/**
 * 删除SKU（硬删除）
 * DELETE /api/v1/goods/skus/<id>/
 * @param {Number} id
 */
export function deleteSku(id) {
  return request.delete(`/api/v1/goods/skus/${id}/`)
}

/**
 * 扣减库存
 * POST /api/v1/goods/skus/<id>/deduct_stock/
 * @param {Number} id
 * @param {Object} data - { quantity }
 */
export function deductStock(id, data) {
  return request.post(`/api/v1/goods/skus/${id}/deduct_stock/`, data)
}

/**
 * 恢复库存
 * POST /api/v1/goods/skus/<id>/restore_stock/
 * @param {Number} id
 * @param {Object} data - { quantity }
 */
export function restoreStock(id, data) {
  return request.post(`/api/v1/goods/skus/${id}/restore_stock/`, data)
}

/* ========== 店铺设置（商家） ========== */

/**
 * 获取店铺设置
 * GET /api/v1/users/shop-settings/
 * 需要seller权限，非商家返回403
 * 返回: { shop_name, shop_description, contact_phone }
 */
export function getShopSettings() {
  return request.get('/api/v1/users/shop-settings/')
}

/**
 * 修改店铺设置
 * PUT /api/v1/users/shop-settings/
 * @param {Object} data - { shop_name, shop_description }
 */
export function updateShopSettings(data) {
  return request.put('/api/v1/users/shop-settings/', data)
}
