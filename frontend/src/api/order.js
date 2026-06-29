/**
 * 订单相关接口
 * 对应后端: /api/v1/orders/
 */
import request from './request'

/**
 * 创建订单
 * POST /api/v1/orders/
 * @param {Object} data - { receiver_name, receiver_phone, receiver_address, items: [{sku_id, quantity, goods_name, goods_image}], remark }
 */
export function createOrder(data) {
  return request.post('/api/v1/orders/', data)
}

/**
 * 订单列表
 * GET /api/v1/orders/
 * @param {Object} params - { status } 可选
 */
export function getOrderList(params) {
  return request.get('/api/v1/orders/', { params })
}

/**
 * 订单详情
 * GET /api/v1/orders/<order_no>/
 * @param {String} orderNo
 */
export function getOrderDetail(orderNo) {
  return request.get(`/api/v1/orders/${orderNo}/`)
}

/**
 * 支付订单（模拟）
 * POST /api/v1/orders/<order_no>/pay/
 * @param {String} orderNo
 * @param {Object} data - { pay_method: 'wechat'|'alipay'|'card' }
 */
export function payOrder(orderNo, data) {
  return request.post(`/api/v1/orders/${orderNo}/pay/`, data)
}

/**
 * 取消订单
 * POST /api/v1/orders/<order_no>/cancel/
 * @param {String} orderNo
 */
export function cancelOrder(orderNo) {
  return request.post(`/api/v1/orders/${orderNo}/cancel/`)
}

/**
 * 确认收货
 * POST /api/v1/orders/<order_no>/complete/
 * @param {String} orderNo
 */
export function completeOrder(orderNo) {
  return request.post(`/api/v1/orders/${orderNo}/complete/`)
}

/**
 * 申请退款
 * POST /api/v1/orders/<order_no>/refund/
 * @param {String} orderNo
 */
export function refundOrder(orderNo) {
  return request.post(`/api/v1/orders/${orderNo}/refund/`)
}

/**
 * 商家发货
 * POST /api/v1/orders/<order_no>/ship/
 * @param {String} orderNo
 * @param {Object} data - { express_no } 可选
 */
export function shipOrder(orderNo, data) {
  return request.post(`/api/v1/orders/${orderNo}/ship/`, data || {})
}
