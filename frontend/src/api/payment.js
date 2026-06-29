/**
 * 支付接口
 * 对应后端: /api/v1/payment/
 */
import request from './request'

/** 发起支付 */
export function createPayment(data) {
  return request.post('/api/v1/payment/create/', data)
}

/** 模拟支付（开发环境） */
export function mockPay(pay_no) {
  return request.post('/api/v1/payment/mock-pay/', { pay_no })
}

/** 查询支付状态 */
export function getPaymentStatus(pay_no) {
  return request.get(`/api/v1/payment/${pay_no}/status/`)
}
