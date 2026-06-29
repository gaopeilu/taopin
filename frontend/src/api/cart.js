/**
 * 购物车接口
 * 对应后端: /api/v1/cart/
 */
import request from './request'

/** 购物车列表 */
export function getCartList() {
  return request.get('/api/v1/cart/')
}

/** 添加到购物车 */
export function addToCart(data) {
  return request.post('/api/v1/cart/add/', data)
}

/** 更新购物车（数量/选中状态） */
export function updateCart(id, data) {
  return request.put(`/api/v1/cart/${id}/`, data)
}

/** 删除购物车项 */
export function deleteCartItem(id) {
  return request.delete(`/api/v1/cart/${id}/delete/`)
}

/** 清空购物车 */
export function clearCart() {
  return request.delete('/api/v1/cart/clear/')
}

/** 全选/取消全选 */
export function selectAllCart(is_selected) {
  return request.post('/api/v1/cart/select-all/', { is_selected })
}
