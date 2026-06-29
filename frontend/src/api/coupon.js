/**
 * 优惠券接口
 * 对应后端: /api/v1/coupons/
 */
import request from './request'

/** 可领取的优惠券列表 */
export function getCouponList() {
  return request.get('/api/v1/coupons/')
}

/** 领取优惠券 */
export function claimCoupon(id) {
  return request.post(`/api/v1/coupons/${id}/claim/`)
}

/** 我的优惠券 */
export function getMyCoupons(params) {
  return request.get('/api/v1/coupons/mine/', { params })
}
